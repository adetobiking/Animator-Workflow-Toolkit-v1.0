"""BounceGen Maya - Scene Generation & Management"""
import maya.cmds as cmds
from typing import List, Dict, Any
import bouncegen_materials


def _grp_name(idx) -> str:
    return "BounceBall_{}_grp".format(idx)


def create_balls(ball_configs: List[Dict[str, Any]]) -> List[str]:
    """Creates a GROUP + BALL pair for each ball:
      - BounceBall_{i}_grp: an empty transform placed at the ball's resting
        world position. This node is NEVER keyframed - it's a free,
        persistent anchor. Move it by hand in the viewport, or live via an
        interface slider (Start Position), and it stays exactly where put,
        with nothing to snap back to.
      - BounceBall_{i}: the sphere, parented under the group. Its bounce arc
        is keyframed in LOCAL space (relative to the group's rest
        position), so moving the group rigidly carries the whole
        performance with it, and regenerating the arc (a new Rebound %,
        Starting Height, etc.) never touches the group's transform.
    Returns the ball (sphere) transform names, in config order."""
    created_balls = []
    for config in ball_configs:
        idx = config.get("index", 1)
        radius = config.get("radius", 1.0)
        color_rgb = config.get("color_rgb", (0.8, 0.3, 0.1))
        mat_name = config.get("material_name", "Rubber")
        start_pos = config.get("start_position", (0.0, radius, 0.0))
        is_visible = config.get("visible", True)
        grp_name = _grp_name(idx)
        ball_name = "BounceBall_{}".format(idx)

        grp = cmds.group(empty=True, name=grp_name)
        cmds.xform(grp, translation=start_pos)
        # Y always represents this ball's resting height (its radius) and
        # scale is never used by this rig at the group level - both are
        # locked so they can't be accidentally moved/scaled by hand, which
        # was causing balls to sink below the grid or their arcs to distort.
        # X/Z stay free for repositioning.
        cmds.setAttr("{}.translateY".format(grp), lock=True)
        for ax in ("scaleX", "scaleY", "scaleZ"):
            cmds.setAttr("{}.{}".format(grp, ax), lock=True)

        # constructionHistory=True (unlike before) keeps a makeNurbSphere
        # history node around, so Radius can be resized live later with a
        # single setAttr instead of deleting/recreating the geometry.
        sphere_data = cmds.sphere(name=ball_name, radius=radius, sections=12, spans=8, constructionHistory=True)
        ball_transform = sphere_data[0]
        cmds.parent(ball_transform, grp)
        cmds.xform(ball_transform, translation=(0.0, 0.0, 0.0))

        sg_name = bouncegen_materials.create_material(mat_name, color_rgb, unique_id=idx)
        cmds.sets(ball_transform, forceElement=sg_name)
        cmds.setAttr("{}.visibility".format(grp), is_visible)
        created_balls.append(ball_transform)
    return created_balls


def clear_scene() -> int:
    """Deletes all BounceGen-created groups, balls, shaders, and shading
    groups. Never aborts partway through due to a single bad node. Returns
    the number of nodes that failed to delete (0 means fully clean)."""
    failures = 0
    patterns = ["BounceBall_*_grp", "BounceBall_*", "BounceGen_*_SG", "BounceGen_*_MAT"]
    nodes = []
    seen = set()
    for p in patterns:
        try:
            for n in (cmds.ls(p) or []):
                if n not in seen:
                    seen.add(n)
                    nodes.append(n)
        except Exception:
            pass

    for node in nodes:
        try:
            if not cmds.objExists(node):
                continue
            is_locked = False
            try:
                is_locked = bool(cmds.lockNode(node, query=True, lock=True)[0])
            except Exception:
                is_locked = False
            if is_locked:
                cmds.lockNode(node, lock=False)
            cmds.delete(node)
        except Exception as e:
            failures += 1
            print("BounceGen: could not delete '{}': {}".format(node, e))
    return failures


def _set_group_y(grp: str, value: float) -> None:
    """Internal: safely set the group's resting Y height. This channel is
    locked (see create_balls) to prevent accidental manual moves, so any
    legitimate programmatic update has to unlock, set, and relock it."""
    cmds.setAttr("{}.translateY".format(grp), lock=False)
    cmds.setAttr("{}.translateY".format(grp), value)
    cmds.setAttr("{}.translateY".format(grp), lock=True)


def set_group_rest_height(ball_name: str, new_height: float) -> None:
    """Public version of _set_group_y, keyed off the ball name - used by
    the UI layer (e.g. when Type or Arc Axis changes) instead of setting
    the locked group attribute directly."""
    grp = get_group(ball_name)
    if grp:
        _set_group_y(grp, new_height)


def get_group(ball_name: str):
    """Returns this ball's anchor group name, or None if it isn't parented
    under one (shouldn't normally happen, but callers should stay safe)."""
    if not cmds.objExists(ball_name):
        return None
    parents = cmds.listRelatives(ball_name, parent=True, fullPath=False) or []
    return parents[0] if parents else None


def set_group_position(ball_name: str, offset: float, axis: str) -> None:
    """Moves a ball's anchor group along the given world axis, LIVE, with
    no keyframe/geometry rebuild involved - this is exactly what lets
    Start Position take effect immediately, and never get clobbered by
    regenerating the ball's bounce arc later."""
    grp = get_group(ball_name)
    if not grp:
        return
    cmds.setAttr("{}.translate{}".format(grp, axis), offset)


def set_visibility(ball_name: str, visible: bool) -> None:
    grp = get_group(ball_name)
    target = grp if grp else ball_name
    if cmds.objExists(target):
        cmds.setAttr("{}.visibility".format(target), visible)


def resize_ball(ball_name: str, new_radius: float) -> None:
    """Live radius resize via the makeNurbSphere history node (geometry
    only), plus keeping the group's resting Y in sync - Y always has to
    equal the ball's radius for it to sit on the grid correctly, and no
    interface control ever offers Y as a free choice, so updating it here
    is a correction, not an override of anything the user set on purpose."""
    if not cmds.objExists(ball_name):
        return
    history = cmds.listHistory(ball_name) or []
    make_nodes = [n for n in history if cmds.nodeType(n) == "makeNurbSphere"]
    if make_nodes:
        cmds.setAttr("{}.radius".format(make_nodes[0]), new_radius)
    set_group_rest_height(ball_name, new_radius)


def update_ball_material(ball_name: str, idx, material_name: str, color_rgb) -> None:
    """Swaps this ball's own BounceGen shader/shading-group for a freshly
    built one - cheap, and touches nothing else (geometry, group transform,
    or keyframes are all left alone)."""
    if not cmds.objExists(ball_name):
        return
    old_sgs = set(cmds.listConnections(ball_name, type="shadingEngine") or [])
    sg_name = bouncegen_materials.create_material(material_name, color_rgb, unique_id=idx)
    cmds.sets(ball_name, forceElement=sg_name)
    for sg in old_sgs:
        if sg == sg_name or not sg.startswith("BounceGen_"):
            continue
        try:
            still_used = cmds.sets(sg, query=True) or []
        except Exception:
            still_used = None
        if not still_used:
            shaders = cmds.listConnections(sg + ".surfaceShader") or []
            try:
                cmds.delete(sg)
            except Exception:
                pass
            for s in shaders:
                try:
                    if cmds.objExists(s) and not (cmds.listConnections(s) or []):
                        cmds.delete(s)
                except Exception:
                    pass


def apply_visibility(ball_names: List[str], visibility_dict: Dict[str, bool]) -> None:
    for ball in ball_names:
        set_visibility(ball, visibility_dict.get(ball, True))
