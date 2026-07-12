"""
BounceGen Maya - Launcher
Module 01 of the Animator Workflow Toolkit.

To run: import BounceGen_Maya.launcher; BounceGen_Maya.launcher.launch()
or use the shelf button installed by install.py.
"""
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import maya.cmds as cmds
import bouncegen_ui


def launch():
    """Bootstraps sys.path and launches the BounceGen UI safely."""
    if cmds.about(batch=True):
        print("BounceGen Maya: batch mode detected, UI not launched.")
        return

    # Force-reload every module in this package so that reinstalling/editing
    # any of them (UI or Phase 2 logic) takes effect immediately, instead of
    # Python silently reusing whatever version was first imported earlier in
    # this Maya session. Order matters: reload leaf/dependency modules before
    # the modules that import them.
    import importlib
    import bouncegen_ball_types
    import bouncegen_physics
    import bouncegen_materials
    import bouncegen_scene
    import bouncegen_animation

    importlib.reload(bouncegen_ball_types)
    importlib.reload(bouncegen_physics)
    importlib.reload(bouncegen_materials)
    importlib.reload(bouncegen_scene)
    importlib.reload(bouncegen_animation)
    importlib.reload(bouncegen_ui)

    bouncegen_ui.launch()


if __name__ == "__main__":
    launch()
