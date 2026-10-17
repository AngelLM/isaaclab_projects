# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Run a trained kame32 policy and report the angle range each joint actually uses.

This answers "how wide are the movements?" per joint (especially the Body_B* yaw
joints). It loads a skrl checkpoint, rolls out the deterministic policy, and prints
the min / max / peak-to-peak amplitude (in degrees) and std for every joint.

Example:
  unset VIRTUAL_ENV CONDA_PREFIX
  /home/angellm/IsaacLab/isaaclab.sh -p scripts/inspect_motion.py \
      --task Template-Kame32-Play-v0 --num_envs 64 --steps 400 \
      --checkpoint logs/skrl/kame32_walk/<run>/checkpoints/best_agent.pt
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Report per-joint angle range of a trained kame32 policy.")
parser.add_argument("--task", type=str, default="Template-Kame32-Play-v0")
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--steps", type=int, default=400, help="Number of control steps to roll out.")
parser.add_argument("--checkpoint", type=str, default=None, help="Path to .pt checkpoint (default: latest).")
parser.add_argument("--ml_framework", type=str, default="torch", choices=["torch", "jax", "jax-numpy"])
parser.add_argument("--algorithm", type=str, default="PPO")
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import os
import torch

import gymnasium as gym
import skrl
from skrl.utils.runner.torch import Runner

from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab_rl.skrl import SkrlVecEnvWrapper
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

import kame32.tasks  # noqa: F401

agent_cfg_entry_point = "skrl_cfg_entry_point"


@hydra_task_config(args_cli.task, agent_cfg_entry_point)
def main(env_cfg: ManagerBasedRLEnvCfg, experiment_cfg: dict):
    env_cfg.scene.num_envs = args_cli.num_envs
    if args_cli.device is not None:
        env_cfg.sim.device = args_cli.device

    log_root_path = os.path.abspath(os.path.join("logs", "skrl", experiment_cfg["agent"]["experiment"]["directory"]))
    if args_cli.checkpoint:
        resume_path = os.path.abspath(args_cli.checkpoint)
    else:
        resume_path = get_checkpoint_path(
            log_root_path, run_dir=f".*_{args_cli.algorithm.lower()}_{args_cli.ml_framework}", other_dirs=["checkpoints"]
        )
    print(f"[INFO] Loading checkpoint: {resume_path}")

    env = gym.make(args_cli.task, cfg=env_cfg)
    me = env.unwrapped
    robot = me.scene["robot"]
    joint_names = list(robot.joint_names)

    env = SkrlVecEnvWrapper(env, ml_framework=args_cli.ml_framework)
    experiment_cfg["trainer"]["close_environment_at_exit"] = False
    experiment_cfg["agent"]["experiment"]["write_interval"] = 0
    experiment_cfg["agent"]["experiment"]["checkpoint_interval"] = 0
    runner = Runner(env, experiment_cfg)
    runner.agent.load(resume_path)
    runner.agent.set_running_mode("eval")

    n_j = len(joint_names)
    jmin = torch.full((n_j,), float("inf"), device=me.device)
    jmax = torch.full((n_j,), float("-inf"), device=me.device)
    # also track per-env per-joint range to get a typical (not just extreme) amplitude
    env_min = torch.full((me.num_envs, n_j), float("inf"), device=me.device)
    env_max = torch.full((me.num_envs, n_j), float("-inf"), device=me.device)
    sumsq = torch.zeros(n_j, device=me.device)
    summ = torch.zeros(n_j, device=me.device)
    count = 0

    obs, _ = env.reset()
    for _ in range(args_cli.steps):
        with torch.inference_mode():
            outputs = runner.agent.act(obs, timestep=0, timesteps=0)
            actions = outputs[-1].get("mean_actions", outputs[0])
            obs, _, _, _, _ = env.step(actions)
        jp = robot.data.joint_pos  # [num_envs, n_j]
        jmin = torch.minimum(jmin, jp.min(dim=0)[0])
        jmax = torch.maximum(jmax, jp.max(dim=0)[0])
        env_min = torch.minimum(env_min, jp)
        env_max = torch.maximum(env_max, jp)
        summ += jp.sum(dim=0)
        sumsq += (jp**2).sum(dim=0)
        count += me.num_envs

    rad2deg = 180.0 / 3.14159265
    mean = summ / count
    std = torch.sqrt(torch.clamp(sumsq / count - mean**2, min=0.0))
    typ_range = (env_max - env_min).mean(dim=0)  # mean per-env peak-to-peak

    print("\n================ PER-JOINT ANGLE RANGE (degrees) ================")
    print(f"{'joint':14s} {'min':>8s} {'max':>8s} {'glob_pp':>9s} {'env_pp':>8s} {'std':>7s}")
    for i, name in enumerate(joint_names):
        print(
            f"{name:14s} {jmin[i].item()*rad2deg:8.1f} {jmax[i].item()*rad2deg:8.1f} "
            f"{(jmax[i]-jmin[i]).item()*rad2deg:9.1f} {typ_range[i].item()*rad2deg:8.1f} {std[i].item()*rad2deg:7.1f}"
        )
    print("\nglob_pp = global peak-to-peak across all envs/steps; env_pp = mean per-env peak-to-peak")
    print("Yaw joints are Body_B* ; lift joints are B*_L* ; the rest are passive parallelogram joints.")
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
