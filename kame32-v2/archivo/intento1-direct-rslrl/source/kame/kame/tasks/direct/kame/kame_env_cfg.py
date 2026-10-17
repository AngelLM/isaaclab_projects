# spdrbot3_env_cfg.py
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import SimulationCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass
from isaaclab.sensors import ContactSensorCfg

from isaaclab_assets.robots.kame import KAME_CFG  # isort: skip


@configclass
class EventCfg:
    """Configuration for randomization."""

    physics_material = EventTerm(
        func=mdp.randomize_rigid_body_material,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names=".*"),
            "static_friction_range": (0.8, 0.8),
            "dynamic_friction_range": (0.6, 0.6),
            "restitution_range": (0.0, 0.0),
            "num_buckets": 64,
        },
    )

@configclass
class KameEnvCfg(DirectRLEnvCfg):
    # env
    episode_length_s = 20.0
    decimation = 4
    action_scale = 0.25
    action_space = 8
    observation_space = 39
    state_space = 0

    # simulation
    sim: SimulationCfg = SimulationCfg(
        dt=1 / 400,
        render_interval=1,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
            restitution=0.0,
        ),
    )

    contact_sensor: ContactSensorCfg = ContactSensorCfg(
        prim_path="/World/envs/env_.*/Robot/Kame32/.*",  # Path to base_link in cloned envs
        history_length=5,
        update_period=0.0025,  # Matches sim dt = 1/400
        track_air_time=True,  # Not needed for base
    )

    # scene
    scene: InteractiveSceneCfg = InteractiveSceneCfg(num_envs=512, env_spacing=2.0, replicate_physics=True)

    # events
    events: EventCfg = EventCfg()

    # robot
    robot: ArticulationCfg = KAME_CFG.replace(prim_path="/World/envs/env_.*/Robot")

@configclass
class KameEnvCfgPhase1(KameEnvCfg):
    """Phase 1: first steps"""
    phase = 1
    forward_reward_weight = 1.0
    alive_reward_weight = 0.5
    action_penalty_weight = -0.01
    stability_reward_weight = 0.0
    no_contact_penalty_weight = 0.0
    contact_var_reward_weight = 0.0
    air_time_penalty_weight = 0.0
    max_air_time_penalty_weight = 0.0
    contact_error_penalty_weight = 0.0
    air_time_balance_penalty_weight = 0.0

class KameEnvCfgPhase2(KameEnvCfg):
    """Phase 2: stability and contact"""
    phase = 2
    forward_reward_weight = 1.0
    alive_reward_weight = 0.5
    action_penalty_weight = -0.01
    stability_reward_weight = 0.3
    no_contact_penalty_weight = -0.5
    contact_var_reward_weight = 0.2
    air_time_penalty_weight = -0.05
    max_air_time_penalty_weight = -0.1
    contact_error_penalty_weight = 0.0
    air_time_balance_penalty_weight = 0.0

class KameEnvCfgPhase3(KameEnvCfg):
    """Phase 3: stability, contact, and balance"""
    phase = 3
    forward_reward_weight = 1.0
    alive_reward_weight = 0.5
    action_penalty_weight = -0.01
    stability_reward_weight = 0.3
    no_contact_penalty_weight = -0.5
    contact_var_reward_weight = 0.2
    air_time_penalty_weight = -0.05
    max_air_time_penalty_weight = -0.1
    contact_error_penalty_weight = -0.2
    air_time_balance_penalty_weight = -0.1