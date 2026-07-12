"""
BounceGen Maya - UI (Phase 2 Integrated)
"""
import maya.cmds as cmds

# Phase 2 Imports
import bouncegen_physics
import bouncegen_scene
import bouncegen_animation
import bouncegen_ball_types

class BounceGenUI(object):
    WINDOW_NAME = "BounceGenMayaWindow"
    BALL_TYPES = [
        "Ping Pong", "Tennis", "Golf", "Basketball", "Baseball",
        "Bowling", "Hockey Puck", "Steel Ball", "Glass Marble", "Custom",
    ]
    MATERIALS = ["Lambert", "Blinn", "Phong", "Metal", "Glass", "Rubber"]
    DEFAULT_H_SPACING = 3.0   # auto spacing between balls along the Arc Axis, no UI control needed
    MIN_BOUNCES = 1           # safety floor only - Rebound % fully governs how many bounces actually happen before settling

    def __init__(self):
        self.controls = {}
        self._has_generated = False

    def launch(self):
        # workspaceControl (rather than a plain cmds.window) makes the panel
        # dockable into Maya's UI like a native panel.
        if cmds.workspaceControl(self.WINDOW_NAME, exists=True):
            cmds.deleteUI(self.WINDOW_NAME)
        self._has_generated = False
        self.window = cmds.workspaceControl(
            self.WINDOW_NAME, label="Animator Workflow Toolkit — Module 01: BounceGen",
            retain=False, floating=True, initialWidth=340, initialHeight=680,
        )
        cmds.setParent(self.window)
        cmds.scrollLayout(childResizable=True)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4, columnAttach=("both", 6))
        self._build_header()
        self._build_controls()
        self._build_balls()
        self._build_actions()
        cmds.setParent("..")
        cmds.setParent("..")
        # Sync each ball row's visible state (Custom position row) with
        # whatever the option menus default to. Balls are NOT auto-created
        # here - the panel opens empty until Generate Bounce is clicked.
        for i in range(1, 6):
            b_type = cmds.optionMenu(self.controls["ball_{}_type".format(i)], q=True, value=True)
            self._set_custom_row_visible(i, b_type == "Custom")

    def _build_header(self):
        cmds.text(label="Animator Workflow Toolkit", font="boldLabelFont", align="center", height=20)
        cmds.text(label="Module 01: BounceGen", font="obliqueLabelFont", align="center", height=16)
        cmds.separator(height=4, style="none")
        cmds.rowLayout(numberOfColumns=5, columnWidth=[(1, 51), (2, 66), (3, 61), (4, 66), (5, 45)], columnAttach=[(1, "both", 1), (2, "both", 1), (3, "both", 1), (4, "both", 1), (5, "both", 1)])
        modules = [("WalkGen", 51), ("OverlapGen", 66), ("ArcAssist", 61), ("FollowThru", 66), ("Timing", 45)]
        for label, w in modules:
            cmds.button(label=label, enable=False, height=22, width=w, annotation="Coming soon")
        cmds.setParent("..")
        cmds.separator(height=6, style="in")

    def _build_controls(self):
        cmds.frameLayout(label="Controls", collapsable=False, marginWidth=3, marginHeight=3)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        LBL = [70, 40, 110]  # shared column widths so every slider in this section lines up, and stays narrow
        self.controls["start_height"] = cmds.floatSliderGrp(label="Start Height", field=True, minValue=0.5, maxValue=30, value=10.0, precision=2, columnWidth3=LBL, changeCommand=self._on_global_shape_changed, annotation="Drop height for every ball. Ignored by any ball set to 'Custom' type - those use their own Start Height instead.")
        self.controls["rebound_pct"] = cmds.floatSliderGrp(label="Rebound %", field=True, minValue=10, maxValue=100, value=80, precision=1, columnWidth3=LBL, changeCommand=self._on_global_shape_changed, annotation="Bounciness for Custom-type balls only (100% = lossless). Other types use their own built-in bounciness.")
        self.controls["horiz_dist"] = cmds.floatSliderGrp(label="Horiz. Dist.", field=True, minValue=0, maxValue=50, value=0, precision=2, columnWidth3=LBL, changeCommand=self._on_global_shape_changed, annotation="Reference travel distance. Livelier/bouncier balls will travel farther than this, heavy/dead balls will fall short of it.")
        self.controls["squash_stretch_amount"] = cmds.floatSliderGrp(label="Sq/Stretch", field=True, minValue=0, maxValue=2, value=0.25, precision=2, columnWidth3=LBL, changeCommand=self._on_global_shape_changed, annotation="Squash/Stretch intensity applied to any ball with its own Sq/St box checked (next to that ball's Radius slider). 1.0 = each ball type's natural amount, 0 = none, 2 = double.")
        cmds.separator(height=3, style="in")
        self.controls["arc_axis"] = cmds.radioButtonGrp(label="Arc Axis", labelArray2=["X Axis", "Z Axis"], numberOfRadioButtons=2, select=1, columnWidth3=[LBL[0], 82, 82], changeCommand=self._on_arc_axis_changed, annotation="Which world axis the horizontal travel happens along.")
        cmds.setParent("..")
        cmds.setParent("..")

    def _build_balls(self):
        cmds.frameLayout(label="Balls (1 to 5)", collapsable=True, collapse=False, marginWidth=3, marginHeight=2)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=3)

        # Master toggles - tick/untick a column for all 5 balls at once
        # instead of clicking each row individually. Same column widths as
        # each ball row's A/V checkboxes, so this reads as a header sitting
        # directly above them.
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 32), (2, 32)], columnAttach=[(1, "both", 1), (2, "both", 1)])
        self.controls["all_animate"] = cmds.checkBox(label="A", value=True, changeCommand=lambda val: self._toggle_all("animate", val), annotation="Toggle Animate for ALL balls at once.")
        self.controls["all_visible"] = cmds.checkBox(label="V", value=True, changeCommand=lambda val: self._toggle_all("visible", val), annotation="Toggle Visible for ALL balls at once.")
        cmds.setParent("..")
        cmds.separator(height=4, style="in")

        for i in range(1, 6): self._build_ball_row(i)
        cmds.setParent("..")
        cmds.setParent("..")

    def _build_ball_row(self, i):
        default_color = bouncegen_ball_types.get_ball_properties("Basketball").default_color

        # Row 1: A / V (no inline label - the master toggle row above is the
        # legend), ball label, Type, Material, Color swatch.
        cmds.rowLayout(numberOfColumns=6, columnWidth=[(1, 32), (2, 32), (3, 43), (4, 85), (5, 70), (6, 26)], columnAttach=[(1, "both", 1), (2, "both", 1), (3, "both", 1), (4, "both", 1), (5, "both", 1), (6, "both", 1)])
        self.controls["ball_{}_animate".format(i)] = cmds.checkBox(label="", value=True, changeCommand=lambda val, i=i: self._on_ball_animate_toggled(i, val), annotation="Animate: animate this ball's bounce trajectory. Unchecked: the ball is still created and visible, but stays still at its resting position.")
        self.controls["ball_{}_visible".format(i)] = cmds.checkBox(label="", value=True, changeCommand=lambda val, i=i: self._on_ball_visible_toggled(i, val), annotation="Visible: this ball's viewport visibility.")
        cmds.text(label="Ball {}".format(i))
        self.controls["ball_{}_type".format(i)] = cmds.optionMenu(label="", changeCommand=lambda val, i=i: self._on_ball_type_changed(i, val), annotation="Ball type - sets bounciness, default radius, and default color. Pick 'Custom' to unlock this ball's own SH (Start Height)/SP (Start Position) and Rebound % controls.")
        for btype in self.BALL_TYPES: cmds.menuItem(label=btype)
        cmds.optionMenu(self.controls["ball_{}_type".format(i)], edit=True, select=4)
        self.controls["ball_{}_material".format(i)] = cmds.optionMenu(label="", changeCommand=lambda val, i=i: self._on_ball_material_changed(i), annotation="Shader/material type applied to this ball.")
        for mat in self.MATERIALS: cmds.menuItem(label=mat)
        cmds.optionMenu(self.controls["ball_{}_material".format(i)], edit=True, select=6)
        self.controls["ball_{}_color".format(i)] = cmds.canvas(rgbValue=default_color, width=24, height=18, pressCommand=lambda i=i: self._pick_color(i), annotation="Click to choose this ball's color. Automatically set from Ball Type, but you can override it here.")
        cmds.setParent("..")

        # Row 2: a blank spacer the same width as the A+V checkbox columns
        # above, so Radius lines up under "Ball N" instead of under the
        # checkboxes - then Radius (kept short so it doesn't crowd out
        # Sq/St), then this ball's own Sq/St opt-in checkbox.
        cmds.rowLayout(numberOfColumns=3, columnWidth=[(1, 64), (2, 185), (3, 45)], columnAttach=[(1, "both", 1), (2, "both", 1), (3, "both", 1)])
        cmds.text(label="")
        self.controls["ball_{}_radius".format(i)] = cmds.floatSliderGrp(label="Radius", field=True, minValue=0.05, maxValue=5, value=1.0, precision=2, columnWidth3=[45, 42, 110], changeCommand=lambda val, i=i: self._on_ball_radius_changed(i), annotation="Ball radius, used for sphere size only - has no effect on squash/stretch. Resizes live, no need to regenerate.")
        self.controls["ball_{}_squash_stretch".format(i)] = cmds.checkBox(label="Sq/St", value=False, changeCommand=lambda val, i=i: self._on_ball_squash_stretch_toggled(i, val), annotation="Apply the Squash/Stretch amount (set under Controls) to this ball. Unchecked = perfectly rigid.")
        cmds.setParent("..")

        # Row 3: Custom-only SH (Start Height) + SP (Start Position). Hidden
        # unless this ball's Type is "Custom" - so it never affects the
        # natural-physics balls, but a Custom ball gets full, independent,
        # LIVE control over exactly where and how high it starts.
        row = cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 150), (2, 150)], columnAttach=[(1, "both", 1), (2, "both", 1)])
        self.controls["ball_{}_custom_row".format(i)] = row
        self.controls["ball_{}_custom_height".format(i)] = cmds.floatSliderGrp(label="SH", field=True, minValue=0, maxValue=30, value=10.0, precision=2, columnWidth3=[22, 42, 80], changeCommand=lambda val, i=i: self._on_custom_height_changed(i), annotation="Start Height - this Custom ball's own drop height, independent of the shared Start Height above. Updates live.")
        self.controls["ball_{}_custom_offset".format(i)] = cmds.floatSliderGrp(label="SP", field=True, minValue=-20, maxValue=20, value=(i - 1) * self.DEFAULT_H_SPACING, precision=2, columnWidth3=[22, 42, 80], changeCommand=lambda val, i=i: self._on_custom_offset_changed(i), annotation="Start Position - this Custom ball's own starting position along the Arc Axis, independent of the other balls. Negative values are allowed. Updates live, instantly - no regeneration needed.")
        cmds.setParent("..")

        cmds.separator(height=5, style="in")

    def _build_actions(self):
        cmds.button(label="Generate Bounce", height=30, backgroundColor=[0.3, 0.6, 0.3], command=self.generate_bounce, annotation="Builds the initial set of balls using the current settings. After that, every change in this panel applies live - you'll only need this again after Clear All Balls.")
        cmds.separator(height=4, style="none")
        cmds.button(label="Clear All Balls", height=28, command=self.clear_balls, annotation="Delete all BounceGen balls, shaders, and shading groups from the scene.")

    # ------------------------------------------------------------------
    # Row/state helpers
    # ------------------------------------------------------------------
    def _set_custom_row_visible(self, i, visible):
        cmds.rowLayout(self.controls["ball_{}_custom_row".format(i)], edit=True, manage=visible)

    def _ball_name(self, i):
        return "BounceBall_{}".format(i)

    def _current_arc_axis(self):
        return "X" if cmds.radioButtonGrp(self.controls["arc_axis"], q=True, select=True) == 1 else "Z"

    def _current_h_offset(self, i, b_type=None):
        if b_type is None:
            b_type = cmds.optionMenu(self.controls["ball_{}_type".format(i)], q=True, value=True)
        if b_type == "Custom":
            return cmds.floatSliderGrp(self.controls["ball_{}_custom_offset".format(i)], q=True, value=True)
        return (i - 1) * self.DEFAULT_H_SPACING

    # ------------------------------------------------------------------
    # Live-update tiers
    #
    # TIER 1 ("instant"): a direct setAttr on the existing ball/group -
    # color, material, visibility, radius, and a Custom ball's own Start
    # Position. None of these touch the group's transform in a way the
    # user didn't ask for, and none of them rebuild geometry or keyframes.
    #
    # TIER 2 ("recompute"): re-runs the physics + re-keys ONLY this ball's
    # own local translate/scale curves. The ball's parent group - which is
    # what actually carries its world position - is never touched, so
    # manual placement (by hand, or by Start Position) always survives a
    # Tier 2 recompute.
    #
    # Both tiers are no-ops until the first automatic generate_bounce() on
    # launch has actually created the balls.
    # ------------------------------------------------------------------
    def _refresh_ball_animation(self, i):
        if not self._has_generated: return
        ball_name = self._ball_name(i)
        if not cmds.objExists(ball_name): return
        animate = cmds.checkBox(self.controls["ball_{}_animate".format(i)], q=True, value=True)
        if not animate:
            bouncegen_animation.reset_to_rest(ball_name)
            return
        start_height = cmds.floatSliderGrp(self.controls["start_height"], q=True, value=True)
        rebound_pct = cmds.floatSliderGrp(self.controls["rebound_pct"], q=True, value=True)
        horiz_dist = cmds.floatSliderGrp(self.controls["horiz_dist"], q=True, value=True)
        arc_axis = self._current_arc_axis()
        ss_amount = cmds.floatSliderGrp(self.controls["squash_stretch_amount"], q=True, value=True)
        ss_enabled = cmds.checkBox(self.controls["ball_{}_squash_stretch".format(i)], q=True, value=True)
        b_type = cmds.optionMenu(self.controls["ball_{}_type".format(i)], q=True, value=True)
        radius = cmds.floatSliderGrp(self.controls["ball_{}_radius".format(i)], q=True, value=True)
        props = bouncegen_ball_types.get_ball_properties(b_type)
        is_custom = (b_type == "Custom")

        if is_custom:
            ball_start_height = cmds.floatSliderGrp(self.controls["ball_{}_custom_height".format(i)], q=True, value=True)
            cor = rebound_pct / 100.0
        else:
            ball_start_height = start_height
            cor = props.cor
        h_offset = self._current_h_offset(i, b_type)

        if ss_enabled:
            squash = props.default_squash * ss_amount
            stretch = props.default_stretch * ss_amount
        else:
            squash, stretch = 0.0, 0.0

        params = {
            "start_height": ball_start_height, "num_bounces": self.MIN_BOUNCES, "cor": cor,
            "horiz_dist": horiz_dist, "arc_axis": arc_axis,
            "start_h_offset": h_offset, "radius": radius,
        }
        trajectory = bouncegen_physics.calculate_trajectory(params)
        bouncegen_animation.animate_balls(ball_name, trajectory, arc_axis, radius, h_offset, squash, stretch)

    def _reposition_ball_group(self, i):
        """Used only for resets that legitimately need to move the group
        (Type change, Arc Axis change) - never for a plain Radius edit."""
        if not self._has_generated: return
        ball_name = self._ball_name(i)
        if not cmds.objExists(ball_name): return
        arc_axis = self._current_arc_axis()
        other_axis = "Z" if arc_axis == "X" else "X"
        radius = cmds.floatSliderGrp(self.controls["ball_{}_radius".format(i)], q=True, value=True)
        h_offset = self._current_h_offset(i)
        grp = bouncegen_scene.get_group(ball_name)
        if not grp: return
        cmds.setAttr("{}.translate{}".format(grp, arc_axis), h_offset)
        cmds.setAttr("{}.translate{}".format(grp, other_axis), 0.0)
        bouncegen_scene.set_group_rest_height(ball_name, radius)

    def _on_global_shape_changed(self, *args):
        """Start Height, Rebound %, Horizontal Distance, and the global
        Squash/Stretch amount all shape the arc itself, for every ball
        (Rebound % only actually changes Custom-type balls, but it's cheap
        and correct to just recompute all 5)."""
        for i in range(1, 6):
            self._refresh_ball_animation(i)

    def _on_arc_axis_changed(self, *args):
        for i in range(1, 6):
            self._reposition_ball_group(i)
            self._refresh_ball_animation(i)

    def _on_ball_animate_toggled(self, i, enabled):
        self._refresh_ball_animation(i)

    def _on_ball_visible_toggled(self, i, visible):
        if not self._has_generated: return
        bouncegen_scene.set_visibility(self._ball_name(i), visible)

    def _on_ball_radius_changed(self, i):
        if not self._has_generated: return
        radius = cmds.floatSliderGrp(self.controls["ball_{}_radius".format(i)], q=True, value=True)
        bouncegen_scene.resize_ball(self._ball_name(i), radius)

    def _on_ball_squash_stretch_toggled(self, i, enabled):
        self._refresh_ball_animation(i)

    def _on_ball_material_changed(self, i):
        if not self._has_generated: return
        color = cmds.canvas(self.controls["ball_{}_color".format(i)], q=True, rgbValue=True)
        material = cmds.optionMenu(self.controls["ball_{}_material".format(i)], q=True, value=True)
        bouncegen_scene.update_ball_material(self._ball_name(i), i, material, tuple(color))

    def _on_custom_height_changed(self, i):
        self._refresh_ball_animation(i)

    def _on_custom_offset_changed(self, i):
        if not self._has_generated: return
        offset = cmds.floatSliderGrp(self.controls["ball_{}_custom_offset".format(i)], q=True, value=True)
        arc_axis = self._current_arc_axis()
        bouncegen_scene.set_group_position(self._ball_name(i), offset, arc_axis)

    def _on_ball_type_changed(self, i, type_name):
        """Refresh this ball's radius/color to the new type's defaults,
        show/hide its dedicated Custom SH/SP row, and - if balls already
        exist - apply everything live: resize, recolor, reposition, and
        recompute its arc. This only fires when the user explicitly picks
        a new type, never as a side effect of anything else."""
        props = bouncegen_ball_types.get_ball_properties(type_name)
        cmds.floatSliderGrp(self.controls["ball_{}_radius".format(i)], edit=True, value=props.default_radius)
        cmds.canvas(self.controls["ball_{}_color".format(i)], edit=True, rgbValue=props.default_color)
        self._set_custom_row_visible(i, type_name == "Custom")
        if not self._has_generated: return
        ball_name = self._ball_name(i)
        bouncegen_scene.resize_ball(ball_name, props.default_radius)
        material = cmds.optionMenu(self.controls["ball_{}_material".format(i)], q=True, value=True)
        bouncegen_scene.update_ball_material(ball_name, i, material, props.default_color)
        self._reposition_ball_group(i)
        self._refresh_ball_animation(i)

    def _pick_color(self, i):
        canvas = self.controls["ball_{}_color".format(i)]
        current = cmds.canvas(canvas, q=True, rgbValue=True)
        cmds.colorEditor(rgbValue=current)
        if cmds.colorEditor(query=True, result=True):
            new_rgb = cmds.colorEditor(query=True, rgbValue=True)[:3]
            cmds.canvas(canvas, edit=True, rgbValue=new_rgb)
            self._on_ball_material_changed(i)

    def _toggle_all(self, column, value):
        for i in range(1, 6):
            cmds.checkBox(self.controls["ball_{}_{}".format(i, column)], edit=True, value=value)
            if column == "animate":
                self._on_ball_animate_toggled(i, value)
            else:
                self._on_ball_visible_toggled(i, value)

    # ------------------------------------------------------------------
    # Full (re)build - launch, and the two buttons only
    # ------------------------------------------------------------------
    def generate_bounce(self, *args, **kwargs):
        try:
            start_height = cmds.floatSliderGrp(self.controls["start_height"], q=True, value=True)
            rebound_pct = cmds.floatSliderGrp(self.controls["rebound_pct"], q=True, value=True)
            horiz_dist = cmds.floatSliderGrp(self.controls["horiz_dist"], q=True, value=True)
            arc_axis = self._current_arc_axis()
            ss_amount = cmds.floatSliderGrp(self.controls["squash_stretch_amount"], q=True, value=True)

            ball_configs = []
            for i in range(1, 6):
                animate = cmds.checkBox(self.controls["ball_{}_animate".format(i)], q=True, value=True)
                is_visible = cmds.checkBox(self.controls["ball_{}_visible".format(i)], q=True, value=True)
                ss_enabled = cmds.checkBox(self.controls["ball_{}_squash_stretch".format(i)], q=True, value=True)
                b_type = cmds.optionMenu(self.controls["ball_{}_type".format(i)], q=True, value=True)
                color = cmds.canvas(self.controls["ball_{}_color".format(i)], q=True, rgbValue=True)
                material = cmds.optionMenu(self.controls["ball_{}_material".format(i)], q=True, value=True)
                radius = cmds.floatSliderGrp(self.controls["ball_{}_radius".format(i)], q=True, value=True)

                props = bouncegen_ball_types.get_ball_properties(b_type)
                is_custom = (b_type == "Custom")

                if is_custom:
                    ball_start_height = cmds.floatSliderGrp(self.controls["ball_{}_custom_height".format(i)], q=True, value=True)
                    cor = rebound_pct / 100.0
                else:
                    ball_start_height = start_height
                    cor = props.cor
                h_offset = self._current_h_offset(i, b_type)

                if ss_enabled:
                    squash = props.default_squash * ss_amount
                    stretch = props.default_stretch * ss_amount
                else:
                    squash, stretch = 0.0, 0.0

                start_pos = (h_offset, radius, 0.0) if arc_axis == "X" else (0.0, radius, h_offset)
                ball_configs.append({
                    "index": i, "radius": radius, "color_rgb": tuple(color), "material_name": material,
                    "start_position": start_pos, "visible": is_visible, "animate": animate,
                    "cor": cor, "squash": squash, "stretch": stretch, "h_offset": h_offset,
                    "start_height": ball_start_height,
                })

            clear_failures = bouncegen_scene.clear_scene()
            if clear_failures:
                print("BounceGen: {} leftover node(s) could not be cleared before generating; new balls may look duplicated.".format(clear_failures))
            ball_names = bouncegen_scene.create_balls(ball_configs)

            for name, config in zip(ball_names, ball_configs):
                if not config["animate"]:
                    continue
                params = {
                    "start_height": config["start_height"], "num_bounces": self.MIN_BOUNCES, "cor": config["cor"],
                    "horiz_dist": horiz_dist, "arc_axis": arc_axis,
                    "start_h_offset": config["h_offset"], "radius": config["radius"],
                }
                trajectory = bouncegen_physics.calculate_trajectory(params)
                bouncegen_animation.animate_balls(name, trajectory, arc_axis, config["radius"], config["h_offset"], config["squash"], config["stretch"])

            self._has_generated = True
            try:
                cmds.inViewMessage(amg="<hl>BounceGen</hl>: generated.", pos='midCenterTop', fade=True, fadeStayTime=700, dragKill=True)
            except Exception:
                print("BounceGen: generated.")
        except Exception as e:
            import traceback
            cmds.confirmDialog(title="BounceGen Error", message="Error:\n\n{}".format(str(e)), button=["OK"], icon="critical")
            print(traceback.format_exc())

    def clear_balls(self, *args):
        try:
            failures = bouncegen_scene.clear_scene()
            self._has_generated = False
            if failures:
                cmds.confirmDialog(
                    title="BounceGen",
                    message="Cleared scene, but {} node(s) could not be deleted (see Script Editor).".format(failures),
                    button=["OK"], icon="warning",
                )
            else:
                try:
                    cmds.inViewMessage(amg="<hl>BounceGen</hl>: all balls cleared.", pos='midCenterTop', fade=True, fadeStayTime=700, dragKill=True)
                except Exception:
                    print("BounceGen: all balls cleared.")
        except Exception as e:
            import traceback
            cmds.confirmDialog(title="BounceGen Error", message="Error:\n\n{}".format(str(e)), button=["OK"], icon="critical")
            print(traceback.format_exc())

def launch():
    ui = BounceGenUI()
    ui.launch()
