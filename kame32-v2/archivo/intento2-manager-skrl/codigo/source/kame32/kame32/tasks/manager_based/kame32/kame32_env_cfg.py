# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Velocity-tracking locomotion environment for the Kame32 quadruped.

The robot is rewarded for tracking a (forward-biased) base-velocity command, i.e.
for walking forward, and the episode ends if it tips over or its body hits the
ground. The design follows Isaac Lab's manager-based ``velocity`` locomotion task
(the one used for ANYmal / A1 / Go1), adapted to this 8-servo spider robot.
"""

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass

from . import mdp
from .kame32 import KAME_ACTUATED_JOINTS, KAME_CFG, KAME_LIFT_JOINTS, KAME_YAW_JOINTS

##
# Scene definition
##


@configclass
class Kame32SceneCfg(InteractiveSceneCfg):
    """Scene: flat ground, the Kame32 robot, and a contact sensor (rewards only)."""

    # flat ground plane
    terrain = TerrainImporterCfg(
        prim_path="/World/ground",
        terrain_type="plane",
        collision_group=-1,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
        ),
        debug_vis=False,
    )

    # robot (USD default prim is "Kame32", so bodies live under .../Robot/Kame32/<body>)
    robot: ArticulationCfg = KAME_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    # contact sensor on all robot bodies; used only by reward / termination terms
    contact_forces = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/Kame32/.*",
        history_length=3,
        track_air_time=True,
    )

    # lights
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=750.0),
    )


##
# MDP settings
##


@configclass
class CommandsCfg:
    """Base-velocity command. Forward-biased so the robot learns to walk ahead."""

    base_velocity = mdp.Kame32VelocityCommandCfg(
        asset_name="robot",
        resampling_time_range=(3.0, 5.0),  # resample more often -> more speed variety per episode
        rel_standing_envs=0.02,
        rel_heading_envs=1.0,
        heading_command=False,
        debug_vis=True,
        ranges=mdp.UniformVelocityCommandCfg.Ranges(
            # wide spread of speeds (reverse, slow, up to ~0.45 m/s) and real turns
            lin_vel_x=(-0.15, 0.45),
            lin_vel_y=(0.0, 0.0),
            ang_vel_z=(-1.0, 1.0),
        ),
    )


@configclass
class ActionsCfg:
    """Position targets for the 8 servos, as offsets from the default pose."""

    joint_pos = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=KAME_ACTUATED_JOINTS,
        scale=0.5,
        use_default_offset=True,
    )


@configclass
class ObservationsCfg:
    """Blind (no-sensor) observations: only the command and the last servo command.

    This variant drops the IMU entirely, for the case where no IMU can be fitted to the robot.
    The policy has NO feedback from the world: it only knows the velocity command it is given
    and the history of its own past actions. That makes it essentially feedforward (blind) --
    it learns a cyclic gait and replays it, using the action history to track where in the cycle
    it is. It is not reactive: it cannot feel a tilt or a push and correct for it.
    """

    @configclass
    class PolicyCfg(ObsGroup):
        # velocity command
        velocity_commands = ObsTerm(func=mdp.generated_commands, params={"command_name": "base_velocity"})
        # last position command sent to the servos (the only proprioceptive signal available)
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self) -> None:
            self.enable_corruption = True
            self.concatenate_terms = True
            # stack the last 5 observations: with no IMU, the action history is the only temporal
            # signal the policy has to infer the gait phase (11 x 5 = 55)
            self.history_length = 5

    policy: PolicyCfg = PolicyCfg()


@configclass
class EventCfg:
    """Domain randomization and resets."""

    # startup: randomize ground friction and add a little mass to the body
    physics_material = EventTerm(
        func=mdp.randomize_rigid_body_material,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names=".*"),
            "static_friction_range": (0.8, 1.2),
            "dynamic_friction_range": (0.6, 1.0),
            "restitution_range": (0.0, 0.0),
            "num_buckets": 64,
        },
    )
    add_base_mass = EventTerm(
        func=mdp.randomize_rigid_body_mass,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names="Body"),
            "mass_distribution_params": (-0.02, 0.05),
            "operation": "add",
        },
    )

    # reset
    reset_base = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {"x": (-0.1, 0.1), "y": (-0.1, 0.1), "yaw": (-3.14, 3.14)},
            "velocity_range": {
                "x": (-0.1, 0.1),
                "y": (-0.1, 0.1),
                "z": (0.0, 0.0),
                "roll": (-0.2, 0.2),
                "pitch": (-0.2, 0.2),
                "yaw": (-0.2, 0.2),
            },
        },
    )
    reset_robot_joints = EventTerm(
        func=mdp.reset_joints_by_offset,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot", joint_names=KAME_ACTUATED_JOINTS),
            "position_range": (-0.1, 0.1),
            "velocity_range": (0.0, 0.0),
        },
    )

    # interval: random pushes for robustness
    push_robot = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(8.0, 12.0),
        params={"velocity_range": {"x": (-0.15, 0.15), "y": (-0.15, 0.15)}},
    )


@configclass
class RewardsCfg:
    """Spot-style reward set, scaled for the small kame32 robot.

    Large positive task rewards (track command, step with proper timing, lift the
    swing foot, trot) dominate; penalties suppress foot sliding and high-frequency
    joint "buzzing". This replaces the earlier simple velocity-tracking set, which
    the policy could exploit by vibrating in place and sliding instead of walking.
    """

    # -- task
    base_linear_velocity = RewTerm(
        func=mdp.base_linear_velocity_reward,
        weight=5.0,
        # std widened with the higher top speed; ramp_rate rewards going fast a bit more
        params={"asset_cfg": SceneEntityCfg("robot"), "std": 0.18, "ramp_at_vel": 0.15, "ramp_rate": 0.75},
    )
    base_angular_velocity = RewTerm(
        func=mdp.base_angular_velocity_reward,
        weight=4.0,  # turning is commanded up to +-1 rad/s and forces the yaw joints to swing
        params={"asset_cfg": SceneEntityCfg("robot"), "std": 0.5},
    )
    air_time = RewTerm(
        func=mdp.air_time_reward,
        weight=5.0,
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "sensor_cfg": SceneEntityCfg("contact_forces", body_names="Foot_.*"),
            "mode_time": 0.3,  # longer target swing/stance -> longer, larger steps
            "velocity_threshold": 0.05,
        },
    )
    foot_clearance = RewTerm(
        func=mdp.foot_clearance_reward,
        weight=2.0,
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names="Foot_.*"),
            "target_height": 0.055,  # lift swing foot higher -> bigger lift-joint motions
            "std": 0.01,
            "tanh_mult": 2.0,
        },
    )
    base_height = RewTerm(
        func=mdp.base_height_reward,
        weight=1.0,  # mild: keep it from crawling, but amplitude/oscillation take priority now
        params={"asset_cfg": SceneEntityCfg("robot"), "target_height": 0.05, "std": 0.025},
    )
    # reward wide swinging of the yaw joints (the stride) and, more lightly, the lift joints,
    # so the legs make big visible strokes instead of tiny limping adjustments
    yaw_swing = RewTerm(
        func=mdp.joint_swing_reward,
        weight=0.2,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=KAME_YAW_JOINTS), "max_speed": 8.0},
    )
    lift_swing = RewTerm(
        func=mdp.joint_swing_reward,
        weight=0.35,  # raised: the lift joints were barely moving; push for wider lift motion
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=KAME_LIFT_JOINTS), "max_speed": 8.0},
    )
    gait = RewTerm(
        func=mdp.GaitReward,
        weight=10.0,  # strong: forces a coordinated trot using all four legs
        params={
            "std": 0.1,
            "max_err": 0.2,
            "velocity_threshold": 0.05,
            # diagonal trot: FL+BR together, FR+BL together
            "synced_feet_pair_names": (("Foot_LeftFront", "Foot_RightBack"), ("Foot_RightFront", "Foot_LeftBack")),
            "asset_cfg": SceneEntityCfg("robot"),
            "sensor_cfg": SceneEntityCfg("contact_forces"),
        },
    )

    # -- penalties
    terminating = RewTerm(func=mdp.is_terminated, weight=-1.0)  # discourage falling (excludes timeouts)
    action_smoothness = RewTerm(func=mdp.action_smoothness_penalty, weight=-1.5)  # kills buzzing, allows smooth swings
    air_time_variance = RewTerm(
        func=mdp.air_time_variance_penalty,
        weight=-2.0,  # stronger: penalizes a "dead" leg (uneven air/contact across feet)
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names="Foot_.*")},
    )
    base_motion = RewTerm(func=mdp.base_motion_penalty, weight=-0.5, params={"asset_cfg": SceneEntityCfg("robot")})
    base_orientation = RewTerm(
        func=mdp.base_orientation_penalty, weight=-3.0, params={"asset_cfg": SceneEntityCfg("robot")}
    )
    foot_slip = RewTerm(
        func=mdp.foot_slip_penalty,
        weight=-0.5,
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names="Foot_.*"),
            "sensor_cfg": SceneEntityCfg("contact_forces", body_names="Foot_.*"),
            "threshold": 1.0,
        },
    )
    joint_acc = RewTerm(
        func=mdp.joint_acceleration_penalty,
        weight=-1.0e-4,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=KAME_ACTUATED_JOINTS)},
    )
    joint_pos = RewTerm(
        func=mdp.joint_position_penalty,
        weight=-0.01,  # almost off: must not suppress the large stepping/yaw motions
        params={
            "asset_cfg": SceneEntityCfg("robot", joint_names=KAME_ACTUATED_JOINTS),
            "stand_still_scale": 5.0,
            "velocity_threshold": 0.05,
        },
    )
    joint_torques = RewTerm(
        func=mdp.joint_torques_penalty,
        weight=-5.0e-4,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=KAME_ACTUATED_JOINTS)},
    )
    joint_vel = RewTerm(
        func=mdp.joint_velocity_penalty,
        weight=-2.0e-3,  # lowered: do not penalize the fast yaw swings we now want
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=KAME_ACTUATED_JOINTS)},
    )


@configclass
class TerminationsCfg:
    """Termination terms."""

    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    # body chassis hits the ground -> fell
    base_contact = DoneTerm(
        func=mdp.illegal_contact,
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names="Body"), "threshold": 1.0},
    )
    # tipped over too far (> ~46 deg from upright)
    bad_orientation = DoneTerm(func=mdp.bad_orientation, params={"limit_angle": 0.8})


##
# Environment configuration
##


@configclass
class Kame32EnvCfg(ManagerBasedRLEnvCfg):
    """Configuration for the Kame32 velocity-tracking locomotion environment."""

    # Scene settings
    scene: Kame32SceneCfg = Kame32SceneCfg(num_envs=4096, env_spacing=1.0)
    # Basic settings
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    # MDP settings
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventCfg = EventCfg()

    def __post_init__(self) -> None:
        """Post initialization."""
        # general settings
        self.decimation = 4  # 200 Hz physics -> 50 Hz control
        self.episode_length_s = 15.0
        # viewer settings (small robot)
        self.viewer.eye = (1.2, 1.2, 0.8)
        self.viewer.lookat = (0.0, 0.0, 0.0)
        # simulation settings
        self.sim.dt = 0.005
        self.sim.render_interval = self.decimation
        # tick the contact sensor at the physics rate
        if self.scene.contact_forces is not None:
            self.scene.contact_forces.update_period = self.sim.dt
        # NOTE: velocity marker sizes are handled by Kame32VelocityCommandCfg (linear + angular)


@configclass
class Kame32EnvCfg_PLAY(Kame32EnvCfg):
    """Lightweight config for visualizing a trained policy."""

    def __post_init__(self) -> None:
        super().__post_init__()
        # smaller scene
        self.scene.num_envs = 50
        self.scene.env_spacing = 1.0
        # disable randomization for clean playback
        self.observations.policy.enable_corruption = False
        self.events.push_robot = None
        # fixed, representative walking speed (edit to view other speeds/turns)
        self.commands.base_velocity.ranges.lin_vel_x = (0.3, 0.3)
        self.commands.base_velocity.ranges.lin_vel_y = (0.0, 0.0)
        self.commands.base_velocity.ranges.ang_vel_z = (0.0, 0.0)
