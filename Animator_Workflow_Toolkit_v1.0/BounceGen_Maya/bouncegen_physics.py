"""BounceGen Maya - Physics Simulation Engine"""
import math
from dataclasses import dataclass
from typing import List, Dict, Any

GRAVITY = 9.81
FPS = 24.0
SETTLE_THRESHOLD = 0.01

@dataclass
class BounceEvent:
    event_index: int
    is_drop: bool
    apex_frame: float
    apex_height: float
    apex_h_pos: float
    impact_frame: float
    impact_height: float
    impact_h_pos: float
    impact_v_vertical: float
    impact_v_horizontal: float
    arc_duration_frames: float

REFERENCE_COR = 0.75  # "typical" bounciness used as the horizontal-speed reference


def _simulate_heights_and_air_times(start_height, e_eff, num_bounces):
    """Shared timing simulation used both for the real ball and for the
    reference-speed calculation below."""
    max_possible_bounces = max(num_bounces * 3, 50)
    heights, fall_times = [], []
    h_current = start_height
    for n in range(max_possible_bounces):
        heights.append(h_current)
        t_fall = math.sqrt(2.0 * h_current / GRAVITY) if h_current > 0 else 0.0
        fall_times.append(t_fall)
        if h_current < SETTLE_THRESHOLD and n >= num_bounces:
            break
        h_current = h_current * (e_eff ** 2)
        if e_eff == 0.0:
            break
    air_times = [fall_times[0]] + [2.0 * t for t in fall_times[1:]]
    return heights, air_times


def calculate_trajectory(params: Dict[str, Any]) -> List[BounceEvent]:
    start_height = max(0.0, params.get("start_height", 10.0))
    num_bounces = max(1, params.get("num_bounces", 5))
    # `cor` is the ball's FINAL, already-resolved coefficient of restitution
    # (the UI resolves per-ball-type COR vs. the Custom-type rebound override
    # before calling this function). It is used directly here with no extra
    # scaling - a ball with cor=1.0 now bounces back to its exact starting
    # height every time, instead of silently losing energy to a second,
    # hidden multiplier (the old "compounding" bug).
    cor = max(0.0, min(1.0, params.get("cor", 0.75)))
    horiz_dist = max(0.0, params.get("horiz_dist", 0.0))
    start_h_offset = params.get("start_h_offset", 0.0)
    radius = max(0.01, params.get("radius", 0.5))
    e_eff = cor

    if start_height <= 0.0:
        return [_create_resting_event(start_h_offset, radius)]

    heights, air_times = _simulate_heights_and_air_times(start_height, e_eff, num_bounces)
    num_events = len(heights)
    total_air_time = sum(air_times)

    # Horizontal speed is derived from a fixed REFERENCE bounciness (not this
    # ball's own COR), so that a livelier ball (more total air time than the
    # reference) travels FARTHER than horiz_dist, and a heavy/dead ball
    # (less total air time) falls SHORT of it - matching how real projectile
    # motion behaves, instead of forcing every ball to the same total
    # distance regardless of how bouncy it is.
    if horiz_dist > 0.0:
        ref_e_eff = REFERENCE_COR
        _, ref_air_times = _simulate_heights_and_air_times(start_height, ref_e_eff, num_bounces)
        ref_total_air_time = sum(ref_air_times)
        v_horiz = horiz_dist / ref_total_air_time if ref_total_air_time > 0 else 0.0
        horiz_distances = [v_horiz * t for t in air_times]
    else:
        v_horiz = 0.0
        horiz_distances = [0.0] * num_events

    events = []
    current_frame, current_h_pos = 1.0, start_h_offset
    
    for i in range(num_events):
        h, t_air, dx = heights[i], air_times[i], horiz_distances[i]
        v_vert_impact = math.sqrt(2.0 * GRAVITY * h) if h > 0 else 0.0
        v_horiz_i = dx / t_air if t_air > 0 else 0.0
        
        if i == 0:
            apex_frame, apex_h, apex_h_pos = current_frame, h, current_h_pos
            impact_frame, impact_h_pos = current_frame + (t_air * FPS), current_h_pos + dx
        else:
            apex_frame = current_frame + ((t_air / 2.0) * FPS)
            apex_h, apex_h_pos = h, current_h_pos + (dx / 2.0)
            impact_frame, impact_h_pos = current_frame + (t_air * FPS), current_h_pos + dx

        events.append(BounceEvent(
            event_index=i, is_drop=(i == 0),
            # +radius so the ball's SURFACE touches the grid at impact,
            # instead of its center (which was clipping half the ball
            # through the floor).
            apex_frame=round(apex_frame, 3), apex_height=round(apex_h + radius, 4), apex_h_pos=round(apex_h_pos, 4),
            impact_frame=round(impact_frame, 3), impact_height=round(radius, 4), impact_h_pos=round(impact_h_pos, 4),
            impact_v_vertical=round(v_vert_impact, 4), impact_v_horizontal=round(v_horiz_i, 4),
            arc_duration_frames=round(t_air * FPS, 3)
        ))
        current_frame, current_h_pos = impact_frame, impact_h_pos
    return events

def _create_resting_event(h_pos: float, radius: float) -> BounceEvent:
    return BounceEvent(0, True, 1.0, radius, h_pos, 1.0, radius, h_pos, 0.0, 0.0, 0.0)
