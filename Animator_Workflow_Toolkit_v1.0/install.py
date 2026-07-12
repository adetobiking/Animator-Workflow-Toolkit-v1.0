"""
BounceGen Maya - Install to Shelf
Module 01 of the Animator Workflow Toolkit.

Run this once in Maya's Script Editor (Python tab). It:
  1. Asks you to pick the BounceGen_Maya folder
  2. Verifies the 8 expected files
  3. Copies the folder to ~/Documents/maya/scripts/BounceGen_Maya/
     (Maya's shared, version-independent scripts folder)
  4. Creates a 'BounceGen' shelf tab with Launch and Uninstall buttons

After install, click the BounceGen shelf tab and click Launch.
"""
import os
import shutil
import sys

import maya.cmds as cmds
import maya.mel as mel


REQUIRED_FILES = [
    "__init__.py",
    "launcher.py",
    "bouncegen_ui.py",
    "bouncegen_ball_types.py",
    "bouncegen_physics.py",
    "bouncegen_animation.py",
    "bouncegen_materials.py",
    "bouncegen_scene.py",
]

SHELF_NAME = "BounceGen"
SCRIPTS_DIR = os.path.join(cmds.internalVar(userAppDir=True), "scripts")
INSTALL_DIR = os.path.join(SCRIPTS_DIR, "BounceGen_Maya")

# Path to this installer script itself, so it can be copied alongside the
# package. Without this, the Reinstall/Uninstall shelf buttons ("import
# install; ...") stop working the moment Maya is restarted, because
# install.py was never persisted anywhere on sys.path.
try:
    THIS_INSTALL_PY = os.path.abspath(__file__)
except NameError:
    THIS_INSTALL_PY = None


def _shelf_top():
    return mel.eval('$tmp=$gShelfTopLevel')


def _ensure_shelf_tab():
    """Create the BounceGen shelf tab if it doesn't exist, return its full path."""
    top = _shelf_top()
    if cmds.shelfLayout(SHELF_NAME, exists=True):
        # Query fullPathName WITHOUT parent (parent must be boolean when query=True)
        return cmds.shelfLayout(SHELF_NAME, query=True, fullPathName=True)
    return cmds.shelfLayout(SHELF_NAME, parent=top)


def _add_buttons_to_shelf(shelf):
    """Add Launch and Uninstall buttons to the shelf."""
    # Remove existing buttons first (idempotent)
    children = cmds.shelfLayout(shelf, query=True, childArray=True) or []
    for c in children:
        try:
            cmds.deleteUI(c)
        except Exception:
            pass

    # Set the shelf as the active parent so buttons are added to it
    cmds.setParent(shelf)

    cmds.shelfButton(
        label="Launch",
        command=(
            "try:\n"
            "    import BounceGen_Maya.launcher\n"
            "    BounceGen_Maya.launcher.launch()\n"
            "except ImportError:\n"
            "    import maya.cmds as _cmds\n"
            "    _cmds.confirmDialog(title='BounceGen', message='BounceGen Maya is not installed correctly. Please reinstall using install.py.', button=['OK'], icon='warning')\n"
        ),
        annotation="Open the BounceGen Maya window.",
        image="commandButton.png",
        style="iconOnly",
        imageOverlayLabel="GO",
        overlayLabelColor=(1.0, 1.0, 1.0),
        overlayLabelBackColor=(0.0, 0.0, 0.0, 0.75),
        sourceType="python",
    )
    cmds.shelfButton(
        label="Uninstall",
        command=(
            "import install, importlib; importlib.reload(install); "
            "install.uninstall_interactive()"
        ),
        annotation="Remove the BounceGen shelf tab and the installed scripts folder.",
        image="commandButton.png",
        style="iconOnly",
        imageOverlayLabel="DEL",
        overlayLabelColor=(1.0, 1.0, 1.0),
        overlayLabelBackColor=(0.5, 0.0, 0.0, 0.75),
        sourceType="python",
    )


def install(source_dir):
    """Copy BounceGen_Maya from source_dir to the user's scripts dir and create the shelf."""
    if not os.path.isdir(source_dir):
        cmds.confirmDialog(
            title="BounceGen Maya - Install",
            message="Source folder not found:" + chr(10) + source_dir,
            button=["OK"], icon="critical",
        )
        return False

    # Verify all required files exist
    missing = [f for f in REQUIRED_FILES if not os.path.isfile(os.path.join(source_dir, f))]
    if missing:
        cmds.confirmDialog(
            title="BounceGen Maya - Install",
            message="Missing files in source folder:" + chr(10) + chr(10) + chr(10).join(missing),
            button=["OK"], icon="critical",
        )
        return False

    # Guard against reinstalling FROM the already-installed copy: deleting
    # INSTALL_DIR first would then delete source_dir out from under us.
    same_dir = os.path.exists(INSTALL_DIR) and os.path.samefile(source_dir, INSTALL_DIR)

    if not same_dir:
        if os.path.exists(INSTALL_DIR):
            shutil.rmtree(INSTALL_DIR)
        shutil.copytree(source_dir, INSTALL_DIR)
        print("BounceGen Maya: copied to {}".format(INSTALL_DIR))
    else:
        print("BounceGen Maya: source is already the installed copy, skipping file copy.")

    # Persist this installer script itself so the Reinstall/Uninstall shelf
    # buttons ("import install; ...") keep working after Maya restarts.
    # __file__ is NOT defined when Maya sources a script via File > Source Script,
    # so we fall back to looking for install.py in the parent of source_dir.
    install_py_src = THIS_INSTALL_PY
    if not install_py_src or not os.path.isfile(install_py_src):
        # Try parent of the BounceGen_Maya folder the user selected
        candidate = os.path.join(os.path.dirname(source_dir), "install.py")
        if os.path.isfile(candidate):
            install_py_src = candidate
    if install_py_src and os.path.isfile(install_py_src):
        try:
            dest_install_py = os.path.join(SCRIPTS_DIR, "install.py")
            if os.path.abspath(install_py_src) != os.path.abspath(dest_install_py):
                shutil.copy2(install_py_src, dest_install_py)
                print("BounceGen Maya: copied install.py to {}".format(SCRIPTS_DIR))
        except Exception as e:
            print("BounceGen Maya: warning, could not persist install.py: {}".format(e))
    else:
        print("BounceGen Maya: WARNING - could not locate install.py to persist. Reinstall/Uninstall may not work after restart.")

    # Make sure the install path is on sys.path
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)

    # Create shelf tab and add buttons
    shelf = _ensure_shelf_tab()
    _add_buttons_to_shelf(shelf)

    # Select the BounceGen tab so it becomes the visible/active tab
    top = _shelf_top()
    try:
        cmds.shelfTabLayout(top, edit=True, selectTab=SHELF_NAME)
    except Exception:
        pass

    print("BounceGen Maya: shelf tab 'BounceGen' created with Launch / Uninstall.")

    install_msg = "BounceGen Maya is installed." + chr(10) + chr(10)
    install_msg += "Click the 'BounceGen' shelf tab and then 'Launch' to open the window." + chr(10) + chr(10)
    install_msg += "Installed at: " + INSTALL_DIR

    cmds.confirmDialog(
        title="BounceGen Maya - Installed",
        message=install_msg,
        button=["OK"], icon="information",
    )
    return True


def install_interactive():
    """Ask the user for the source folder, then install."""
    result = cmds.fileDialog2(
        fileMode=3,
        caption="Select the BounceGen_Maya folder",
        okCaption="Install from this folder",
    )
    if not result:
        return
    install(result[0])


def _clear_bouncegen_scene():
    """Deletes any BounceGen-created balls/shaders/shading groups from the
    current scene. Duplicated here (rather than importing
    bouncegen_scene.clear_scene) on purpose - at uninstall time the
    BounceGen_Maya package folder may not be on sys.path yet (e.g. if the
    user never actually launched the tool this session), so this stays
    self-contained and always works."""
    patterns = ["BounceBall_*", "BounceGen_*_SG", "BounceGen_*_MAT"]
    nodes = []
    for p in patterns:
        try:
            nodes.extend(cmds.ls(p) or [])
        except Exception:
            pass
    removed = 0
    for node in nodes:
        try:
            if not cmds.objExists(node):
                continue
            try:
                if cmds.lockNode(node, query=True, lock=True)[0]:
                    cmds.lockNode(node, lock=False)
            except Exception:
                pass
            cmds.delete(node)
            removed += 1
        except Exception as e:
            print("BounceGen Maya: could not delete '{}' during uninstall: {}".format(node, e))
    return removed


def uninstall_interactive():
    """Confirm with the user, then remove the install."""
    uninst_msg = "Remove the BounceGen shelf tab, delete the installed folder, and clear any generated balls from the scene?" + chr(10) + chr(10)
    uninst_msg += "Path: " + INSTALL_DIR

    ans = cmds.confirmDialog(
        title="BounceGen Maya - Uninstall",
        message=uninst_msg,
        button=["Yes, uninstall", "Cancel"],
        defaultButton="Cancel", cancelButton="Cancel", icon="warning",
    )
    if ans != "Yes, uninstall":
        return

    # Close the live BounceGen window first, if it's open - otherwise it
    # keeps running (and its buttons keep calling into modules that are
    # about to be deleted from disk) until the user manually closes it.
    try:
        if cmds.workspaceControl("BounceGenMayaWindow", exists=True):
            cmds.deleteUI("BounceGenMayaWindow")
    except Exception as e:
        print("BounceGen Maya: warning, could not close the open window: {}".format(e))

    # Clear any balls/shaders BounceGen left in the scene, so uninstalling
    # doesn't leave orphaned geometry behind.
    removed = _clear_bouncegen_scene()
    if removed:
        print("BounceGen Maya: removed {} generated node(s) from the scene.".format(removed))

    top = _shelf_top()
    if cmds.shelfLayout(SHELF_NAME, exists=True):
        cmds.deleteUI(SHELF_NAME, layout=True)

    # Deleting the live UI is not enough: Maya auto-persists each shelf tab to
    # a .mel file in the user's prefs folder, and reloads every .mel file it
    # finds there on the next launch — which silently resurrects the shelf
    # (pointing at code that's about to be deleted) unless we remove that
    # file too.
    try:
        pref_dir = cmds.internalVar(userPrefDir=True)
        shelf_mel = os.path.join(pref_dir, "shelves", "shelf_{}.mel".format(SHELF_NAME))
        if os.path.isfile(shelf_mel):
            os.remove(shelf_mel)
            print("BounceGen Maya: removed persisted shelf file {}".format(shelf_mel))
    except Exception as e:
        print("BounceGen Maya: warning, could not remove persisted shelf file: {}".format(e))

    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR)

    print("BounceGen Maya: uninstalled.")
    cmds.confirmDialog(
        title="BounceGen Maya - Uninstalled",
        message="BounceGen Maya has been removed.",
        button=["OK"], icon="information",
    )


if __name__ == "__main__":
    install_interactive()
