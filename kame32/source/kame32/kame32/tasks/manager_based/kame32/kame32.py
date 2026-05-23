"""Articulation configuration for the Kame32 quadruped (spider-type) robot.

Kame32 is a small 4-legged "spider" robot (a redesign of the MiniKame). Each leg
has 2 actuated DoF driven by hobby servos (SG90 / MG90s):

* ``Body_B*`` : *yaw* joint (rotates the whole leg about the vertical / Z axis).
* ``B*_L*``   : *lift* joint (raises / lowers the leg about the X axis).

The foot is kept perpendicular to the ground by a passive **parallelogram** (a
four-bar linkage). In the USD this is modelled with 8 *passive* revolute joints
(``L*_F*`` and ``Lk*_F*``) plus 4 loop-closure joints that are excluded from the
articulation (``B*_Lk*``, ``physics:excludeFromArticulation = True``). We therefore
drive only the 8 real servos and leave the parallelogram joints free; the loop
constraints keep each foot perpendicular to the floor automatically.

Verified in sim: the all-zero joint pose is a stable, upright stance (base settles
to ~0.032 m on flat ground). Total mass ~0.33 kg, root body is ``Body``.
"""

from pathlib import Path

from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg
from isaaclab.sim import ArticulationRootPropertiesCfg, RigidBodyPropertiesCfg, UsdFileCfg

PROJECT_DIR = Path(__file__).resolve().parents[6]
KAME_USD_PATH = PROJECT_DIR / "assets" / "kame32.usd"

# The 8 servo-driven joints (2 per leg), split by function.
# yaw (Z axis) -- rotates the whole leg about the vertical axis (provides stride/propulsion)
KAME_YAW_JOINTS = ["Body_BLB", "Body_BRB", "Body_BLF", "Body_BRF"]
# lift (X axis) -- raises / lowers the leg
KAME_LIFT_JOINTS = ["BLB_LLB", "BRB_LRB", "BLF_LLF", "BRF_LRF"]
KAME_ACTUATED_JOINTS = KAME_YAW_JOINTS + KAME_LIFT_JOINTS

# The 8 passive parallelogram joints. Kept free; the loop constraint governs them.
KAME_PASSIVE_JOINTS = [
    "LLB_FLB",
    "LRB_FRB",
    "LLF_FLF",
    "LRF_FRF",
    "LkLB_FLB",
    "LkRB_FRB",
    "LkLF_FLF",
    "LkRF_FRF",
]


KAME_CFG = ArticulationCfg(
    spawn=UsdFileCfg(
        # NOTE: must be a *str* -- Isaac Lab does ``"4.5" in usd_path`` internally,
        # which raises if a pathlib.Path is passed.
        usd_path=str(KAME_USD_PATH),
        activate_contact_sensors=True,
        rigid_props=RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=10.0,
            max_angular_velocity=50.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=ArticulationRootPropertiesCfg(
            # disabled to avoid spurious internal collisions in the parallelogram
            enabled_self_collisions=False,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=1,
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        # Default to a *raised* stance (~0.051 m) instead of the low sprawl (~0.032 m):
        # the lift joints are mirrored, so raising the body needs left lifts negative and
        # right lifts positive (verified in sim). This gives clearance for a real gait and
        # a higher body, which is then reinforced by the base_height reward.
        pos=(0.0, 0.0, 0.06),
        joint_pos={
            "Body_B.*": 0.0,  # yaw joints neutral
            "BLB_LLB": -0.5,  # left-back lift  (raise)
            "BLF_LLF": -0.5,  # left-front lift (raise)
            "BRB_LRB": 0.5,  # right-back lift  (raise)
            "BRF_LRF": 0.5,  # right-front lift (raise)
            "L.*_F.*": 0.0,  # passive parallelogram joints
        },
        joint_vel={".*": 0.0},
    ),
    actuators={
        # The real servos. SG90/MG90s ~1.8 kg.cm stall -> ~0.18 N.m, ~0.1 s/60deg -> ~8 rad/s.
        # stiffness/damping are a starting point and the main thing to tune if the
        # gait looks too stiff (oscillation) or too soft (collapses under load).
        "servos": ImplicitActuatorCfg(
            joint_names_expr=KAME_ACTUATED_JOINTS,
            effort_limit_sim=0.18,
            velocity_limit_sim=8.0,
            stiffness=6.0,
            damping=0.2,
        ),
        # Passive parallelogram joints: no drive, the loop-closure constraint orients
        # the foot. Configured explicitly so all 16 articulation DoF are handled.
        "parallelogram": ImplicitActuatorCfg(
            joint_names_expr=KAME_PASSIVE_JOINTS,
            effort_limit_sim=0.0,
            velocity_limit_sim=100.0,
            stiffness=0.0,
            damping=0.0,
        ),
    },
)
