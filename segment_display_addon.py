import bpy
import typing
import copy
import os
import mathutils
from bpy.types import Scene, WindowManager, Image, ShaderNodeTree, ShaderNodeGroup

bl_info = {
    "name": "segment-display-generator",
    "description": "An addon that generates fully working 7 segment displays in various formats to display numbers or time.",
    "author": "DUDSS",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "3D View > Right sidebar > Segment display",
    "warning": "",
    "doc_url": "",
    "tracker_url": "https://github.com/xDUDSSx/segment-display-blender-addon",
    "category": "3D View"
}

################################################################################
# DATA
################################################################################

class SegmentAddonData(bpy.types.PropertyGroup):
    # Display type
    ########################################################################
    display_type: bpy.props.EnumProperty(
        name = "Display type",
        items = [
            ("numeric", "Numeric", "A display showing decimal numbers, including decimal places."),
            ("clock", "Clock", "A display showing time in a specific format (hours, minutes, seconds, milliseconds)"),
        ]
    )
    digits: bpy.props.IntProperty(
        name = "Digits",
        min = 1, max = 10,
        default = 3
    )
    fraction_digits: bpy.props.IntProperty(
        name = "Decimal places",
        min = 0, max = 10,
        default = 2
    )

    millisecond_digits: bpy.props.IntProperty(
        name = "Millisecond digits",
        min = 0, max = 3,
        default = 0
    )
    second_digits: bpy.props.IntProperty(
        name = "Second digits",
        min = 0, max = 2,
        default = 2
    )
    minute_digits: bpy.props.IntProperty(
        name = "Minute digits",
        min = 0, max = 2,
        default = 2
    )
    hour_digits: bpy.props.IntProperty(
        name = "Hour digits",
        min = 0, max = 3,
        default = 0
    )

    # Display value
    ########################################################################
    # Display value numeric
    display_value_numeric: bpy.props.EnumProperty(
        name = "Numeric display value",
        items = [
            ("number", "Number", "Show a specific decimal value"),
            ("frame", "Frame", "Show the current animation frame"),
            ("timer", "Timer", "Animate the display to go from one value to another"),
        ]
    )
    number: bpy.props.FloatProperty(
        name = "Number",
        min = 0,
        default = 43.12
    )
    frame_divisor: bpy.props.FloatProperty(
        name = "Divisor",
        min = 0,
        default = 1,
        description = "What number to divide the frame number with. Since frames are integers to get a changing fractional part use a divisor like 1.237"
    )
    frame_offset: bpy.props.IntProperty(
        name = "Frame offset",
        default = 0,
        description = "Offsets the current frame number by an amount (Can be negative)"
    )
    timer_number_from: bpy.props.FloatProperty(
        name = "From number",
        min = 0,
        default = 1
    )
    timer_number_to: bpy.props.FloatProperty(
        name = "To number",
        min = 0,
        default = 50
    )
    timer_frame_start: bpy.props.IntProperty(
        name = "Frame Start",
        min = 0,
        default = 50
    )
    timer_frame_end: bpy.props.IntProperty(
        name = "End",
        min = 0,
        default = 250
    )

    # Display value clock
    display_value_clock: bpy.props.EnumProperty(
        name = "Clock display value ",
        items = [
            ("seconds", "Seconds", "Show a specific time for a number of seconds"),
            ("time", "Time", "Show a specific time"),
            ("frame", "Frame", "Show the current animation frame converted to time in seconds"),
            ("timer", "Timer", "Animate the display count down/up from one time to another"),
        ]
    )
    hours: bpy.props.IntProperty(
        name = "Hours",
        min = 0,
        default = 12
    )
    minutes: bpy.props.IntProperty(
        name = "Minutes",
        min = 0, max = 59,
        default = 32
    )
    seconds: bpy.props.IntProperty(
        name = "Seconds",
        min = 0, max = 59,
        default = 5
    )
    milliseconds: bpy.props.IntProperty(
        name = "Milliseconds",
        min = 0,
        default = 374
    )
    number_of_seconds: bpy.props.FloatProperty(
        name = "Seconds",
        min = 0,
        default = 3666.143
    )
    clock_frame_divisor: bpy.props.FloatProperty(
        name = "Divisor",
        min = 0,
        default = 1,
        description = "What number to divide the frame number with. This can be set to the current FPS to show realtime animation time."
    )
    timer_time_from: bpy.props.FloatProperty(
        name = "From time",
        min = 0,
        default = 90,
        description = "The initial time in seconds"
    )
    timer_time_to: bpy.props.FloatProperty(
        name = "To time",
        min = 0,
        default = 0,
        description = "The target time in seconds"
    )

    # Appeareance
    ########################################################################
    digit_foreground: bpy.props.FloatVectorProperty(
        name="Digit foreground",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="Color of the lit digit segments"
    )
    digit_background: bpy.props.FloatVectorProperty(
        name="Digit background",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="Color of the unlit digit segments"
    )
    background: bpy.props.FloatVectorProperty(
        name="Background",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="Color of the display background"
    )
    emission_strength: bpy.props.FloatProperty(
        name = "Emission strength",
        min = 0,
        default = 2.5
    )
    normal_strength: bpy.props.FloatProperty(
        name = "Normal strength",
        min = 0,
        default = 0.5
    )
    hide_background: bpy.props.BoolProperty(
        name = "Hide background",
        default = False,
        description="Deletes the faces making up the background, leaving just the digit segments"
    )
    skew: bpy.props.FloatProperty(
        name = "Skew",
        default = 0,
        description = "Skews the display"
    )
    #style: bpy.props.EnumProperty - Set during register()

    # Classic style
    background_noise_strength: bpy.props.FloatProperty(
        name = "BG noise strength",
        min = 0,
        default = 1
    )
    background_noise_scale: bpy.props.FloatProperty(
        name = "BG noise scale",
        default = 2
    )

    # LCD style
    lcd_cell_width: bpy.props.FloatProperty(
        name = "Pixel width",
        description = "Pixel width factor",
        min = 0,
        default = 1
    )
    lcd_cell_height: bpy.props.FloatProperty(
        name = "Pixel height",
        description = "Pixel height factor",
        min = 0,
        default = 1.55
    )
    lcd_scale: bpy.props.FloatProperty(
        name = "Scale",
        default = 2
    )
    lcd_unit_strength: bpy.props.FloatProperty(
        name = "Unlit strength",
        description = "How bright unlit lcd pixels should appear",
        default = 0.010
    )
    lcd_cell_border_x_width: bpy.props.FloatProperty(
        name = "Pixel x gap",
        description = "Gap between pixels on the x axis",
        default = 0.1
    )
    lcd_cell_border_y_width: bpy.props.FloatProperty(
        name = "Pixel y gap",
        description = "Gap between pixels on the y axis",
        default = 0.1
    )
    lcd_cell_subpixel_border_width: bpy.props.FloatProperty(
        name = "Subpixel gap",
        description = "Gap between individual r,g,b subpixels",
        default = 0.02
    )



    # Advanced
    ########################################################################
    float_correction: bpy.props.FloatProperty(
        name = "Float correction",
        min = 0,
        default = 0.0001
    )
    join_display: bpy.props.BoolProperty( #TODO
        name = "Join display into single object",
        default = True
    )


################################################################################
# UI
################################################################################

class SegmentPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        return True


class MainPanel(SegmentPanel, bpy.types.Panel):
    bl_label = "Segment display"
    bl_idname = "SEGMENT_PT_main_panel"
    bl_category = "Segment display"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.segment_addon_data

        layout.label(text="Generate 7 segment displays", icon="INFO")

class DisplayTypePanel(SegmentPanel, bpy.types.Panel):
    bl_label = "Display type"
    bl_idname = "SEGMENT_PT_display_type_panel"
    bl_parent_id = "SEGMENT_PT_main_panel"
    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.segment_addon_data

        layout.prop(data, "display_type", expand=True)

        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align=True)

        if data.display_type == "numeric":
            col.prop(data, "digits")
            col.prop(data, "fraction_digits")
        elif data.display_type == "clock":
            col.prop(data, "hour_digits")
            col.prop(data, "minute_digits")
            col.prop(data, "second_digits")
            col.prop(data, "millisecond_digits")


class DisplayValuePanel(SegmentPanel, bpy.types.Panel):
    bl_label = "Display value"
    bl_idname = "SEGMENT_PT_display_value"
    bl_parent_id = "SEGMENT_PT_main_panel"
    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.segment_addon_data

        if data.display_type == "numeric":
            layout.prop(data, "display_value_numeric", expand=True)

            layout.use_property_split = True
            layout.use_property_decorate = False
            col = layout.column(align=True)

            if data.display_value_numeric == "number":
                col.prop(data, "number")
            elif data.display_value_numeric == "frame":
                col.prop(data, "frame_divisor")
                col.prop(data, "frame_offset")
            elif data.display_value_numeric == "timer":
                col.prop(data, "timer_number_from")
                col.prop(data, "timer_number_to")
                col.separator()
                col.prop(data, "timer_frame_start")
                col.prop(data, "timer_frame_end")

        elif data.display_type == "clock":
            layout.prop(data, "display_value_clock", expand=True)

            if data.display_value_clock == "seconds":
                layout.use_property_split = True
                layout.use_property_decorate = False
                col = layout.column(align=True)
                col.prop(data, "number_of_seconds")
            elif data.display_value_clock == "time":
                row = layout.row(align=True)
                row.label(text="Time to show (H, M, S, Ms):", icon="TIME")
                row = layout.row(align=True)
                row.prop(data, "hours", text="")
                row.prop(data, "minutes", text="")
                row.prop(data, "seconds", text="")
                row.prop(data, "milliseconds", text="")
            elif data.display_value_clock == "frame":
                layout.use_property_split = True
                layout.use_property_decorate = False
                col = layout.column(align=True)
                col.prop(data, "clock_frame_divisor")
                col.prop(data, "frame_offset")
            elif data.display_value_clock == "timer":
                layout.use_property_split = True
                layout.use_property_decorate = False
                col = layout.column(align=True)
                col.prop(data, "timer_time_from")
                col.prop(data, "timer_time_to")
                col.separator()
                col.prop(data, "timer_frame_start")
                col.prop(data, "timer_frame_end")


class DisplayAppearancePanel(SegmentPanel, bpy.types.Panel):
    bl_label = "Appeareance"
    bl_idname = "SEGMENT_PT_display_appearance"
    bl_parent_id = "SEGMENT_PT_main_panel"
    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.segment_addon_data

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(data, "digit_foreground")
        col.prop(data, "digit_background")
        col.prop(data, "emission_strength")
        col.separator()
        col.prop(data, "background")
        col.prop(data, "hide_background")
        col.separator()
        col.prop(data, "normal_strength")
        col.prop(data, "skew")

class DisplayStylePanel(SegmentPanel, bpy.types.Panel):
    bl_label = "Display style"
    bl_idname = "SEGMENT_PT_display_style"
    bl_parent_id = "SEGMENT_PT_display_appearance"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.segment_addon_data

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.label(text="Display style")
        layout.template_icon_view(data, "style", show_labels=True)

        if data.style == 'classic':
            col = layout.column(align=True)
            col.prop(data, "background_noise_strength")
            col.prop(data, "background_noise_scale")
        elif data.style == 'lcd':
            col = layout.column(align=True)
            col.prop(data, "lcd_cell_width")
            col.prop(data, "lcd_cell_height")
            col.separator()
            col.prop(data, "lcd_scale")
            col.prop(data, "lcd_unit_strength")
            col.separator()
            col.prop(data, "lcd_cell_border_x_width")
            col.prop(data, "lcd_cell_border_y_width")
            col.prop(data, "lcd_cell_subpixel_border_width")

class AdvancedPanel(SegmentPanel, bpy.types.Panel):
    bl_label = "Advanced"
    bl_idname = "SEGMENT_PT_advanced"
    bl_parent_id = "SEGMENT_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.segment_addon_data

        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align=True)
        col.prop(data, "float_correction")

        layout.use_property_split = False
        layout.prop(data, "join_display")


class GeneratePanel(SegmentPanel, bpy.types.Panel):
    bl_label = "Generate display"
    bl_idname = "SEGMENT_PT_generate_display"
    bl_parent_id = "SEGMENT_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.segment_addon_data

        layout.operator("segment_addon.create", icon="RESTRICT_VIEW_OFF")


################################################################################
# OPERATORS
################################################################################

class CreateDisplayOperator(bpy.types.Operator):
    bl_idname = "segment_addon.create"
    bl_label = "Create display"
    bl_description = "Create the segment display"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        data = scene.segment_addon_data

        print(f"Creating segment display [digits: {data.digits}]")
        print("Blend file path: " + SegmentAddon.addon_blend_path)

        # Load resources from the segment blend file
        link = False
        with bpy.data.libraries.load(SegmentAddon.addon_blend_path, link=link) as (data_src, data_dst):
            data_dst.meshes = ['segment_digit_mesh']
            data_dst.objects = ['segment_digit']
            data_dst.materials = ['7SegmentDisplay', '7SegmentDisplayBackground']
            data_dst.node_groups =  [
                                    '7SegmentDecimalProcessor', '7SegmentClockProcessor',
                                    '7SegmentTimerResolver',
                                    '7SegmentClassicShader', '7SegmentPlainShader', '7SegmentPlainLCDShader'
                                    ]
        resource = data_dst

        segment_addon = SegmentAddon(context, data, resource)
        if not segment_addon.validate_data():
            msg = "SegmentDisplayAddon: Invalid display type!"
            print(msg)
            self.report({'ERROR'}, msg)

        # Setup material
        segment_addon.setup_segment_material()

        # Generate digits
        digit_prototype = resource.objects[0]

        if data.display_type == "numeric":
            segment_addon.create_numeric_display(digit_prototype)
        elif data.display_type == "clock":
            segment_addon.create_clock_display(digit_prototype)

        return {'FINISHED'}


################################################################################
# CORE
################################################################################

class SegmentAddon:
    VC_STEP = 0.1
    VC_STEP_FAILSAFE = 0.01
    DIGIT_WIDTH = 12
    DIGIT_SEPARATOR_WIDTH = 3

    addon_directory_path = None
    addon_resources_dir = None
    addon_blend_path = None
    style_previews_dir = None

    previews = dict()
    style_previews = "styles_preview"

    def __init__(self, context, data: SegmentAddonData, resource):
        self.context = context
        self.data = data
        self.resource = resource

    def validate_data(self) -> bool:
        if self.data.display_type == "numeric":
            pass
        elif self.data.display_type == "clock":
            pass
        else:
            return False
        return True

    def create_numeric_display(self, digit_prototype):
        offset_step = self.DIGIT_WIDTH
        offset = 0
        for i in range(0, self.data.fraction_digits):
            self.create_digit(digit_prototype, offset, self.data.fraction_digits/10.0, self.VC_STEP*i)
            offset -= offset_step
        offset -= self.DIGIT_SEPARATOR_WIDTH
        for i in range(0, self.data.digits):
            self.create_digit(digit_prototype, offset, 0, self.VC_STEP*i)
            offset -= offset_step

    def create_clock_display(self, digit_prototype):
        offset_step = self.DIGIT_WIDTH
        offset = 0

        if self.data.millisecond_digits > 0:
            offset = self.create_digits(digit_prototype, offset, 0, self.data.millisecond_digits, offset_step)
            offset -= self.DIGIT_SEPARATOR_WIDTH
        if self.data.second_digits > 0:
            offset = self.create_digits(digit_prototype, offset, 0.1, self.data.second_digits, offset_step)
            offset -= self.DIGIT_SEPARATOR_WIDTH
        if self.data.minute_digits > 0:
            offset = self.create_digits(digit_prototype, offset, 0.2, self.data.minute_digits, offset_step)
            offset -= self.DIGIT_SEPARATOR_WIDTH
        if self.data.hour_digits > 0:
            offset = self.create_digits(digit_prototype, offset, 0.3, self.data.hour_digits, offset_step)

    def setup_segment_material(self):
        mat = self.resource.materials[0]
        self.setup_segment_display_processor(mat)
        self.setup_display_value(mat)
        self.setup_display_shader(mat)
        # Float correction
        mat.node_tree.nodes["segment_base"].inputs[2].default_value = self.data.float_correction

    def setup_display_shader(self, mat):
        """
        Sets up the node group responsible for styling the segment base mask output.
        This is referred to as "display style" in the settings.
        """
        # Create the appropriate shader depending on settings
        shader_node_group = self.create_display_style_shader(mat)
        Utils.move_node(shader_node_group, 1020, 671)
        shader_node_group.width = 212

        # Connect mask to the shader group
        mat.node_tree.links.new(mat.node_tree.nodes['segment_base'].outputs[0], shader_node_group.inputs[0])

        # Set style specific settings
        if self.data.style == "plain":
            pass
        elif self.data.style == "classic":
            shader_node_group.inputs[5].default_value = self.data.background_noise_strength
            shader_node_group.inputs[6].default_value = self.data.background_noise_scale
        elif self.data.style == "lcd":
            shader_node_group.inputs[5].default_value = self.data.lcd_cell_width
            shader_node_group.inputs[6].default_value = self.data.lcd_cell_height
            shader_node_group.inputs[7].default_value = self.data.lcd_scale
            shader_node_group.inputs[8].default_value = self.data.lcd_unit_strength

            # Process and set the rgb cell border
            cell_x_ramp = shader_node_group.node_tree.nodes['segment_lcd_shader'].node_tree.nodes['cell_x_ramp']
            cell_y_ramp = shader_node_group.node_tree.nodes['segment_lcd_shader'].node_tree.nodes['cell_y_ramp']
            x_points = SegmentAddon.lcd_style_calculate_x_ramp(self.data.lcd_cell_border_x_width, self.data.lcd_cell_subpixel_border_width)
            y_points = SegmentAddon.lcd_style_calculate_y_ramp(self.data.lcd_cell_border_y_width)
            print(x_points)
            print(y_points)
            for i, p in enumerate(x_points):
                cell_x_ramp.color_ramp.elements[i+1].position = p
            for i, p in enumerate(y_points):
                cell_y_ramp.color_ramp.elements[i+1].position = p

        # Set common settings
        shader_node_group.inputs[1].default_value = (self.data.digit_foreground.r, self.data.digit_foreground.g, self.data.digit_foreground.b, 1.0)
        shader_node_group.inputs[2].default_value = (self.data.digit_background.r, self.data.digit_background.g, self.data.digit_background.b, 1.0)
        shader_node_group.inputs[3].default_value = self.data.emission_strength
        shader_node_group.inputs[4].default_value = self.data.normal_strength

        # Connect the shader group to the principled shader
        principled = mat.node_tree.nodes['segment_principled']
        mat.node_tree.links.new(shader_node_group.outputs[0], principled.inputs[0]) # Base
        mat.node_tree.links.new(shader_node_group.outputs[1], principled.inputs[9]) # Roughness
        mat.node_tree.links.new(shader_node_group.outputs[2], principled.inputs[19]) # Emission
        mat.node_tree.links.new(shader_node_group.outputs[3], principled.inputs[20]) # Emission strength
        mat.node_tree.links.new(shader_node_group.outputs[4], principled.inputs[22]) # Normal

    def create_display_style_shader(self, mat):
        node_tree = None

        if self.data.style == "plain":
            node_tree = self.resource.node_groups[4]
        elif self.data.style == "classic":
            node_tree = self.resource.node_groups[3]
        elif self.data.style == 'lcd':
            node_tree = self.resource.node_groups[5]

        node_group = mat.node_tree.nodes.new(type='ShaderNodeGroup')
        node_group.node_tree = node_tree
        node_group.name = node_tree.name
        return node_group

    def setup_display_value(self, mat):
        """
        Sets up the 7SegmentBase number input to reflect display value settings.
        """
        if self.data.display_type == "numeric":
            if self.data.display_value_numeric == "number":
                self.setup_numeric_number_display_value(mat, self.data.number)
            elif self.data.display_value_numeric == "frame":
                self.setup_numeric_frame_display_value(mat, self.data.frame_divisor)
            elif self.data.display_value_numeric == "timer":
                self.setup_numeric_timer_display_value(mat, self.data.timer_number_from, self.data.timer_number_to)
        elif self.data.display_type == 'clock':
            if self.data.display_value_clock == "seconds":
                self.setup_numeric_number_display_value(mat, self.data.number_of_seconds)
            elif self.data.display_value_clock == "time":
                self.setup_clock_time_display_value(mat)
            elif self.data.display_value_clock == "frame":
                self.setup_numeric_frame_display_value(mat, self.data.clock_frame_divisor)
            elif self.data.display_value_clock == "timer":
                self.setup_numeric_timer_display_value(mat, self.data.timer_time_from, self.data.timer_time_to)

    def setup_numeric_number_display_value(self, mat, number):
        """
        Connects a simple value node to the number input.
        """
        # Get number from the settings and set it as input for the segment base group
        value_node = mat.node_tree.nodes.new(type="ShaderNodeValue")
        segment_base_group = mat.node_tree.nodes['segment_base']

        value_node.outputs[0].default_value = number
        mat.node_tree.links.new(value_node.outputs[0], segment_base_group.inputs[0])
        Utils.move_node(value_node, 450, 300)

        # Set divisor to 1
        mat.node_tree.nodes["segment_base"].inputs[1].default_value = 1

    def setup_numeric_frame_display_value(self, mat, divisor):
        """
        Connects an animated frame value node to the number input.
        """
        frame_node = Utils.create_frame_value_node(mat.node_tree, self.data.frame_offset)
        segment_base_group = mat.node_tree.nodes['segment_base']

        mat.node_tree.links.new(frame_node.outputs[0], segment_base_group.inputs[0])
        mat.node_tree.nodes["segment_base"].inputs[1].default_value = divisor

        Utils.move_node(frame_node, 450, 300)

    def setup_numeric_timer_display_value(self, mat, from_value, to_value):
        """
        Timer is realized by running the frame value through the 7SegmentTimerResolver node.
        """
        # Create frame node
        frame_node = Utils.create_frame_value_node(mat.node_tree)
        segment_base_group = mat.node_tree.nodes['segment_base']
        Utils.move_node(frame_node, 450-190, 300)

        # Create timer resolver group
        timer_resolver_tree = self.resource.node_groups[2]
        timer_resolver_group = mat.node_tree.nodes.new(type='ShaderNodeGroup')
        timer_resolver_group.node_tree = timer_resolver_tree
        timer_resolver_group.name = "7SegmentTimerResolver"
        Utils.move_node(timer_resolver_group, 463, 370)

        # Link nodes
        mat.node_tree.links.new(frame_node.outputs[0], timer_resolver_group.inputs[4])
        mat.node_tree.links.new(timer_resolver_group.outputs[0], segment_base_group.inputs[0])

        # Set divisor to 1
        mat.node_tree.nodes["segment_base"].inputs[1].default_value = 1

        # Set remaining timer resolver inputs according to settings
        timer_resolver_group.inputs[0].default_value = from_value
        timer_resolver_group.inputs[1].default_value = to_value
        timer_resolver_group.inputs[2].default_value = self.data.timer_frame_start
        timer_resolver_group.inputs[3].default_value = self.data.timer_frame_end

    def setup_clock_time_display_value(self, mat):
        hours = self.data.hours
        minutes = self.data.hours
        seconds = self.data.hours
        milliseconds = self.data.hours
        number = hours * 3600 + minutes * 60 + seconds + (milliseconds/1000)
        self.setup_numeric_number_display_value(mat, number)

    def setup_segment_display_processor(self, mat):
        """
        Sets the node group responsible for adjusting the 7SegmentCore number input using the display vertex color.
        """
        segment_base_group = mat.node_tree.nodes['segment_base']
        number_node = segment_base_group.node_tree.nodes['number_adjusted']
        display_node = segment_base_group.node_tree.nodes['display_converted']

        processor_name = ""
        processor_node_tree = None
        if self.data.display_type == "numeric":
            processor_node_tree = self.resource.node_groups[0]
            processor_name = "Decimal"
        elif self.data.display_type == "clock":
            processor_node_tree = self.resource.node_groups[1]
            processor_name = "Clock"

        processor_node_group = segment_base_group.node_tree.nodes.new(type='ShaderNodeGroup')
        processor_node_group.node_tree = processor_node_tree
        processor_node_group.name = f"7Segment{processor_name}Processor"
        processor_node_group.location = number_node.location[0] + 280, number_node.location[1] + 70

        segment_core_group = segment_base_group.node_tree.nodes['segment_core']

        segment_base_group.node_tree.links.new(number_node.outputs[0], processor_node_group.inputs[0])
        segment_base_group.node_tree.links.new(display_node.outputs[0], processor_node_group.inputs[1])
        segment_base_group.node_tree.links.new(processor_node_group.outputs[0], segment_core_group.inputs[0])

    def create_digits(self, digit_prototype, offset, display, digit_count, offset_step):
        for i in range(0, digit_count):
            self.create_digit(digit_prototype, offset, display, self.VC_STEP*i)
            offset -= offset_step
        return offset

    def create_digit(self, digit_prototype, offset, display, digit):
        obj = Utils.copy_object(digit_prototype)
        bpy.context.collection.objects.link(obj)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')

        # Select segments face map
        bpy.ops.mesh.select_all(action = 'DESELECT')
        obj.face_maps.active_index = bpy.context.object.face_maps['segments'].index
        bpy.ops.object.face_map_select()

        # Add materials
        obj.data.materials.append(self.resource.materials[1])
        obj.data.materials.append(self.resource.materials[0])
        obj.active_material_index = 1
        bpy.ops.object.material_slot_assign()

        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        self.create_vertex_color_map(mesh, "Digit", digit)
        self.create_vertex_color_map(mesh, "Display", display)

        # Move by offset
        obj.location.x += offset

    @classmethod
    def lcd_style_calculate_x_ramp(cls, bW, sbW) -> tuple:
        bWH = bW/2
        sbWH = sbW/2

        rgbW = (1 - bW) - sbW*2

        p1 = bWH
        p6 = 1 - bWH

        rgb1 = bWH + sbWH + ((1/3)*rgbW)
        p2 = rgb1 - sbWH
        p3 = rgb1 + sbWH

        rgb2 = bWH + sbW + sbWH + ((2/3)*rgbW)
        p4 = rgb2 - sbWH
        p5 = rgb2 + sbWH

        print(f"bw: {bW} bWH: {bWH} sbW: {sbW} rgbW: {rgbW} rgb1: {rgb1} rgb2: {rgb2} p[]: {p1} {p2} {p3} {p4} {p5} {p6}")
        return (p1, p2, p3, p4, p5, p6)

    @classmethod
    def lcd_style_calculate_y_ramp(cls, bW) -> tuple:
        bWH = bW/2
        p1 = bWH
        p2 = 1 - bWH
        return (p1, p2)

    @classmethod
    def vertex_paint_all(cls, mesh, color_map, value):
        i = 0
        for poly in mesh.polygons:
           for idx in poly.loop_indices:
               color_map.data[i].color = [value] * 3 + [1]
               i += 1

    @classmethod
    def create_vertex_color_map(cls, mesh, name, value):
        mesh.vertex_colors.new(name=name)
        color_map = mesh.vertex_colors[name]
        cls.vertex_paint_all(mesh, color_map, value + cls.VC_STEP_FAILSAFE)


class Utils:
    @staticmethod
    def move_node(node, dx, dy):
        node.location = node.location[0] + dx, node.location[1] + dy

    @staticmethod
    def create_frame_value_node(node_tree, offset=0):
        value_node = node_tree.nodes.new('ShaderNodeValue')
        Utils.create_expression_driver(value_node.outputs[0], 'default_value', 'frame' if offset == 0 else ('frame+'+str(offset)))
        value_node.label = "frame"
        return value_node

    @staticmethod
    def create_expression_driver(target, prop, expression):
        driver = target.driver_add(prop).driver
        driver.expression = expression

    @staticmethod
    def copy_object(obj):
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        return new_obj

    @staticmethod
    def s2lin(x):
            a = 0.055
            if x <=0.04045 :
                y = x * (1.0 / 12.92)
            else:
                y = pow( (x + a) * (1.0 / (1 + a)), 2.4)
            return y

    @staticmethod
    def lin2s(x):
        a = 0.055
        if x <=0.0031308:
            y = x * 12.92
        else:
            y = (1 + a) * pow(x, 1 / 2.4) - a
        return y


################################################################################
# ADDON
################################################################################

classes = [MainPanel, DisplayTypePanel, DisplayValuePanel, DisplayAppearancePanel, DisplayStylePanel, AdvancedPanel, GeneratePanel, SegmentAddonData, CreateDisplayOperator]

def load_preview(pcoll, name, filepath, type):
    if not name in pcoll.keys():
        return pcoll.load(name, filepath, type)
    else:
        print("Preview '" + name +"' already exists!")
        return pcoll[name]


def generate_style_previews():
    directory = SegmentAddon.style_previews_dir
    pcoll = SegmentAddon.previews[SegmentAddon.style_previews]
    print("Loading style previews from directory: " + directory)

    items = []
    to_load = [
        ["plain", "Plain", "angery.png"],
        ["classic", "Classic", "hmm.png"],
        ["lcd", "LCD", "hmmw.png"],
    ]

    for i, style in enumerate(to_load):
        filepath = os.path.join(directory, style[2])
        if not filepath in pcoll.keys():
            thumb = None
            if os.path.exists(filepath):
                thumb = load_preview(pcoll, filepath, filepath, 'IMAGE')
            else:
                filepath = os.path.join(directory, "missing.png")
                thumb = load_preview(pcoll, filepath, filepath, 'IMAGE')
            items.append((style[0], style[1], "", thumb.icon_id, i))

    return items


def register():
    print("SegmentAddon: Registering")
    print("")
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    SegmentAddon.addon_directory_path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    SegmentAddon.addon_resources_dir = os.path.join(SegmentAddon.addon_directory_path, 'resources')
    SegmentAddon.addon_blend_path = os.path.join(SegmentAddon.addon_resources_dir, 'segment.blend')
    SegmentAddon.style_previews_dir = os.path.join(SegmentAddon.addon_resources_dir, 'styles')

    print("Segment addon dir: " + SegmentAddon.addon_directory_path)
    print("Segment resource dir: " + SegmentAddon.addon_resources_dir)
    print("Segment blend path: " + SegmentAddon.addon_blend_path)
    print("Segment style previews dir: " + SegmentAddon.style_previews_dir)

    Scene.segment_addon_data = bpy.props.PointerProperty(type=SegmentAddonData)

    # Create the display style enum
    SegmentAddon.previews[SegmentAddon.style_previews] = bpy.utils.previews.new()
    style_previews = generate_style_previews()
    SegmentAddonData.style = bpy.props.EnumProperty(
        items=style_previews
    )


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    for preview in SegmentAddon.previews.values():
        bpy.utils.previews.remove(preview)
    SegmentAddon.previews.clear()

    del Scene.segment_addon_data


if __name__ == "__main__":
    register()
