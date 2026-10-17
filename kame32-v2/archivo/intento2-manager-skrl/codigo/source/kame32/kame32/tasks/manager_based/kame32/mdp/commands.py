# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Velocity command for kame32 with visible linear and angular velocity markers.

Isaac Lab's stock ``UniformVelocityCommand`` only draws the linear velocity as a single
arrow, and it places that arrow 0.5 m above the base (sized for a one-metre robot). On a
15 cm robot that arrow ends up as a thin sliver floating high above and is effectively
invisible. This subclass fixes two things: it draws the markers just above the robot at a
size that suits kame32, and it adds a second pair of markers for the angular (yaw) velocity.

The linear velocity is shown as a horizontal arrow pointing in the direction of travel, and
the angular velocity as a horizontal arrow pointing to the side the robot turns toward (left
for a left turn, right for a right turn) whose length grows with the turn rate. Green marks the
commanded value and blue the robot's actual value, so linear and angular are told apart by their
orientation (forward versus sideways) and command and actual by colour.
"""

from __future__ import annotations

import math
import torch

import isaaclab.utils.math as math_utils
from isaaclab.envs.mdp.commands.commands_cfg import UniformVelocityCommandCfg
from isaaclab.envs.mdp.commands.velocity_command import UniformVelocityCommand
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg
from isaaclab.markers.config import BLUE_ARROW_X_MARKER_CFG, GREEN_ARROW_X_MARKER_CFG
from isaaclab.utils import configclass


class Kame32VelocityCommand(UniformVelocityCommand):
    """Velocity command that visualizes both the linear and the angular velocity."""

    cfg: "Kame32VelocityCommandCfg"

    def _set_debug_vis_impl(self, debug_vis: bool):
        if debug_vis:
            if not hasattr(self, "goal_vel_visualizer"):
                self.goal_vel_visualizer = VisualizationMarkers(self.cfg.goal_vel_visualizer_cfg)
                self.current_vel_visualizer = VisualizationMarkers(self.cfg.current_vel_visualizer_cfg)
                self.goal_ang_vel_visualizer = VisualizationMarkers(self.cfg.goal_ang_vel_visualizer_cfg)
                self.current_ang_vel_visualizer = VisualizationMarkers(self.cfg.current_ang_vel_visualizer_cfg)
            for vis in (
                self.goal_vel_visualizer,
                self.current_vel_visualizer,
                self.goal_ang_vel_visualizer,
                self.current_ang_vel_visualizer,
            ):
                vis.set_visibility(True)
        else:
            if hasattr(self, "goal_vel_visualizer"):
                for vis in (
                    self.goal_vel_visualizer,
                    self.current_vel_visualizer,
                    self.goal_ang_vel_visualizer,
                    self.current_ang_vel_visualizer,
                ):
                    vis.set_visibility(False)

    def _debug_vis_callback(self, event):
        if not self.robot.is_initialized:
            return
        # place the markers just above the (small) robot
        base_pos_w = self.robot.data.root_pos_w.clone()
        base_pos_w[:, 2] += self.cfg.marker_height
        # linear velocity: horizontal arrows
        lin_goal_scale, lin_goal_quat = self._resolve_xy_velocity_to_arrow(self.command[:, :2])
        lin_cur_scale, lin_cur_quat = self._resolve_xy_velocity_to_arrow(self.robot.data.root_lin_vel_b[:, :2])
        self.goal_vel_visualizer.visualize(base_pos_w, lin_goal_quat, lin_goal_scale)
        self.current_vel_visualizer.visualize(base_pos_w, lin_cur_quat, lin_cur_scale)
        # angular velocity: horizontal side arrows (point toward the turn direction)
        ang_goal_scale, ang_goal_quat = self._resolve_ang_velocity_to_arrow(self.command[:, 2])
        ang_cur_scale, ang_cur_quat = self._resolve_ang_velocity_to_arrow(self.robot.data.root_ang_vel_b[:, 2])
        self.goal_ang_vel_visualizer.visualize(base_pos_w, ang_goal_quat, ang_goal_scale)
        self.current_ang_vel_visualizer.visualize(base_pos_w, ang_cur_quat, ang_cur_scale)

    def _resolve_xy_velocity_to_arrow(self, xy_velocity: torch.Tensor):
        """Convert the planar velocity into a horizontal arrow pointing along it.

        The length is a fixed base plus a term that grows with the speed, so the arrow stays
        clearly visible even at low speed (a purely speed-proportional length becomes a tiny
        sliver for this slow robot). The y/z components are the marker thickness from the cfg.
        """
        default_scale = self.goal_vel_visualizer.cfg.markers["arrow"].scale
        arrow_scale = torch.tensor(default_scale, device=self.device).repeat(xy_velocity.shape[0], 1)
        speed = torch.linalg.norm(xy_velocity, dim=1)
        arrow_scale[:, 0] = self.cfg.lin_arrow_base + speed * self.cfg.lin_arrow_gain
        # direction: point along the velocity, converted from base frame to world frame
        heading_angle = torch.atan2(xy_velocity[:, 1], xy_velocity[:, 0])
        zeros = torch.zeros_like(heading_angle)
        arrow_quat = math_utils.quat_from_euler_xyz(zeros, zeros, heading_angle)
        arrow_quat = math_utils.quat_mul(self.robot.data.root_quat_w, arrow_quat)
        return arrow_scale, arrow_quat

    def _resolve_ang_velocity_to_arrow(self, ang_velocity: torch.Tensor):
        """Convert a yaw rate into a horizontal arrow pointing to the side the robot turns toward.

        It points to the robot's left for a left turn (positive yaw) and to its right for a right
        turn (negative yaw), with a length that grows with the turn rate. With base 0 the arrow
        vanishes when going straight, which reads as "no turn". Together with the forward linear
        arrow it forms an L, so the two are easy to tell apart.
        """
        default_scale = self.goal_ang_vel_visualizer.cfg.markers["arrow"].scale
        arrow_scale = torch.tensor(default_scale, device=self.device).repeat(ang_velocity.shape[0], 1)
        arrow_scale[:, 0] = self.cfg.ang_arrow_base + torch.abs(ang_velocity) * self.cfg.ang_arrow_gain
        # in the base frame: +90 deg about Z points to the robot's left (+Y) for a left turn,
        # -90 deg points to its right (-Y) for a right turn; then convert to the world frame
        side_angle = torch.where(ang_velocity >= 0.0, math.pi / 2.0, -math.pi / 2.0)
        zeros = torch.zeros_like(side_angle)
        arrow_quat = math_utils.quat_from_euler_xyz(zeros, zeros, side_angle)
        arrow_quat = math_utils.quat_mul(self.robot.data.root_quat_w, arrow_quat)
        return arrow_scale, arrow_quat


@configclass
class Kame32VelocityCommandCfg(UniformVelocityCommandCfg):
    """Configuration for :class:`Kame32VelocityCommand`."""

    class_type: type = Kame32VelocityCommand

    marker_height: float = 0.12
    """Height (m) at which the velocity markers float above the robot base."""

    # Arrow length = base + gain * magnitude (in marker scale units). Tweak these if the
    # arrows look too big or too small relative to the robot.
    lin_arrow_base: float = 0.35
    lin_arrow_gain: float = 1.5
    ang_arrow_base: float = 0.0  # 0 so the turn arrow vanishes when going straight
    ang_arrow_gain: float = 0.6

    goal_ang_vel_visualizer_cfg: VisualizationMarkersCfg = GREEN_ARROW_X_MARKER_CFG.replace(
        prim_path="/Visuals/Command/ang_vel_goal"
    )
    current_ang_vel_visualizer_cfg: VisualizationMarkersCfg = BLUE_ARROW_X_MARKER_CFG.replace(
        prim_path="/Visuals/Command/ang_vel_current"
    )

    def __post_init__(self):
        # the x component (length) is overwritten per-step from base + gain; y/z set the
        # arrow thickness. Sized to be clearly visible on a ~15 cm robot.
        self.goal_vel_visualizer_cfg.markers["arrow"].scale = (0.12, 0.12, 0.12)
        self.current_vel_visualizer_cfg.markers["arrow"].scale = (0.12, 0.12, 0.12)
        self.goal_ang_vel_visualizer_cfg.markers["arrow"].scale = (0.12, 0.12, 0.12)
        self.current_ang_vel_visualizer_cfg.markers["arrow"].scale = (0.12, 0.12, 0.12)
