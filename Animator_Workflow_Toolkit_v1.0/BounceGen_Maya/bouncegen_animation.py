"""BounceGen Maya - Animation & Keyframing"""
import math
import maya.cmds as cmds
from typing import List
import bouncegen_physics

_ANIM_ATTRS = ('translateX', 'translateY', 'translateZ', 'scaleX', 'scaleY', 'scaleZ')


def clear_keys(ball_name: str) -> None:
    """Removes any existing translate/scale keyframes on the ball itself.
    Never touches its parent group - that's the whole point: regenerating
    a ball's bounce arc is safe to call as often as needed (every time a
    physics-affecting slider changes) without ever disturbing wherever the
    group has been placed, by hand or by Start Position."""
    for attr in _ANIM_ATTRS:
        try:
            if cmds.keyframe(ball_name, attribute=attr, query=True, keyframeCount=True):
                cmds.cutKey(ball_name, attribute=attr, clear=True)
        except Exception:
            pass


def reset_to_rest(ball_name: str) -> None:
    """Clears keys and puts the ball back at its parent group's origin -
    used when Animate gets unticked for a ball."""
    clear_keys(ball_name)
    try:
        cmds.setAttr(ball_name + '.translateX', 0.0)
        cmds.setAttr(ball_name + '.translateY', 0.0)
        cmds.setAttr(ball_name + '.translateZ', 0.0)
        cmds.setAttr(ball_name + '.scaleX', 1.0)
        cmds.setAttr(ball_name + '.scaleY', 1.0)
        cmds.setAttr(ball_name + '.scaleZ', 1.0)
    except Exception:
        pass


def animate_balls(ball_name: str, trajectory_data: List[bouncegen_physics.BounceEvent],
                  arc_axis: str, radius: float, start_h_offset: float,
                  default_squash: float, default_stretch: float) -> None:
    """Keys the ball's bounce arc in LOCAL space, relative to its parent
    group's rest position - subtracting `radius` from every height and
    `start_h_offset` from every horizontal position bakes the arc as a pure
    shape (independent of where the group actually sits). That's what lets
    the group be repositioned - by a slider, or by hand in the viewport -
    without ever fighting or being overwritten by these keyframes."""
    if not trajectory_data: return
    clear_keys(ball_name)
    _keyframe_translation(ball_name, trajectory_data, arc_axis, radius, start_h_offset)
    _keyframe_squash_stretch(ball_name, trajectory_data, default_squash, default_stretch)
    last_frame = trajectory_data[-1].impact_frame
    for attr in ('scaleX', 'scaleY', 'scaleZ'):
        cmds.setKeyframe(ball_name, attribute=attr, value=1.0, time=last_frame + 10, inTangentType='flat', outTangentType='flat')


def _keyframe_translation(ball: str, events: List[bouncegen_physics.BounceEvent], axis: str, radius: float, start_h_offset: float) -> None:
    e0 = events[0]
    cmds.setKeyframe(ball, attribute='translateY', value=e0.apex_height - radius, time=e0.apex_frame)
    cmds.setKeyframe(ball, attribute='translate{}'.format(axis), value=e0.apex_h_pos - start_h_offset, time=e0.apex_frame)
    for i, e in enumerate(events):
        if i == 0:
            _key_parabolic_segment(ball, e.apex_frame, e.impact_frame, e.apex_h_pos, e.impact_h_pos, e.apex_height, e.impact_height, axis, False, radius, start_h_offset)
        else:
            prev_e = events[i-1]
            _key_parabolic_segment(ball, prev_e.impact_frame, e.apex_frame, prev_e.impact_h_pos, e.apex_h_pos, prev_e.impact_height, e.apex_height, axis, True, radius, start_h_offset)
            _key_parabolic_segment(ball, e.apex_frame, e.impact_frame, e.apex_h_pos, e.impact_h_pos, e.apex_height, e.impact_height, axis, False, radius, start_h_offset)

def _key_parabolic_segment(ball: str, f_start: float, f_end: float, x_start: float, x_end: float, y_start: float, y_end: float, axis: str, is_upward: bool, radius: float, start_h_offset: float) -> None:
    duration = f_end - f_start
    if duration <= 0: return
    for f in range(int(f_start), int(f_end) + 1):
        u = (f - f_start) / duration
        x_val = x_start + (x_end - x_start) * u
        y_val = y_start + (y_end - y_start) * (2*u - u*u if is_upward else u*u)
        cmds.setKeyframe(ball, attribute='translate{}'.format(axis), value=x_val - start_h_offset, time=f, outTangentType='linear')
        cmds.setKeyframe(ball, attribute='translateY', value=y_val - radius, time=f, outTangentType='linear')

def _set_scale_key(ball: str, frame: float, sy: float) -> None:
    sxz = 1.0 / math.sqrt(sy)
    for attr, val in [('scaleY', sy), ('scaleX', sxz), ('scaleZ', sxz)]:
        cmds.setKeyframe(ball, attribute=attr, value=val, time=frame, inTangentType='flat', outTangentType='flat')


def _keyframe_squash_stretch(ball: str, events: List[bouncegen_physics.BounceEvent], default_squash: float, default_stretch: float) -> None:
    """Follows the classic reference: neutral at apex, a brief stretch as
    the ball approaches the ground, squash exactly at impact, a brief
    stretch again as it leaves the ground, then back to neutral. Both
    stretch poses are kept tight to the ground (a small fraction of the
    gap to the neighboring apex) rather than spreading into the open part
    of the arc. A per-bounce decay is applied on top of the natural
    velocity-based falloff, so the effect visibly shrinks bounce over
    bounce even for lively balls whose early impacts would otherwise all
    hit the same clamp and look identical."""
    BOUNCE_DECAY = 0.82
    n = len(events)
    for i, e in enumerate(events):
        decay = BOUNCE_DECAY ** i
        v_impact = e.impact_v_vertical

        # Neutral at this event's apex.
        _set_scale_key(ball, e.apex_frame, 1.0)

        stretch_factor = min(1.0, v_impact * 0.05 * default_stretch) * decay
        sy_stretch = 1.0 + stretch_factor

        # Brief stretch shortly BEFORE impact, as the ball falls toward the
        # ground - kept close to the ground (at most 30% of the gap back to
        # the apex it fell from).
        gap_before = e.impact_frame - e.apex_frame
        if gap_before > 0:
            pre_frame = e.impact_frame - min(max(1.0, 0.12 * gap_before), gap_before * 0.3)
            _set_scale_key(ball, pre_frame, sy_stretch)

        # Squash exactly AT impact.
        squash_factor = min(0.8, v_impact * 0.05 * default_squash) * decay
        sy_impact = max(0.2, 1.0 - squash_factor)
        _set_scale_key(ball, e.impact_frame, sy_impact)

        # Brief stretch shortly AFTER impact, as the ball leaves the
        # ground - same tight-to-the-ground rule, using the gap to the
        # NEXT apex (or the final settle key for the very last bounce).
        next_apex_frame = events[i + 1].apex_frame if i + 1 < n else e.impact_frame + 10
        gap_after = next_apex_frame - e.impact_frame
        if gap_after > 0:
            post_frame = e.impact_frame + min(max(1.0, 0.12 * gap_after), gap_after * 0.3)
            _set_scale_key(ball, post_frame, sy_stretch)
