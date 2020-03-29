bl_info = {
    "name": "Bake To Vertex",
    "version": (1, 0),
    "blender": (2, 80, 0),
}

import bpy
from bpy.types import Scene, Image


class BAKE_PT_Bake_panel(bpy.types.Panel):
    bl_label = "Bake To Vertex"
    bl_category = "Bake To Vertex"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    #image : bpy.props.PointerProperty(type=bpy.data.Image)

    def draw(self, context):
        layout = self.layout

        #layout.label(text="This is a label")
        layout = self.layout
        col = layout.column()
        row = col.row(align=True)
        row.prop_search(context.scene, 'bake_image_name', bpy.data, 'images')
        row.operator("image.open", icon="FILE_FOLDER", text="")
        self.layout.operator("object.bake_to_vertex", text="Bake")


def bake_uv_to_vc(image_name):
    # Lookup the image by name. Easier than trying to figure out which one is
    # currently active
    image = bpy.data.images[image_name]

    if not image.pixels:
        return

    width = image.size[0]
    height = image.size[1]

    # Keep UVs in the within the bounds to avoid out-of-bounds errors
    def _clamp_uv(val):
        return max(0, min(val, 1))

    ob = bpy.context.object
    
    if not ob.data.uv_layers.active:
        return
    
    # Need to set the mode to VERTEX_PAINT, otherwise the vertex color data is
    # empty for some reason
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')

    # Caching the image pixels makes this *much* faster
    local_pixels = list(image.pixels[:])

    for face in ob.data.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            uv_coords = ob.data.uv_layers.active.data[loop_idx].uv

            # Just sample the closest pixel to the UV coordinate. If you need
            # higher quality, an improved approach might be to implement
            # bilinear sampling here instead
            target = [round(_clamp_uv(uv_coords.x) * (width - 1)), round(_clamp_uv(uv_coords.y) * (height - 1))]
            index = ( target[1] * width + target[0] ) * 4

            bpy.context.object.data.vertex_colors.active.data[loop_idx].color[0] = local_pixels[index]
            bpy.context.object.data.vertex_colors.active.data[loop_idx].color[1] = local_pixels[index + 1]
            bpy.context.object.data.vertex_colors.active.data[loop_idx].color[2] = local_pixels[index + 2]
            bpy.context.object.data.vertex_colors.active.data[loop_idx].color[3] = local_pixels[index + 3]
            
    bpy.ops.object.mode_set(mode='OBJECT')



class BakeVertex(bpy.types.Operator):
    bl_idname = 'object.bake_to_vertex'
    bl_label = 'Bake To Vertecies'
    bl_options = {"REGISTER", "UNDO"}
 
 
    def execute(self, context):
        selected_objs = context.selected_objects.copy()
        for obj in selected_objs:
            context.view_layer.objects.active = obj
            bake_uv_to_vc(context.scene.bake_image_name)
        return {"FINISHED"}


classes = (BAKE_PT_Bake_panel,BakeVertex)


def register():
    bpy.types.Scene.bake_image_name = bpy.props.StringProperty(name = '')
    
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()