#!/usr/bin/env python
# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause
"""Export a trained kame32 skrl PPO policy (no-IMU variant) for on-device inference.

This reads a saved skrl checkpoint (`checkpoint.pt` next to this script by default) and:

  1. Extracts the policy MLP weights and the observation normalizer (RunningStandardScaler:
     running_mean, running_variance) from the checkpoint.
  2. Rebuilds the exact inference the robot needs -- normalize, then a 4-layer ELU MLP -- as a
     plain numpy function, and CHECKS it against skrl's own RunningStandardScaler + a torch MLP
     so we are certain the maths (including the epsilon and the +-5 clip) match the trained policy.
  3. Writes `policy_weights.h`, a C header with every weight/bias plus the precomputed
     normalization (mean and inv_std = 1/(sqrt(var)+eps)), ready to #include in the ESP32 firmware.
  4. Embeds a self-test case (one example observation of 55 and the expected 8 outputs) into that
     header, so the firmware can verify its own inference matches this PC at boot.
  5. Optionally exports `policy.onnx` (normalization inside the graph) for inspection on a PC.

The heavy sim-to-real detail (order of the 55-value observation, action->servo mapping) lives in
the firmware; this script only concerns the network itself. See the docs in the kame32-rl project.

Usage:
    unset VIRTUAL_ENV CONDA_PREFIX
    /home/angellm/IsaacLab/isaaclab.sh -p export/export_policy.py \
        [--checkpoint export/checkpoint.pt] [--out ../../../Desktop/kame32-rl/lib/Policy/policy_weights.h] [--onnx]
"""

import argparse
import os

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CKPT = os.path.join(HERE, "checkpoint.pt")
DEFAULT_OUT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "Desktop", "kame32-rl", "lib", "Policy", "policy_weights.h"))

OBS_DIM = 55
ACT_DIM = 8
HIDDEN = 128
EPS = 1e-8          # skrl RunningStandardScaler epsilon
CLIP = 5.0          # skrl RunningStandardScaler clip_threshold


def elu(x):
    return np.where(x > 0, x, np.exp(np.minimum(x, 0.0)) - 1.0)


def load_policy(ckpt_path):
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    p = ckpt["policy"]
    sp = ckpt["state_preprocessor"]

    def npy(key):
        return p[key].detach().cpu().numpy().astype(np.float64)

    weights = {
        "W0": npy("net_container.0.weight"), "b0": npy("net_container.0.bias"),
        "W2": npy("net_container.2.weight"), "b2": npy("net_container.2.bias"),
        "W4": npy("net_container.4.weight"), "b4": npy("net_container.4.bias"),
        "Wout": npy("policy_layer.weight"), "bout": npy("policy_layer.bias"),
    }
    mean = sp["running_mean"].detach().cpu().numpy().astype(np.float64)
    var = sp["running_variance"].detach().cpu().numpy().astype(np.float64)
    inv_std = 1.0 / (np.sqrt(var) + EPS)
    return weights, mean, var, inv_std


def infer_numpy(obs, w, mean, inv_std):
    """The exact reference we port to C: normalize (+clip), then 4-layer ELU MLP."""
    x = np.clip((obs - mean) * inv_std, -CLIP, CLIP)
    x = elu(w["W0"] @ x + w["b0"])
    x = elu(w["W2"] @ x + w["b2"])
    x = elu(w["W4"] @ x + w["b4"])
    return w["Wout"] @ x + w["bout"]


def cross_check(w, mean, var, inv_std, n=32):
    """Confirm the numpy reference matches skrl's own normalizer + a torch MLP."""
    try:
        from skrl.resources.preprocessors.torch import RunningStandardScaler
    except Exception as e:
        print(f"[warn] skrl not importable ({e}); skipping cross-check against skrl normalizer.")
        return None
    scaler = RunningStandardScaler(size=OBS_DIM, device="cpu")
    scaler.running_mean = torch.tensor(mean, dtype=torch.float64)
    scaler.running_variance = torch.tensor(var, dtype=torch.float64)

    def torch_lin(x, W, b):
        return torch.nn.functional.linear(x, torch.tensor(W, dtype=torch.float32), torch.tensor(b, dtype=torch.float32))

    rng = np.random.default_rng(0)
    max_err = 0.0
    for _ in range(n):
        obs = rng.normal(mean, np.sqrt(var) + 0.05).astype(np.float64)
        # skrl path
        xt = scaler(torch.tensor(obs, dtype=torch.float32).unsqueeze(0)).squeeze(0)
        xt = torch.nn.functional.elu(torch_lin(xt, w["W0"], w["b0"]))
        xt = torch.nn.functional.elu(torch_lin(xt, w["W2"], w["b2"]))
        xt = torch.nn.functional.elu(torch_lin(xt, w["W4"], w["b4"]))
        ref = torch_lin(xt, w["Wout"], w["bout"]).detach().numpy()
        # numpy path
        mine = infer_numpy(obs, w, mean, inv_std)
        max_err = max(max_err, float(np.max(np.abs(ref - mine))))
    return max_err


def _fmt(v):
    # always emit a valid C float literal (an integer like "0" would make "0f" invalid)
    s = f"{float(v):.8g}"
    if not any(c in s for c in ".eEni"):  # no dot/exponent (and not nan/inf)
        s += ".0"
    return s + "f"


def c_array(name, arr, ctype="float"):
    flat = np.asarray(arr, dtype=np.float64).flatten()
    body = ", ".join(_fmt(v) for v in flat)
    return f"static const {ctype} {name}[{flat.size}] = {{{body}}};\n"


def write_header(path, w, mean, inv_std, test_obs, test_act):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = []
    lines.append("// Auto-generated by kame32/export/export_policy.py -- do not edit by hand.\n")
    lines.append("// Trained kame32 walking policy (no-IMU variant). MLP 55->128->128->128->8, ELU.\n")
    lines.append("#ifndef POLICY_WEIGHTS_H\n#define POLICY_WEIGHTS_H\n\n")
    lines.append(f"#define POLICY_OBS_DIM {OBS_DIM}\n#define POLICY_ACT_DIM {ACT_DIM}\n#define POLICY_HIDDEN {HIDDEN}\n")
    lines.append(f"#define POLICY_CLIP {CLIP}f\n\n")
    # normalization (mean and inverse std, so the device does no sqrt and matches skrl exactly)
    lines.append(c_array("POLICY_OBS_MEAN", mean))
    lines.append(c_array("POLICY_OBS_INV_STD", inv_std))
    lines.append("\n")
    # weights (row-major: W[out][in])
    lines.append(c_array("POLICY_W0", w["W0"]));   lines.append(c_array("POLICY_B0", w["b0"]))
    lines.append(c_array("POLICY_W2", w["W2"]));   lines.append(c_array("POLICY_B2", w["b2"]))
    lines.append(c_array("POLICY_W4", w["W4"]));   lines.append(c_array("POLICY_B4", w["b4"]))
    lines.append(c_array("POLICY_WOUT", w["Wout"])); lines.append(c_array("POLICY_BOUT", w["bout"]))
    lines.append("\n// Self-test: feeding POLICY_TEST_OBS must yield POLICY_TEST_ACT (within ~1e-3).\n")
    lines.append(c_array("POLICY_TEST_OBS", test_obs))
    lines.append(c_array("POLICY_TEST_ACT", test_act))
    lines.append("\n#endif  // POLICY_WEIGHTS_H\n")
    with open(path, "w") as f:
        f.writelines(lines)


def export_onnx(path, w, mean, inv_std):
    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.mean = torch.tensor(mean, dtype=torch.float32)
            self.inv_std = torch.tensor(inv_std, dtype=torch.float32)
            self.l0 = torch.nn.Linear(OBS_DIM, HIDDEN); self.l2 = torch.nn.Linear(HIDDEN, HIDDEN)
            self.l4 = torch.nn.Linear(HIDDEN, HIDDEN);   self.lo = torch.nn.Linear(HIDDEN, ACT_DIM)
            for lyr, key in [(self.l0, "0"), (self.l2, "2"), (self.l4, "4")]:
                lyr.weight.data = torch.tensor(w[f"W{key}"], dtype=torch.float32)
                lyr.bias.data = torch.tensor(w[f"b{key}"], dtype=torch.float32)
            self.lo.weight.data = torch.tensor(w["Wout"], dtype=torch.float32)
            self.lo.bias.data = torch.tensor(w["bout"], dtype=torch.float32)

        def forward(self, obs):
            x = torch.clamp((obs - self.mean) * self.inv_std, -CLIP, CLIP)
            x = torch.nn.functional.elu(self.l0(x)); x = torch.nn.functional.elu(self.l2(x))
            x = torch.nn.functional.elu(self.l4(x)); return self.lo(x)

    net = Net().eval()
    dummy = torch.zeros(1, OBS_DIM)
    torch.onnx.export(net, dummy, path, input_names=["obs"], output_names=["action"], opset_version=18)
    print(f"[ok] wrote {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=DEFAULT_CKPT)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--onnx", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.checkpoint):
        raise SystemExit(f"Checkpoint not found: {args.checkpoint}\nCopy your trained best_agent.pt there first.")

    w, mean, var, inv_std = load_policy(args.checkpoint)
    print(f"[ok] loaded policy: obs={OBS_DIM} act={ACT_DIM} hidden={HIDDEN}")

    err = cross_check(w, mean, var, inv_std)
    if err is not None:
        status = "OK" if err < 1e-4 else "MISMATCH!"
        print(f"[{status}] numpy vs skrl-normalizer max abs diff = {err:.2e}")

    # deterministic test case
    rng = np.random.default_rng(1234)
    test_obs = rng.normal(mean, np.sqrt(var) + 0.05).astype(np.float64)
    test_act = infer_numpy(test_obs, w, mean, inv_std)
    print("[info] test action:", np.array2string(test_act, precision=4))

    write_header(args.out, w, mean, inv_std, test_obs, test_act)
    print(f"[ok] wrote {args.out}")

    if args.onnx:
        export_onnx(os.path.join(HERE, "policy.onnx"), w, mean, inv_std)


if __name__ == "__main__":
    main()
