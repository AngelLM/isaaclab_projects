# spdrbot3_env.py
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import gymnasium as gym
import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.sensors import ContactSensor

from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane

from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
import isaaclab.utils.math as math_utils

from .kame_env_cfg import KameEnvCfg

def define_markers() -> VisualizationMarkers:
    """Define markers with various different shapes."""
    marker_cfg = VisualizationMarkersCfg(
        prim_path="/Visuals/myMarkers",
        markers={
                "forward": sim_utils.UsdFileCfg(
                    usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/UIElements/arrow_x.usd",
                    scale=(0.25, 0.25, 0.5),
                    visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 1.0, 1.0)),
                ),
                "command": sim_utils.UsdFileCfg(
                    usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/UIElements/arrow_x.usd",
                    scale=(0.25, 0.25, 0.5),
                    visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.0, 0.0)),
                ),
        },
    )
    return VisualizationMarkers(cfg=marker_cfg)

class KameEnv(DirectRLEnv):
    cfg: KameEnvCfg

    def __init__(self, cfg: KameEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        # Joint position command (deviation from default joint positions)
        self.actions = torch.zeros(self.num_envs, gym.spaces.flatdim(self.single_action_space), device=self.device)
        self._previous_actions = torch.zeros(
            self.num_envs, gym.spaces.flatdim(self.single_action_space), device=self.device
        )

        # IDs de articulaciones (mapeo del USD al orden de la red)
        self.actuated_joint_names = [
            "Body_BLB", "Body_BRB", "Body_BLF", "Body_BRF",
            "BLB_LLB", "BRB_LRB", "BLF_LLF", "BRF_LRF",
        ]
        self.actuated_joint_ids, _ = self.robot.find_joints(self.actuated_joint_names)

        self.feet_names = ["Foot_LeftFront", "Foot_LeftBack", "Foot_RightFront", "Foot_RightBack"]  # o como se llamen tus feet
        self.feet_ids, _ = self._contact_sensor.find_bodies(self.feet_names)

        self.bracket_names = [
            "Bracket_LeftFront",
            "Bracket_RightFront",
            "Bracket_LeftBack",
            "Bracket_RightBack",
        ]

        self.bracket_ids, _ = self._contact_sensor.find_bodies(self.bracket_names)


    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot)
        self.scene.articulations["robot"] = self.robot

        # Contact Sensor
        self._contact_sensor = ContactSensor(self.cfg.contact_sensor)
        self.scene.sensors["contact_sensor"] = self._contact_sensor

        # add ground plane
        spawn_ground_plane(prim_path="/World/ground", cfg=GroundPlaneCfg())

        self.scene.clone_environments(copy_from_source=False)

        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)


        self.visualization_markers = define_markers()

        # setting aside useful variables for later
        self.up_dir = torch.tensor([0.0, 0.0, 1.0]).cuda() # z-up
        self.yaws = torch.zeros((self.cfg.scene.num_envs, 1)).cuda()                            # yaw angles buffer for each env
        self.commands = torch.randn((self.cfg.scene.num_envs, 3)).cuda()                        # random velocity commands for each env
        self.commands[:,-1] = 0.0                                                               # no vertical component in the command
        self.commands = self.commands/torch.linalg.norm(self.commands, dim=1, keepdim=True)     # normalize commands to unit vectors

        # offsets to account for atan range and keep things on [-pi, pi]. yaw = atan(vy/vx). Problematic cases when vx = 0 or when both vx and vy are negative.
        ratio = self.commands[:,1]/(self.commands[:,0]+1E-8) # avoid division by zero
        gzero = torch.where(self.commands > 0, True, False)  # boolean mask for positive values. F.g if command = [0.5, -0.3], gzero = [True, False]
        lzero = torch.where(self.commands < 0, True, False)  # boolean mask for negative values. F.g if command = [0.5, -0.3], lzero = [False, True]
        # Quadrant determination. If vx>0 and vy>0 then yaw in Q1, if vx<0 and vy>0 then yaw in Q2, if vx<0 and vy<0 then yaw in Q3, if vx>0 and vy<0 then yaw in Q4.
        plus = lzero[:,0]*gzero[:,1]
        minus = lzero[:,0]*lzero[:,1]
        offsets = torch.pi*plus - torch.pi*minus # offsets of +pi for Q2, -pi for Q3, 0 for Q1 and Q4
        self.yaws = torch.atan(ratio).reshape(-1,1) + offsets.reshape(-1,1) # final yaw angles in radians

        self.marker_locations = torch.zeros((self.cfg.scene.num_envs, 3)).cuda()            # marker locations buffer
        self.marker_offset = torch.zeros((self.cfg.scene.num_envs, 3)).cuda()               # marker offset buffer
        self.marker_offset[:,-1] = 0.5                                                      # markers are placed 0.5m above the robot base  
        self.forward_marker_orientations = torch.zeros((self.cfg.scene.num_envs, 4)).cuda() # forward marker orientations buffer
        self.command_marker_orientations = torch.zeros((self.cfg.scene.num_envs, 4)).cuda() # command marker orientations buffer

        self.air_time_counter = torch.zeros(self.num_envs, 4, device=self.device)


    def _pre_physics_step(self, actions):
        self.actions = actions.clone()
        self._visualize_markers()

    def _apply_action(self):
        # Apply the actions as joint position targets for the actuated joints
        all_targets = self.robot.data.default_joint_pos.clone()
        all_targets[:, self.actuated_joint_ids] = self.actions
        self.robot.set_joint_position_target(all_targets)

    def _get_observations(self) -> dict:
        self.velocity = self.robot.data.root_com_vel_w                                                          # get the linear velocity of the robot in world frame
        self.forwards = math_utils.quat_apply(self.robot.data.root_link_quat_w, self.robot.data.FORWARD_VEC_B) # get the forward direction of the robot in world frame
        
        dot = torch.sum(self.forwards * self.commands, dim=-1, keepdim=True)                            # dot product between robot's forward direction and command direction. It indicates how aligned the robot is with the command.
        cross = torch.cross(self.forwards, self.commands, dim=-1)[:,-1].reshape(-1,1)                   # z-component of the cross product between robot's forward direction and command direction. It indicates the direction to turn to align with the command.
        forward_speed = self.robot.data.root_com_lin_vel_b[:,0].reshape(-1,1)                           # forward speed in the robot's base frame   
        self._previous_actions = self.actions.clone()
        
        obs = torch.cat(
            [
                tensor
                for tensor in (
                    self.robot.data.root_lin_vel_b,                                     # Dim 3
                    self.robot.data.root_ang_vel_b,                                     # Dim 3
                    self.robot.data.projected_gravity_b,                                # Dim 3
                    self.commands,                                                      # Dim 3
                    self.robot.data.joint_pos - self.robot.data.default_joint_pos,      # Dim 8
                    self.robot.data.joint_vel,                                          # Dim 8                    
                    self.actions,                                                       # Dim 8
                    dot,                                                                # Dim 1
                    cross,                                                              # Dim 1
                    forward_speed,                                                      # Dim 1
                )
                if tensor is not None
            ],
            dim=-1,
        )

        obs = torch.clamp(obs, -5.0, 5.0)
        
        observations = {"policy": obs}
        return observations


    def _get_rewards(self) -> torch.Tensor:

        # ---------------- BASE REWARD ----------------
        forward_reward = self.robot.data.root_com_lin_vel_b[:, 0]
        alignment_reward = torch.sum(self.forwards * self.commands, dim=-1)

        action_penalty = torch.sum(self.actions ** 2, dim=1)
        alive_reward = (~self.reset_buf).float()

        # ---------------- CONTACT REWARDS ----------------
        contact_forces = self._contact_sensor.data.net_forces_w
        foot_forces = torch.norm(contact_forces[:, self.feet_ids, :], dim=-1)

        contact = foot_forces > 1.0
        
        num_contacts = torch.sum(contact, dim=1)

        # objetivo: ~3 patas en contacto (crawl gait)
        contact_target = 3.0
        contact_error = torch.abs(num_contacts.float() - contact_target)

        # ✔ estabilidad → mínimo 3 patas
        stability_reward = (num_contacts >= 3).float()

        # ❌ penalizar quedarse sin contacto (salto / caída)
        no_contact_penalty = (num_contacts == 0).float()

        # ✔ uso equilibrado de patas
        contact_var = torch.var(contact.float(), dim=1)

        # ✔ penalizar tiempo en el aire
        # incrementar tiempo en aire
        self.air_time_counter += (~contact).float()

        # resetear cuando hay contacto
        self.air_time_counter *= (~contact).float()
        
        air_time_penalty = torch.sum(self.air_time_counter, dim=1)
        max_air_time = torch.max(self.air_time_counter, dim=1)[0]

        # equilibrio entre patas (muy importante)
        mean_air_time = torch.mean(self.air_time_counter, dim=1, keepdim=True)

        air_time_balance = torch.mean(
            torch.abs(self.air_time_counter - mean_air_time), dim=1
        )

        # ---------------- FINAL REWARD ----------------

        reward = (
            self.cfg.forward_reward_weight * forward_reward * torch.exp(alignment_reward)
            + self.cfg.alive_reward_weight * alive_reward
            + self.cfg.action_penalty_weight * action_penalty
            + self.cfg.stability_reward_weight * stability_reward
            + self.cfg.no_contact_penalty_weight * no_contact_penalty
            + self.cfg.contact_var_reward_weight * contact_var
            + self.cfg.air_time_penalty_weight * air_time_penalty
            + self.cfg.max_air_time_penalty_weight * max_air_time
            + self.cfg.contact_error_penalty_weight * contact_error
            - self.cfg.air_time_balance_penalty_weight * air_time_balance
        )

        return reward


    def _get_dones(self):
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        base_height = self.robot.data.root_pos_w[:, 2]
        died = base_height <= 0.01

        # 🔥 NUEVO
        contact_forces = self._contact_sensor.data.net_forces_w
        bracket_forces = torch.norm(
            contact_forces[:, self.bracket_ids, :], dim=-1
        )
        bracket_contact = torch.any(bracket_forces > 1.0, dim=1)

        died = died | bracket_contact

        return died, time_out


    def _reset_idx(self, env_ids: torch.Tensor | None):
        if env_ids is None or len(env_ids) == self.num_envs:
            env_ids = self.robot._ALL_INDICES
        self.robot.reset(env_ids)
        super()._reset_idx(env_ids)

        if len(env_ids) == self.num_envs:
            # Spread out the resets to avoid spikes in training when many environments reset at a similar time
            self.episode_length_buf[:] = torch.randint_like(self.episode_length_buf, high=int(self.max_episode_length))

        self.actions[env_ids] = 0.0
        self._previous_actions[env_ids] = 0.0

        # pick new commands for reset envs and normalize them just like in the setup
        self.commands[env_ids] = torch.randn((len(env_ids), 3)).cuda()
        self.commands[env_ids,-1] = 0.0
        self.commands[env_ids] = self.commands[env_ids]/torch.linalg.norm(self.commands[env_ids], dim=1, keepdim=True)


        # Reset robot state
        joint_pos = self.robot.data.default_joint_pos[env_ids]
        joint_vel = self.robot.data.default_joint_vel[env_ids]
        default_root_state = self.robot.data.default_root_state[env_ids]
        default_root_state[:, :3] += self.scene.env_origins[env_ids]
        self.robot.write_root_pose_to_sim(default_root_state[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(default_root_state[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(joint_pos, joint_vel, None, env_ids)

        # recalculate the orientations for the command markers with the new commands
        ratio = self.commands[env_ids][:,1]/(self.commands[env_ids][:,0]+1E-8)
        gzero = torch.where(self.commands[env_ids] > 0, True, False)
        lzero = torch.where(self.commands[env_ids]< 0, True, False)
        plus = lzero[:,0]*gzero[:,1]
        minus = lzero[:,0]*lzero[:,1]
        offsets = torch.pi*plus - torch.pi*minus
        self.yaws[env_ids] = torch.atan(ratio).reshape(-1,1) + offsets.reshape(-1,1)

        self._visualize_markers()
    
    def _visualize_markers(self):
        # get marker locations and orientations
        self.marker_locations = self.robot.data.root_pos_w                                                    # marker locations are at the robot base position
        self.forward_marker_orientations = self.robot.data.root_quat_w                                        # forward marker orientations match the robot base orientation
        self.command_marker_orientations = math_utils.quat_from_angle_axis(self.yaws, self.up_dir).squeeze()  # command marker orientations are derived from the command yaw angles

        # offset markers so they are above the jetbot
        loc = self.marker_locations + self.marker_offset                                            # apply offset to marker locations
        loc = torch.vstack((loc, loc))                                                              # duplicate for both markers size(2*num_envs, 3)
        rots = torch.vstack((self.forward_marker_orientations, self.command_marker_orientations))   # stack orientations for both markers size(2*num_envs, 4)

        # render the markers
        all_envs = torch.arange(self.cfg.scene.num_envs)                                            # env indices size(num_envs,). F.g if num_envs=3, all_envs=[0,1,2]
        indices = torch.hstack((torch.zeros_like(all_envs), torch.ones_like(all_envs)))             # marker indices: 0 for forward markers, 1 for command markers size(2*num_envs,). F.g if num_envs=3, indices=[0,0,0,1,1,1]
        self.visualization_markers.visualize(loc, rots, marker_indices=indices)                     # visualize markers