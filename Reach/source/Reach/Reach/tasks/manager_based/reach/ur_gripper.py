
# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for the Universal Robots.
Reference: https://github.com/ros-industrial/universal_robot
"""

from pathlib import Path
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg

PROJECT_DIR = Path(__file__).resolve().parents[6]
UR_USD_PATH = PROJECT_DIR / "assets" / "UR-with-gripper.usd"

UR_GRIPPER_CFG = ArticulationCfg(

    # Where is the USD file for this robot?
    spawn=sim_utils.UsdFileCfg(       
        usd_path=str(UR_USD_PATH),
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                rigid_body_enabled=True,
                max_linear_velocity=1000.0,
                max_angular_velocity=1000.0,
                max_depenetration_velocity=5.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True, 
                solver_position_iteration_count=8, 
                solver_velocity_iteration_count=0
            ),
        ),
    # What is its initial position of the robot, and its joints?
        init_state=ArticulationCfg.InitialStateCfg(
            joint_pos={
                "shoulder_pan_joint": 0.0,
                "shoulder_lift_joint": -1.5708,
                "elbow_joint": 1.5708,
                "wrist_1_joint": -1.5708,
                "wrist_2_joint": -1.5708,
                "wrist_3_joint": 0.0,

                "finger_joint": 0.0,
                ".*_inner_finger_joint": 0.0,
                ".*_inner_finger_pad_joint": 0.0,
                ".*_outer_.*_joint": 0.0,
            },
        ),
    # What parts of the robot move, and how stiff / damped are they?
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"], 
                effort_limit_sim=87.0,
                stiffness=800.0,
                damping=40.0,
            ),

            "gripper": ImplicitActuatorCfg(
                joint_names_expr=["finger_joint"],
                effort_limit_sim=200.0,
                velocity_limit_sim=2.0,
                stiffness=500.0,
                damping=50.0,
                friction=0.0,
                armature=0.0,
            ),

            # the auxiliary actuator joint for gripper
            "gripper_aux": ImplicitActuatorCfg(
                joint_names_expr=[".*_inner_finger_joint"],
                effort_limit_sim=1.0,
                velocity_limit_sim=1.0,
                stiffness=0.2,
                damping=0.001,
                friction=0.0,
                armature=0.0,
            ),

            # the passive joints for gripper
            "gripper_passive": ImplicitActuatorCfg(
                joint_names_expr=[".*_inner_finger_pad_joint", ".*_outer_finger_joint", "right_outer_knuckle_joint"],
                effort_limit_sim=1.0,
                velocity_limit_sim=1.0,
                stiffness=0.0,
                damping=0.0,
                friction=0.0,
                armature=0.0,
            )
        }
)
