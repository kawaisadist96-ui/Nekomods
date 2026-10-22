"""
PDX Script (.gfx / .asset) file generation for Clausewitz engine games.

Generates .gfx and .asset files alongside exported .mesh files,
using data from the Blender scene (materials, textures, locators).

author : stnh-mesh-IO contributors
"""

import math
import os

import bpy  # type: ignore
from mathutils import Quaternion  # type: ignore

from .. import IO_PDX_LOG
from .blender_import_export import (
    get_locators_info,
    get_material_shader,
    get_material_textures,
    get_mesh_index,
    list_scene_pdx_meshes,
)


class PDXScriptWriter:
    """Simple text builder for PDX Script syntax (tab-indented key=value blocks)."""

    def __init__(self):
        self._lines = []
        self._indent = 0

    def line(self, text):
        self._lines.append("\t" * self._indent + text)
        return self

    def open_block(self, key):
        self._lines.append("\t" * self._indent + key + " = {")
        self._indent += 1
        return self

    def close_block(self):
        self._indent = max(0, self._indent - 1)
        self._lines.append("\t" * self._indent + "}")
        return self

    def keyvalue(self, key, value):
        if isinstance(value, str):
            formatted = '"{}"'.format(value)
        elif isinstance(value, float):
            # strip trailing zeros but keep at least one decimal (1.0, not 1)
            formatted = "{:.6f}".format(value).rstrip("0")
            if formatted.endswith("."):
                formatted += "0"
        elif isinstance(value, int):
            formatted = str(value)
        else:
            formatted = str(value)
        self._lines.append("\t" * self._indent + "{} = {}".format(key, formatted))
        return self

    def inline_list(self, key, values):
        def _fmt(v):
            if isinstance(v, float):
                s = "{:.6f}".format(v).rstrip("0")
                return s + "0" if s.endswith(".") else s
            return str(v)
        parts = " ".join(_fmt(v) for v in values)
        self._lines.append("\t" * self._indent + "{} = {{ {} }}".format(key, parts))
        return self

    def comment(self, text):
        self._lines.append("\t" * self._indent + "# " + text)
        return self

    def blank(self):
        self._lines.append("")
        return self

    def get_text(self):
        return "\n".join(self._lines) + "\n"


def auto_detect_gfx_prefix(meshpath):
    """Extract relative gfx/ path from the mesh export path.

    Example: "D:/mods/stnh/gfx/models/ships/andorian_01/ship.mesh"
           -> "gfx/models/ships/andorian_01/"
    """
    normalized = meshpath.replace("\\", "/")
    idx = normalized.lower().find("/gfx/")
    if idx >= 0:
        # take everything from "gfx/" up to and including the last directory separator
        # force lowercase "gfx" prefix to match engine expectations
        rel = "gfx" + normalized[idx + 4:]  # "gfx/models/ships/andorian_01/ship.mesh"
        last_slash = rel.rfind("/")
        if last_slash >= 0:
            return rel[: last_slash + 1]  # "gfx/models/ships/andorian_01/"
    return ""


def _get_scene_empties(exp_selected):
    """Return empties (locator candidates) from the scene, optionally filtered by selection."""
    if exp_selected:
        return [obj for obj in bpy.context.selected_objects if obj.type == "EMPTY"]
    return [obj for obj in bpy.context.scene.objects if obj.type == "EMPTY"]


def generate_gfx_file(meshpath, pdxmesh_name, scale, gfx_path_prefix, exp_selected):
    """Generate a .gfx file next to the .mesh file.

    Returns the output path on success, or None if no meshes found.
    """
    mesh_objects = list_scene_pdx_meshes()
    if exp_selected:
        selected_names = {obj.name for obj in bpy.context.selected_objects}
        mesh_objects = [obj for obj in mesh_objects if obj.name in selected_names]

    if not mesh_objects:
        IO_PDX_LOG.warning("No PDX meshes found for .gfx export")
        return None

    mesh_objects.sort(key=lambda obj: get_mesh_index(obj.data))

    mesh_filename = os.path.basename(meshpath)
    file_path = gfx_path_prefix + mesh_filename
    # normalize to forward slashes
    file_path = file_path.replace("\\", "/")

    w = PDXScriptWriter()
    w.open_block("objectTypes")
    w.blank()
    w.open_block("pdxmesh")
    w.keyvalue("name", pdxmesh_name)
    w.keyvalue("file", file_path)
    w.keyvalue("scale", scale)

    for obj in mesh_objects:
        for slot_idx, slot in enumerate(obj.material_slots):
            mat = slot.material
            if mat is None:
                continue
            shader = get_material_shader(mat)
            if shader is None:
                continue

            w.blank()
            w.open_block("meshsettings")

            # submesh name: use material name to distinguish multi-material meshes
            submesh_name = mat.name if len(obj.material_slots) > 1 else obj.name
            w.keyvalue("name", submesh_name)
            w.keyvalue("index", get_mesh_index(obj.data))

            # textures
            try:
                tex_dict = get_material_textures(mat)
                tex_map = {"diff": "texture_diffuse", "n": "texture_normal", "spec": "texture_specular"}
                for pdx_slot, gfx_key in tex_map.items():
                    if pdx_slot in tex_dict:
                        tex_path = tex_dict[pdx_slot]
                        # use just the filename
                        tex_name = os.path.basename(tex_path)
                        w.keyvalue(gfx_key, tex_name)
            except Exception as err:
                IO_PDX_LOG.warning("Could not read textures for material {}: {}".format(mat.name, err))

            w.keyvalue("shader", shader)
            w.close_block()

    w.close_block()  # pdxmesh
    w.blank()
    w.close_block()  # objectTypes

    # write file
    gfx_outpath = os.path.splitext(meshpath)[0] + ".gfx"
    with open(gfx_outpath, "w", encoding="utf-8-sig") as f:
        f.write(w.get_text())

    IO_PDX_LOG.info("Exported .gfx file: {}".format(gfx_outpath))
    return gfx_outpath


def generate_asset_file(meshpath, entity_name, pdxmesh_name, scale, exp_selected):
    """Generate a .asset file next to the .mesh file.

    Returns the output path on success, or None if nothing to write.
    """
    empties = _get_scene_empties(exp_selected)
    locator_list = get_locators_info(empties) if empties else []

    w = PDXScriptWriter()
    w.open_block("entity")
    w.keyvalue("name", entity_name)
    w.keyvalue("pdxmesh", pdxmesh_name)
    w.keyvalue("scale", scale)

    for loc in locator_list:
        w.blank()
        w.open_block("locator")
        w.keyvalue("name", loc["name"])

        # position
        pos = loc.get("p", [0.0, 0.0, 0.0])
        w.inline_list("position", [round(v, 6) for v in pos])

        # rotation: convert quaternion (xyzw) to Euler degrees
        q_xyzw = loc.get("q", [0.0, 0.0, 0.0, 1.0])
        quat = Quaternion((q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]))  # Quaternion expects wxyz
        euler = quat.to_euler("XYZ")
        rot_deg = [round(math.degrees(euler.x), 6), round(math.degrees(euler.y), 6), round(math.degrees(euler.z), 6)]
        w.inline_list("rotation", rot_deg)

        w.close_block()

    # state template as comments
    w.blank()
    w.comment('--- Template: Animation States (uncomment and adjust as needed) ---')
    w.comment('default_state = "idle"')
    w.comment('state = { name = "idle"    animation = "idle" animation_blend_time = 4')
    w.comment('\tstart_event = { trigger_once = yes sound = { soundeffect = "amb_wrecked_shipyard_idle" } }')
    w.comment('}')
    w.comment('state = { name = "moving"  animation = "idle" animation_blend_time = 2')
    w.comment('\tevent = { trigger_once = yes sound = { soundeffect = moving_out_corvette } }')
    w.comment('}')
    w.comment('state = { name = "death" animation = "death2" animation_blend_time = 0.0 chance = 1 looping = no')
    w.comment('\tevent = { time = 0.0 node = "root" particle = "ship_explosion_particle" sound = { soundeffect = ship_destroyed } }')
    w.comment('}')
    w.comment('')
    w.comment('game_data = {')
    w.comment('\tsize = 2.5')
    w.comment('}')

    w.close_block()  # entity

    # write file
    asset_outpath = os.path.splitext(meshpath)[0] + ".asset"
    with open(asset_outpath, "w", encoding="utf-8-sig") as f:
        f.write(w.get_text())

    IO_PDX_LOG.info("Exported .asset file: {}".format(asset_outpath))
    return asset_outpath
