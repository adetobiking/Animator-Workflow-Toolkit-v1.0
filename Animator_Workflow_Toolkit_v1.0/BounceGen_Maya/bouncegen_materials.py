"""BounceGen Maya - Material Creation"""
import maya.cmds as cmds
from typing import Tuple

def _is_arnold_available() -> bool:
    try: return cmds.pluginInfo('mtoa', query=True, loaded=True)
    except Exception: return False

def create_material(material_name: str, color_rgb: Tuple[float, float, float], unique_id: int = 1) -> str:
    safe_name = material_name.replace(" ", "_")
    mat_name = f"BounceGen_{safe_name}_{unique_id}_MAT"
    sg_name = f"BounceGen_{safe_name}_{unique_id}_SG"
    use_arnold = _is_arnold_available()
    mat_node = None
    
    if material_name == "Lambert":
        mat_node = cmds.shadingNode('lambert', asShader=True, name=mat_name)
        cmds.setAttr(f"{mat_node}.color", *color_rgb, type="double3")
    elif material_name == "Blinn":
        mat_node = cmds.shadingNode('blinn', asShader=True, name=mat_name)
        cmds.setAttr(f"{mat_node}.color", *color_rgb, type="double3")
    elif material_name == "Phong":
        mat_node = cmds.shadingNode('phong', asShader=True, name=mat_name)
        cmds.setAttr(f"{mat_node}.color", *color_rgb, type="double3")
    elif material_name in ["Metal", "Glass", "Rubber"]:
        if use_arnold:
            mat_node = cmds.shadingNode('aiStandardSurface', asShader=True, name=mat_name)
            cmds.setAttr(f"{mat_node}.baseColor", *color_rgb, type="double3")
            if material_name == "Metal":
                cmds.setAttr(f"{mat_node}.metalness", 1.0)
                cmds.setAttr(f"{mat_node}.specularRoughness", 0.1)
            elif material_name == "Glass":
                cmds.setAttr(f"{mat_node}.transmission", 0.9)
                cmds.setAttr(f"{mat_node}.opacity", 0.1, 0.1, 0.1, type="double3")
            elif material_name == "Rubber":
                cmds.setAttr(f"{mat_node}.specularRoughness", 0.8)
        else:
            if material_name == "Metal":
                # 'reflectivity' isn't rendered by Maya's default viewport
                # without raytracing, so it looked identical to plain Blinn.
                # A tight, bright specular highlight + a cool desaturated
                # tint reads as "metallic" under standard viewport lighting.
                mat_node = cmds.shadingNode('blinn', asShader=True, name=mat_name)
                tinted = tuple(min(1.0, c * 0.6 + 0.15) for c in color_rgb)
                cmds.setAttr(f"{mat_node}.color", *tinted, type="double3")
                cmds.setAttr(f"{mat_node}.specularColor", 0.95, 0.95, 0.95, type="double3")
                cmds.setAttr(f"{mat_node}.eccentricity", 0.05)
                cmds.setAttr(f"{mat_node}.reflectivity", 0.8)
            elif material_name == "Glass":
                mat_node = cmds.shadingNode('blinn', asShader=True, name=mat_name)
                cmds.setAttr(f"{mat_node}.color", *color_rgb, type="double3")
                cmds.setAttr(f"{mat_node}.transparency", 0.9, 0.9, 0.9, type="double3")
            elif material_name == "Rubber":
                # Plain lambert looked identical to the "Lambert" material
                # option (same node type, no visible distinction). Blinn with
                # a near-black specular color and wide eccentricity gives a
                # matte, dull-highlight "rubber" look that IS visible without
                # raytracing, while staying clearly different from Metal.
                mat_node = cmds.shadingNode('blinn', asShader=True, name=mat_name)
                darkened = tuple(c * 0.85 for c in color_rgb)
                cmds.setAttr(f"{mat_node}.color", *darkened, type="double3")
                cmds.setAttr(f"{mat_node}.specularColor", 0.05, 0.05, 0.05, type="double3")
                cmds.setAttr(f"{mat_node}.eccentricity", 0.9)
                
    if not mat_node:
        mat_node = cmds.shadingNode('lambert', asShader=True, name=mat_name)
        cmds.setAttr(f"{mat_node}.color", *color_rgb, type="double3")
        
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
    cmds.connectAttr(f"{mat_node}.outColor", f"{sg}.surfaceShader", force=True)
    return sg
