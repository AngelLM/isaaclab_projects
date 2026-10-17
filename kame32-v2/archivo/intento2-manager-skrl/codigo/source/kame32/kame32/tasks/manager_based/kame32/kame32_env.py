# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Manager-based RL env for kame32 that also logs the angular range of each active joint.

This is a thin subclass of :class:`ManagerBasedRLEnv`. Its only extra job is to track, for
each of the 8 driven servos, the minimum and maximum angle reached during an episode, and to
write the per-episode range (in degrees) into ``extras["log"]`` when an environment resets.
skrl picks those entries up and they appear in TensorBoard as ``Info / JointRange/<joint>``,
which makes it easy to see at a glance how wide each joint is actually moving (in particular
the lift joints, which tend to stay too still).
"""

from __future__ import annotations

import math
import torch
from collections.abc import Sequence

from isaaclab.envs import ManagerBasedRLEnv, ManagerBasedRLEnvCfg

from .kame32 import KAME_ACTUATED_JOINTS

_RAD2DEG = 180.0 / math.pi


class Kame32Env(ManagerBasedRLEnv):
    """ManagerBasedRLEnv that logs the per-episode angular range of each active joint."""

    def __init__(self, cfg: ManagerBasedRLEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        # resolve the 8 driven joints (ids and names, kept in matching order)
        self._jr_ids, self._jr_names = self.scene["robot"].find_joints(KAME_ACTUATED_JOINTS)
        joint_pos = self.scene["robot"].data.joint_pos[:, self._jr_ids]
        self._jr_min = joint_pos.clone()
        self._jr_max = joint_pos.clone()

    def step(self, action: torch.Tensor):
        out = super().step(action)
        # accumulate min/max of the active joints over the episode
        joint_pos = self.scene["robot"].data.joint_pos[:, self._jr_ids]
        self._jr_min = torch.minimum(self._jr_min, joint_pos)
        self._jr_max = torch.maximum(self._jr_max, joint_pos)
        return out

    def _reset_idx(self, env_ids: Sequence[int]):
        # compute the range for the finishing episodes before the trackers are cleared
        log_range = None
        if getattr(self, "_jr_min", None) is not None:
            rng = (self._jr_max[env_ids] - self._jr_min[env_ids]) * _RAD2DEG
            log_range = {f"JointRange/{name}": rng[:, i].mean() for i, name in enumerate(self._jr_names)}
        # parent resets extras["log"] and fills it with the manager logs
        super()._reset_idx(env_ids)
        # add our entries and restart the trackers for the reset envs
        if log_range is not None:
            self.extras["log"].update(log_range)
            joint_pos = self.scene["robot"].data.joint_pos[:, self._jr_ids]
            self._jr_min[env_ids] = joint_pos[env_ids]
            self._jr_max[env_ids] = joint_pos[env_ids]
