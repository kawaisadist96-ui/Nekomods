"""
Paradox asset files, Blender import/export interface.

Based on io_pdx_mesh by ross-g. STNH fork by the STNH Team.
"""

import importlib
import os
from textwrap import wrap

import bpy  # type: ignore
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty  # type: ignore
from bpy.types import Operator, Panel, UIList  # type: ignore
from bpy_extras.io_utils import ExportHelper, ImportHelper  # type: ignore

from .. import ENGINE_SETTINGS, IO_PDX_INFO, IO_PDX_LOG, IO_PDX_SETTINGS
from ..pdx_data import PDXData
from ..updater import github

try:
    from . import blender_import_export

    importlib.reload(blender_import_export)
    from .blender_import_export import (
        PDX_DIFFUSE,
        PDX_MESHINDEX,
        PDX_NORMAL,
        PDX_SHADER,
        PDX_SPECULAR,
        build_material_nodes,
        create_shader,
        export_animfile,
        export_meshfile,
        get_material_textures,
        get_mesh_index,
        import_animfile,
        import_meshfile,
        list_scene_pdx_meshes,
        set_ignore_joints,
        set_local_axis_display,
    )
except Exception as err:
    IO_PDX_LOG.error(err)
    raise


""" ====================================================================================================================
    Variables and Helper functions.
========================================================================================================================
"""


def get_material_list(self, context):
    sel_engine = context.scene.io_pdx_settings.setup_engine

    material_list = [(material, material, material) for material in ENGINE_SETTINGS[sel_engine]["material"]]
    material_list.insert(0, ("__NONE__", "", ""))

    return material_list


def get_scene_material_list(self, context):
    material_list = [(mat.name, mat.name, mat.name) for mat in bpy.data.materials if mat.get(PDX_SHADER, None)]

    return material_list


def set_engine(self, context):
    sel_engine = context.scene.io_pdx_settings.setup_engine
    IO_PDX_SETTINGS.last_set_engine = sel_engine
    IO_PDX_LOG.info("Set game engine to: '{}'".format(sel_engine))


""" ====================================================================================================================
    Operator classes called by the tool UI.
========================================================================================================================
"""


class IOPDX_OT_popup_message(Operator):
    bl_idname = "io_pdx_mesh.popup_message"
    bl_label = IO_PDX_INFO["name"]
    bl_description = "Popup Message"
    bl_options = {"REGISTER"}
    # fmt:off
    msg_text: StringProperty(
        default="NOT YET IMPLEMENTED!",
    )
    msg_icon: StringProperty(
        default="ERROR",  # options are - "ERROR", "QUESTION", "CANCEL", "INFO"
    )
    msg_width: IntProperty(
        default=300,
    )
    # fmt:on

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=self.msg_width)

    def draw(self, context):
        self.layout.operator_context = "INVOKE_DEFAULT"

        # split text into multiple label rows if it's wider than the panel
        txt_lines = []
        for line in self.msg_text.splitlines():
            txt_lines.extend(wrap(line, self.msg_width // 6))
            txt_lines.append("")

        col = self.layout.column(align=True)
        col.label(text=txt_lines[0], icon=self.msg_icon)
        for line in txt_lines[1:]:
            if line:
                col.label(text=line)
            else:
                col.separator()

        col.label(text="")


class material_popup(object):
    bl_options = {"REGISTER"}
    # fmt:off
    mat_name: StringProperty(
        name="Material name",
        default="",
    )
    mat_type: EnumProperty(
        name="Material type",
        items=get_material_list,
    )
    use_custom: BoolProperty(
        name="Custom type:",
        default=False,
    )
    custom_type: StringProperty(
        name="Shader",
        default="",
    )
    apply_mat: BoolProperty(
        name="Apply material to selected?",
        default=False,
    )
    diffuse_tex: StringProperty(
        name="Diffuse (.dds)",
        subtype="FILE_PATH",
        default="",
    )
    normal_tex: StringProperty(
        name="Normal (.dds)",
        subtype="FILE_PATH",
        default="",
    )
    specular_tex: StringProperty(
        name="Specular (.dds)",
        subtype="FILE_PATH",
        default="",
    )
    # fmt:on


class IOPDX_OT_material_create_popup(material_popup, Operator):
    bl_idname = "io_pdx_mesh.material_create_popup"
    bl_description = bl_label = "Create a PDX material"

    def check(self, context):
        return True

    def execute(self, context):
        mat_name = self.mat_name
        mat_type = self.mat_type
        if self.use_custom or mat_type == "__NONE__":
            mat_type = self.custom_type

        # collect any supplied texture paths (resolved to absolute)
        tex_attrs = {}
        if self.diffuse_tex:
            tex_attrs["diff"] = [bpy.path.abspath(self.diffuse_tex)]
        if self.specular_tex:
            tex_attrs["spec"] = [bpy.path.abspath(self.specular_tex)]
        if self.normal_tex:
            tex_attrs["n"] = [bpy.path.abspath(self.normal_tex)]

        # create a mock PDXData object for convenience here to pass to the create_shader function
        mat_dict = {"shader": [mat_type]}
        mat_dict.update(tex_attrs)
        mat_pdx = type("Material", (PDXData, object), mat_dict)

        # if any textures were given, build the full graph; otherwise an empty template
        template_only = not tex_attrs
        shader = create_shader(mat_pdx, mat_name, "", template_only=template_only)
        IO_PDX_LOG.info("Created material: {0} ({1})".format(mat_name, mat_type))
        if self.apply_mat:
            selected_objs = [obj for obj in context.selected_objects if isinstance(obj.data, bpy.types.Mesh)]
            for obj in selected_objs:
                # for each selected mesh, append the new material
                obj.data.materials.append(shader)
                IO_PDX_LOG.info("Applied material: {0} to object: {1}".format(shader.name, obj.name))
        return {"FINISHED"}

    def invoke(self, context, event):
        self.mat_name = ""
        # Default to PdxMeshShip when the active engine offers it (correct ship
        # shader); otherwise fall back to no preset.
        preferred = "PdxMeshShip"
        engine = context.scene.io_pdx_settings.setup_engine
        available = ENGINE_SETTINGS[engine]["material"]
        self.mat_type = preferred if preferred in available else "__NONE__"
        self.use_custom = False
        self.custom_type = ""
        self.diffuse_tex = ""
        self.normal_tex = ""
        self.specular_tex = ""
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        box = self.layout.box()
        box.prop(self, "mat_name")
        mat_type = box.row()
        mat_type.prop(self, "mat_type")
        split = box.split(factor=0.3)
        col1, col2 = split.column(), split.column()
        col1.prop(self, "use_custom")
        col2.prop(self, "custom_type", text="")
        col2.enabled = False
        if self.use_custom:
            mat_type.enabled = False
            col2.enabled = True

        self.layout.separator()
        tex_box = self.layout.box()
        tex_box.label(text="Textures (.dds):")
        tex_box.prop(self, "diffuse_tex")
        tex_box.prop(self, "normal_tex")
        tex_box.prop(self, "specular_tex")

        self.layout.separator()
        apply = self.layout.row()
        apply.prop(self, "apply_mat")
        self.layout.separator()


class IOPDX_OT_material_edit_popup(material_popup, Operator):
    bl_idname = "io_pdx_mesh.material_edit_popup"
    bl_description = bl_label = "Edit a PDX material"

    def _load_textures(self, mat, curr_mat):
        tex = {}
        try:
            tex = get_material_textures(mat)
        except RuntimeError as err:
            IO_PDX_LOG.warning(str(err))
        curr_mat.diffuse_tex = tex.get("diff", "")
        curr_mat.normal_tex = tex.get("n", "")
        curr_mat.specular_tex = tex.get("spec", "")

    def mat_select(self, context):
        mat = bpy.data.materials[self.scene_mats]
        curr_mat = context.scene.io_pdx_material
        curr_mat.mat_name = mat.name
        curr_mat.mat_type = mat.get(PDX_SHADER, "")
        self._load_textures(mat, curr_mat)

    # fmt:off
    scene_mats: EnumProperty(
        name="Selected material",
        items=get_scene_material_list,
        update=mat_select,
    )
    # fmt:on

    def check(self, context):
        return True

    def execute(self, context):
        mat = bpy.data.materials[self.scene_mats]
        curr_mat = context.scene.io_pdx_material
        mat.name = curr_mat.mat_name
        mat[PDX_SHADER] = curr_mat.mat_type

        # assemble texture attrs from the (possibly edited) dialog fields
        tex_attrs = {"shader": [curr_mat.mat_type]}
        if curr_mat.diffuse_tex:
            tex_attrs["diff"] = [bpy.path.abspath(curr_mat.diffuse_tex)]
        if curr_mat.specular_tex:
            tex_attrs["spec"] = [bpy.path.abspath(curr_mat.specular_tex)]
        if curr_mat.normal_tex:
            tex_attrs["n"] = [bpy.path.abspath(curr_mat.normal_tex)]
        mat_pdx = type("Material", (PDXData, object), tex_attrs)

        # store / clear the texture filenames as custom properties so the export
        # reads them deterministically (matching what create_shader does on import)
        for pdx_attr, prop_key in (("diff", PDX_DIFFUSE), ("n", PDX_NORMAL), ("spec", PDX_SPECULAR)):
            if pdx_attr in tex_attrs:
                mat[prop_key] = os.path.basename(tex_attrs[pdx_attr][0])
            elif prop_key in mat:
                del mat[prop_key]

        # rebuild the node tree in place; name + fake_user + mesh assignment are
        # properties of the material datablock and are preserved
        mat.use_nodes = True
        template_only = not any(k in tex_attrs for k in ("diff", "spec", "n"))
        build_material_nodes(mat, mat_pdx, "", template_only=template_only)

        IO_PDX_LOG.info("Edited material: {0} ({1})".format(curr_mat.mat_name, curr_mat.mat_type))
        return {"FINISHED"}

    def invoke(self, context, event):
        pdx_scene_materials = get_scene_material_list(self, context)
        if pdx_scene_materials:
            if self.scene_mats in bpy.data.materials:
                self.mat_select(context)
                mat = bpy.data.materials[self.scene_mats]
                self.mat_name = mat.name
                self.custom_type = mat.get(PDX_SHADER, "")
                return context.window_manager.invoke_props_dialog(self, width=400)
            else:
                return {"CANCELLED"}
        else:
            bpy.ops.io_pdx_mesh.popup_message("INVOKE_DEFAULT", msg_text="NO PDX MATERIALS FOUND IN THE SCENE!")
            return {"CANCELLED"}

    def draw(self, context):
        curr_mat = context.scene.io_pdx_material

        self.layout.prop(self, "scene_mats")
        self.layout.separator()

        box = self.layout.box()
        box.prop(curr_mat, "mat_name")
        box.prop(curr_mat, "mat_type")

        self.layout.separator()
        tex_box = self.layout.box()
        tex_box.label(text="Textures (.dds):")
        tex_box.prop(curr_mat, "diffuse_tex")
        tex_box.prop(curr_mat, "normal_tex")
        tex_box.prop(curr_mat, "specular_tex")
        self.layout.separator()


class IOPDX_UL_mesh_index_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False)


class IOPDX_OT_mesh_index_actions(Operator):
    bl_idname = "io_pdx_mesh.mesh_index_actions"
    bl_description = bl_label = "Mesh index list actions"
    bl_options = {"REGISTER"}
    # fmt:off
    action: EnumProperty(
        items=(("UP", "Up", ""), ("DOWN", "Down", "")),
    )
    # fmt:on

    @classmethod
    def poll(cls, context):
        return context.scene.io_pdx_group

    def move_index(self):
        list_index = bpy.context.scene.io_pdx_group.idx
        list_length = len(bpy.context.scene.io_pdx_group.coll) - 1

        new_index = list_index + (-1 if self.action == "UP" else 1)
        bpy.context.scene.io_pdx_group.idx = max(0, min(new_index, list_length))

    def execute(self, context):
        collection = context.scene.io_pdx_group.coll
        index = context.scene.io_pdx_group.idx
        neighbor = index + (-1 if self.action == "UP" else 1)
        collection.move(neighbor, index)
        self.move_index()

        return {"FINISHED"}


class IOPDX_OT_mesh_index_popup(Operator):
    bl_idname = "io_pdx_mesh.mesh_index_popup"
    bl_description = bl_label = "Set mesh index on PDX meshes"
    bl_options = {"REGISTER"}

    def check(self, context):
        return True

    def execute(self, context):
        for i, item in enumerate(context.scene.io_pdx_group.coll):
            item.ref.data[PDX_MESHINDEX] = i
        return {"FINISHED"}

    def invoke(self, context, event):
        obj_group = context.scene.io_pdx_group

        obj_group.coll.clear()
        pdx_scenemeshes = list_scene_pdx_meshes()
        pdx_scenemeshes.sort(key=lambda obj: get_mesh_index(obj.data))

        for obj in pdx_scenemeshes:
            item = obj_group.coll.add()
            item.name = obj.name
            item.ref = obj
        return context.window_manager.invoke_props_dialog(self, width=200)

    def draw(self, context):
        obj_group = context.scene.io_pdx_group
        row = self.layout.row()
        row.template_list("IOPDX_UL_mesh_index_list", "", obj_group, "coll", obj_group, "idx", rows=8)

        col = row.column(align=True)
        col.operator("io_pdx_mesh.mesh_index_actions", icon="TRIA_UP", text="").action = "UP"
        col.operator("io_pdx_mesh.mesh_index_actions", icon="TRIA_DOWN", text="").action = "DOWN"
        self.layout.separator()


class IOPDX_OT_import_mesh(Operator, ImportHelper):
    bl_idname = "io_pdx_mesh.import_mesh"
    bl_description = bl_label = "Import PDX mesh"
    bl_options = {"REGISTER", "UNDO"}

    # ImportHelper mixin class uses these
    filename_ext = ".mesh"
    # fmt:off
    filter_glob: StringProperty(
        default="*.mesh",
        options={"HIDDEN"},
        maxlen=255,
    )
    filepath: StringProperty(
        name="Import file Path",
        maxlen=1024,
    )
    chk_mesh: BoolProperty(
        name="Import mesh",
        description="Import mesh",
        default=True,
    )
    chk_skel: BoolProperty(
        name="Import skeleton",
        description="Import skeleton",
        default=True,
    )
    chk_locs: BoolProperty(
        name="Import locators",
        description="Import locators",
        default=True,
    )
    chk_joinmats: BoolProperty(
        name="Join materials",
        description="Join materials",
        default=True,
    )
    chk_bonespace: BoolProperty(
        name="Convert bone orientation - WARNING",
        description="Convert bone orientation - WARNING: this re-orients bones authored at source and will BREAK ALL "
                    "EXISTING ANIMATIONS. Only use this option if you are going to fully re-animate the model.",
        default=False,
    )
    # fmt:on

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Settings:", icon="IMPORT")
        box.prop(self, "chk_mesh")
        if self.chk_mesh:
            mesh_settings = box.box()
            split = mesh_settings.split(factor=0.1)
            _, col = split.column(), split.column()
            col.prop(self, "chk_joinmats")
        box.prop(self, "chk_skel")
        box.prop(self, "chk_locs")
        # box.prop(self, 'chk_bonespace')  # TODO: works but overcomplicates things, disabled for now

    def execute(self, context):
        try:
            import_meshfile(
                self.filepath,
                imp_mesh=self.chk_mesh,
                imp_skel=self.chk_skel,
                imp_locs=self.chk_locs,
                join_materials=self.chk_joinmats,
                bonespace=self.chk_bonespace,
            )
            self.report({"INFO"}, "[io_pdx_mesh] Finished importing {}".format(self.filepath))
            IO_PDX_SETTINGS.last_import_mesh = self.filepath

        except Exception as err:
            IO_PDX_LOG.warning("FAILED to import {0}".format(self.filepath))
            IO_PDX_LOG.error(err, exc_info=True)
            self.report({"WARNING"}, "Mesh import failed!")
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        return {"FINISHED"}

    def invoke(self, context, event):
        self.filepath = IO_PDX_SETTINGS.last_import_mesh or ""
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


class IOPDX_OT_import_anim(Operator, ImportHelper):
    bl_idname = "io_pdx_mesh.import_anim"
    bl_description = bl_label = "Import PDX animation"
    bl_options = {"REGISTER", "UNDO"}

    # ImportHelper mixin class uses these
    filename_ext = ".anim"
    # fmt:off
    filter_glob: StringProperty(
        default="*.anim",
        options={"HIDDEN"},
        maxlen=255,
    )
    filepath: StringProperty(
        name="Import file Path",
        maxlen=1024,
    )
    int_start: IntProperty(
        name="Start frame",
        description="Start frame",
        default=1,
    )
    # fmt:on

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Settings:", icon="IMPORT")
        box.prop(self, "int_start")

    def execute(self, context):
        try:
            import_animfile(self.filepath, frame_start=self.int_start)
            self.report({"INFO"}, "[io_pdx_mesh] Finished importing {}".format(self.filepath))
            IO_PDX_SETTINGS.last_import_anim = self.filepath

        except Exception as err:
            IO_PDX_LOG.warning("FAILED to import {0}".format(self.filepath))
            IO_PDX_LOG.error(err, exc_info=True)
            self.report({"WARNING"}, "Animation import failed!")
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        return {"FINISHED"}

    def invoke(self, context, event):
        self.filepath = IO_PDX_SETTINGS.last_import_anim or ""
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


class IOPDX_OT_export_mesh(Operator, ExportHelper):
    bl_idname = "io_pdx_mesh.export_mesh"
    bl_description = bl_label = "Export PDX mesh"
    bl_options = {"REGISTER", "UNDO"}

    # ExportHelper mixin class uses these
    filename_ext = ".mesh"
    # fmt:off
    filter_glob: StringProperty(
        default="*.mesh",
        options={"HIDDEN"},
        maxlen=255,
    )
    filepath: StringProperty(
        name="Export file Path",
        maxlen=1024,
    )
    chk_mesh: BoolProperty(
        name="Meshes",
        description="Export meshes",
        default=True,
    )
    chk_mesh_blendshape: BoolProperty(
        name="As blendshape",
        description="Export meshes as blendshapes",
        default=False,
    )
    chk_skel: BoolProperty(
        name="Skeleton",
        description="Export related armatures",
        default=True,
    )
    chk_locs: BoolProperty(
        name="Locators",
        description="Export empties data",
        default=True,
    )
    chk_selected: BoolProperty(
        name="Selected only",
        description="Filter export by selection",
        default=False,
    )
    chk_debug: BoolProperty(
        name="[debug options]",
        description="Non-standard options",
        default=False,
    )
    chk_split_vtx: BoolProperty(
        name="Split all vertices",
        description="Splits all vertices (per triangle) during export",
        default=False,
    )
    ddl_sort_vtx: EnumProperty(
        name="Sort vertices",
        description="Sort all vertex data by id during export",
        items=(
            ("+", "Incr", "Ascending id sort"),
            ("~", "Native", "Blender native order"),
            ("-", "Decr", "Descending id sort")
        ),
        default="+",
    )
    chk_plain_txt: BoolProperty(
        name="Also export plain text",
        description="Exports a plain text file along with binary",
        default=False,
    )
    chk_gfx: BoolProperty(
        name="Export .gfx",
        description="Generate a .gfx file alongside the .mesh",
        default=False,
    )
    chk_asset: BoolProperty(
        name="Export .asset",
        description="Generate an .asset file alongside the .mesh",
        default=False,
    )
    str_gfx_path_prefix: StringProperty(
        name="GFX path prefix",
        description="Relative path prefix for the mesh file reference in the .gfx (e.g. gfx/models/ships/faction/)",
        default="gfx/models/ships/",
    )
    str_pdxmesh_name: StringProperty(
        name="pdxmesh name",
        description="Name for the pdxmesh entry (leave empty for auto-name based on filename)",
        default="",
    )
    str_entity_name: StringProperty(
        name="Entity name",
        description="Name for the entity entry (leave empty for auto-name based on filename)",
        default="",
    )
    flt_gfx_scale: FloatProperty(
        name="Scale",
        description="Scale value written into .gfx and .asset files",
        default=1.0,
        min=0.001,
        max=100.0,
    )
    # fmt:on

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Settings:", icon="EXPORT")
        box.prop(self, "chk_mesh")
        if self.chk_mesh:
            mesh_settings = box.box()
            split = mesh_settings.split(factor=0.1)
            _, col = split.column(), split.column()
            col.prop(self, "chk_mesh_blendshape")
        box.prop(self, "chk_skel")
        box.prop(self, "chk_locs")
        box.prop(self, "chk_selected")
        box.prop(self, "chk_debug")
        if self.chk_debug:
            debug_settings = box.box()
            split = debug_settings.split(factor=0.1)
            _, col = split.column(), split.column()
            col.alignment = "RIGHT"
            col.prop(self, "chk_split_vtx")
            col.prop(self, "ddl_sort_vtx")
            col.prop(self, "chk_plain_txt")

        box = self.layout.box()
        box.label(text="PDX Script Files:", icon="TEXT")
        box.prop(self, "chk_gfx")
        box.prop(self, "chk_asset")
        if self.chk_gfx or self.chk_asset:
            script_settings = box.box()
            script_settings.prop(self, "str_gfx_path_prefix")
            script_settings.prop(self, "flt_gfx_scale")
            if self.chk_gfx:
                script_settings.prop(self, "str_pdxmesh_name")
            if self.chk_asset:
                script_settings.prop(self, "str_entity_name")

    def execute(self, context):
        try:
            export_meshfile(
                self.filepath,
                exp_mesh=self.chk_mesh,
                exp_skel=self.chk_skel,
                exp_locs=self.chk_locs,
                exp_selected=self.chk_selected,
                as_blendshape=self.chk_mesh_blendshape,
                debug_mode=self.chk_debug,
                split_verts=self.chk_split_vtx,
                sort_verts=self.ddl_sort_vtx,
                plain_txt=self.chk_plain_txt,
            )
            self.report({"INFO"}, "[io_pdx_mesh] Finished exporting {}".format(self.filepath))
            IO_PDX_SETTINGS.last_export_mesh = self.filepath

        except Exception as err:
            IO_PDX_LOG.warning("FAILED to export {0}".format(self.filepath))
            IO_PDX_LOG.error(err, exc_info=True)
            self.report({"WARNING"}, "Mesh export failed!")
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        # generate .gfx / .asset files if requested
        if self.chk_gfx or self.chk_asset:
            try:
                from .pdx_script_export import auto_detect_gfx_prefix, generate_asset_file, generate_gfx_file

                basename = os.path.splitext(os.path.basename(self.filepath))[0]
                pdxmesh_name = self.str_pdxmesh_name or (basename + "_mesh")
                entity_name = self.str_entity_name or (basename + "_entity")
                gfx_prefix = self.str_gfx_path_prefix or auto_detect_gfx_prefix(self.filepath)

                if self.chk_gfx:
                    gfx_out = generate_gfx_file(
                        self.filepath, pdxmesh_name, self.flt_gfx_scale, gfx_prefix, self.chk_selected,
                    )
                    if gfx_out:
                        self.report({"INFO"}, "[io_pdx_mesh] Exported {}".format(gfx_out))

                if self.chk_asset:
                    asset_out = generate_asset_file(
                        self.filepath, entity_name, pdxmesh_name, self.flt_gfx_scale, self.chk_selected,
                    )
                    if asset_out:
                        self.report({"INFO"}, "[io_pdx_mesh] Exported {}".format(asset_out))

            except Exception as err:
                IO_PDX_LOG.error(err, exc_info=True)
                self.report({"WARNING"}, "PDX script file export failed: {}".format(err))

        return {"FINISHED"}

    def invoke(self, context, event):
        self.filepath = IO_PDX_SETTINGS.last_export_mesh or ""

        # auto-detect gfx path prefix from last used export path
        if self.filepath and not self.str_gfx_path_prefix:
            from .pdx_script_export import auto_detect_gfx_prefix

            detected = auto_detect_gfx_prefix(self.filepath)
            if detected:
                self.str_gfx_path_prefix = detected

        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


class IOPDX_OT_export_anim(Operator, ExportHelper):
    bl_idname = "io_pdx_mesh.export_anim"
    bl_description = bl_label = "Export PDX animation"
    bl_options = {"REGISTER", "UNDO"}

    # ExportHelper mixin class uses these
    filename_ext = ".anim"
    # fmt:off
    filter_glob: StringProperty(
        default="*.anim",
        options={"HIDDEN"},
        maxlen=255,
    )
    filepath: StringProperty(
        name="Export file Path",
        maxlen=1024,
    )
    int_start: IntProperty(
        name="Start frame",
        description="Custom start frame",
        default=1,
    )
    int_end: IntProperty(
        name="End frame",
        description="Custom end frame",
        default=100,
    )
    chk_uniform_scale: BoolProperty(
        name="Uniform scale only",
        description="Exports only uniform scale animation data, newer games support non-uniformly scaled bones",
        default=True,
    )
    chk_debug: BoolProperty(
        name="[debug options]",
        description="Non-standard options",
        default=False,
    )
    chk_plain_txt: BoolProperty(
        name="Also export plain text",
        description="Exports a plain text file along with binary",
        default=False,
    )
    # fmt:on

    def draw(self, context):
        settings = context.scene.io_pdx_export

        box = self.layout.box()
        box.label(text="Settings:", icon="EXPORT")
        box.prop(settings, "custom_range")
        if settings.custom_range:
            range_settings = box.box()
            range_settings.use_property_split = True
            col = range_settings.column()
            col.prop(self, "int_start")
            col.prop(self, "int_end")
        box.prop(self, "chk_uniform_scale")
        box.prop(self, "chk_debug")
        if self.chk_debug:
            debug_settings = box.box()
            split = debug_settings.split(factor=0.1)
            _, col = split.column(), split.column()
            col.alignment = "RIGHT"
            col.prop(self, "chk_plain_txt")

    def execute(self, context):
        settings = context.scene.io_pdx_export

        try:
            if settings.custom_range:
                start, end = self.int_start, self.int_end
            else:
                start, end = context.scene.frame_start, context.scene.frame_end

            export_animfile(
                self.filepath,
                frame_start=start,
                frame_end=end,
                debug_mode=self.chk_debug,
                uniform_scale=self.chk_uniform_scale,
                plain_txt=self.chk_plain_txt,
            )

            self.report({"INFO"}, "[io_pdx_mesh] Finished exporting {}".format(self.filepath))
            IO_PDX_SETTINGS.last_export_anim = self.filepath

        except Exception as err:
            IO_PDX_LOG.warning("FAILED to export {0}".format(self.filepath))
            IO_PDX_LOG.error(err, exc_info=True)
            self.report({"WARNING"}, "Animation export failed!")
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        return {"FINISHED"}

    def invoke(self, context, event):
        self.filepath = IO_PDX_SETTINGS.last_export_anim or ""
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


class IOPDX_OT_show_axis(Operator):
    bl_idname = "io_pdx_mesh.show_axis"
    bl_description = bl_label = "Show / hide local axis"
    bl_options = {"REGISTER"}

    # fmt:off
    show: BoolProperty(
        default=True,
    )
    data_type: EnumProperty(
        name="Data type",
        items=(
            ("EMPTY", "Empty", "Empty", 1),
            ("ARMATURE", "Armature", "Armature", 2)
        ),
    )
    # fmt:on

    def execute(self, context):
        set_local_axis_display(self.show, self.data_type)
        return {"FINISHED"}


class IOPDX_OT_ignore_bone(Operator):
    bl_idname = "io_pdx_mesh.ignore_bone"
    bl_description = bl_label = "Ignore / Unignore selected bones"
    bl_options = {"REGISTER"}

    # fmt:off
    state: BoolProperty(
        default=False,
    )
    # fmt:on

    def execute(self, context):
        set_ignore_joints(self.state)
        return {"FINISHED"}


""" ====================================================================================================================
    UI classes for the import/export tool.
========================================================================================================================
"""


class PDXUI(object):
    bl_category = "STNH Mesh IO"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


class IOPDX_PT_PDXblender_info(PDXUI, Panel):
    # bl_idname = 'panel.io_pdx_mesh.help'
    bl_label = "Info"
    bl_options = {"HIDE_HEADER"}
    panel_order = 0

    def draw(self, context):
        self.layout.label(text="STNH Mesh IO - v{}".format(github.CURRENT_VERSION), icon="TOOL_SETTINGS")


class IOPDX_PT_PDXblender_file(PDXUI, Panel):
    # bl_idname = 'panel.io_pdx_mesh.file'
    bl_label = "File"
    panel_order = 1

    def draw(self, context):
        self.layout.label(text="Import:", icon="IMPORT")
        row = self.layout.row(align=True)
        row.operator("io_pdx_mesh.import_mesh", icon="MESH_CUBE", text="Load mesh ...")
        row.operator("io_pdx_mesh.import_anim", icon="RENDER_ANIMATION", text="Load anim ...")

        self.layout.label(text="Export:", icon="EXPORT")
        row = self.layout.row(align=True)
        row.operator("io_pdx_mesh.export_mesh", icon="MESH_CUBE", text="Save mesh ...")
        row.operator("io_pdx_mesh.export_anim", icon="RENDER_ANIMATION", text="Save anim ...")


class IOPDX_PT_PDXblender_tools(PDXUI, Panel):
    # bl_idname = 'panel.io_pdx_mesh.tools'
    bl_label = "Tools"
    panel_order = 2

    def draw(self, context):
        col = self.layout.column(align=True)

        col.label(text="PDX materials:")
        row = col.row(align=True)
        row.operator("io_pdx_mesh.material_create_popup", icon="MATERIAL", text="Create")
        row.operator("io_pdx_mesh.material_edit_popup", icon="SHADING_TEXTURE", text="Edit")
        col.separator()

        col.label(text="PDX bones:")
        row = col.row(align=True)
        op_ignore_bone = row.operator("io_pdx_mesh.ignore_bone", icon="GROUP_BONE", text="Ignore bones")
        op_ignore_bone.state = True
        op_unignore_bone = row.operator("io_pdx_mesh.ignore_bone", icon="BONE_DATA", text="Unignore bones")
        op_unignore_bone.state = False
        col.separator()

        # col.label(text='PDX animations:')
        # row = col.row(align=True)
        # row.operator('io_pdx_mesh.popup_message', icon='IPO_BEZIER', text='Create')
        # row.operator('io_pdx_mesh.popup_message', icon='NORMALIZE_FCURVES', text='Edit')
        # col.separator()

        col.label(text="PDX meshes:")
        row = col.row(align=True)
        row.operator("io_pdx_mesh.mesh_index_popup", icon="SORTALPHA", text="Set mesh order")


class IOPDX_PT_PDXblender_display(PDXUI, Panel):
    # bl_idname = 'panel.io_pdx_mesh.display'
    bl_label = "Display"
    bl_options = {"DEFAULT_CLOSED"}
    panel_order = 3

    def draw(self, context):
        col = self.layout.column(align=True)

        col.label(text="Display local axes:")
        row = col.row(align=True)
        op_show_bone_axis = row.operator("io_pdx_mesh.show_axis", icon="OUTLINER_OB_ARMATURE", text="Show on bones")
        op_show_bone_axis.show = True
        op_show_bone_axis.data_type = "ARMATURE"
        op_hide_bone_axis = row.operator("io_pdx_mesh.show_axis", icon="OUTLINER_DATA_ARMATURE", text="Hide on bones")
        op_hide_bone_axis.show = False
        op_hide_bone_axis.data_type = "ARMATURE"
        row = col.row(align=True)
        op_show_loc_axis = row.operator("io_pdx_mesh.show_axis", icon="OUTLINER_OB_EMPTY", text="Show on empties")
        op_show_loc_axis.show = True
        op_show_loc_axis.data_type = "EMPTY"
        op_hide_loc_axis = row.operator("io_pdx_mesh.show_axis", icon="OUTLINER_DATA_EMPTY", text="Hide on empties")
        op_hide_loc_axis.show = False
        op_hide_loc_axis.data_type = "EMPTY"


class IOPDX_PT_PDXblender_setup(PDXUI, Panel):
    # bl_idname = 'panel.io_pdx_mesh.setup'
    bl_label = "Setup"
    bl_options = {"DEFAULT_CLOSED"}
    panel_order = 4

    def draw(self, context):
        settings = context.scene.io_pdx_settings

        self.layout.prop(settings, "setup_engine")
        row = self.layout.row(align=True)
        row.label(text="Animation:")
        row.prop(context.scene.render, "fps", text="FPS")


class IOPDX_PT_PDXblender_help(PDXUI, Panel):
    # bl_idname = 'panel.io_pdx_mesh.help'
    bl_label = "Help"
    bl_options = {"DEFAULT_CLOSED"}
    panel_order = 5

    def draw(self, context):
        col = self.layout.column(align=True)

        col.operator("wm.url_open", icon="QUESTION", text="Addon Wiki").url = IO_PDX_INFO["doc_url"]
        col.operator("wm.url_open", icon="QUESTION", text="Paradox forums").url = IO_PDX_INFO["forum_url"]
        col.operator("wm.url_open", icon="QUESTION", text="Source code").url = IO_PDX_INFO["website"]
