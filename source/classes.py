import json
import os
import time

import wx
import wx.lib.scrolledpanel
import wx.media
import wx.propgrid

from . import constants, environment, utils
from .errors import ErrorMessage, OceanFloorError


class MenuItem(wx.MenuItem):
    """A subclass of `wx.MenuItem` that adds an option to specify a bitmap filename in the constructor.
    """
    def __init__(self, bitmap_filename=None, *args, **kwargs):
        """Creates a new MenuItem.
        """
        super().__init__(*args, **kwargs)

        if bitmap_filename:
            self.Bitmap = wx.Bitmap((environment.BITMAPS_PATH / bitmap_filename).as_posix())


def show_error(message, context):
    """Shows an error message dialog with the error message and context.
    """
    return wx.MessageDialog(None, f"{context}: {message}", "Error", wx.OK|wx.CENTRE|wx.ICON_ERROR).ShowModal()


def show_warning(warning):
    """Shows a warning message dialog with the warning message.
    """
    return wx.MessageDialog(None, str(warning), "Warning", wx.OK|wx.CENTRE|wx.ICON_WARNING).ShowModal()


class Effect:
    """An effect, deserialized from a JSON object
    as defined in the containing plugin.
    """

    def __init__(self, plugin_name, effect_filename):
        """Creates a new `Effect` object using the specified `plugin_name` and `effect_filename`.
        """
        self.plugin_name = plugin_name
        self.effect_filename = effect_filename

        # Validate plugin folder exists
        plugin_path = environment.PLUGINS_PATH / plugin_name
        if not plugin_path.is_dir():
            raise OceanFloorError(ErrorMessage.PLUGIN_NOT_RECOGNIZED.format(plugin_name))

        # Validate effect file exists
        effect_path = plugin_path / "effects" / effect_filename
        if not effect_path.is_file():
            raise OceanFloorError(ErrorMessage.EFFECT_NOT_RECOGNIZED.format(effect_filename, plugin_name))

        # Validate the effect's json and load it as a dict
        try:
            with open(effect_path, "r") as effect_as_json:
                effect_as_dict = json.load(effect_as_json)
        except ValueError:
            raise OceanFloorError(ErrorMessage.EFFECT_FILE_CONTAINS_INVALID_JSON.format(plugin_name, effect_filename))

        # Validate required keys exist in the dict and add them as attributes
        for key in constants.EFFECT_REQUIRED_KEYS:
            if key in effect_as_dict.keys():
                # create control objects
                if key == "controls":
                    self.controls = []
                    for control_as_dict in effect_as_dict["controls"]:
                        self.controls.append(EffectControl(plugin_name, effect_filename, control_as_dict))
                # add other attributes
                else:
                    self.__dict__[key] = effect_as_dict[key]
            else:
                raise OceanFloorError(ErrorMessage.EFFECT_FILE_MISSING_REQUIRED_KEY.format(key, plugin_name, effect_filename))

        # Validate optional keys exist in the dict and add them as attributes
        for key in constants.EFFECT_OPTIONAL_KEYS:
            if key in effect_as_dict.keys():
                self.__dict__[key] = effect_as_dict[key]

        # Get bitmap for the effect
        image_path = (environment.PLUGINS_PATH / plugin_name / "bitmaps" / (os.path.splitext(effect_filename)[0] + ".png")).as_posix()
        if os.path.exists(image_path):
            self.bitmap = wx.Bitmap(image_path)
        else:
            image_path = (environment.BITMAPS_PATH / "unknown.png").as_posix()
            self.bitmap = wx.Bitmap(image_path)

    def __repr__(self):
        return f"Effect({self.plugin_name}, {self.effect_filename})"


class EffectControl:
    """Effect controls are objects that allow the user to interact
    with the effect and give it the information necessary to make it work,
    as certain named parameters (`magic_names` and their `magic_values`).
    """

    def __init__(self, plugin_name, effect_filename, control_as_dict):
        """Creates a new `EffectControl` using the specified `plugin_name` and `effect_filename`,
        and the `control_as_dict` deserialized from the containing effect's JSON file.
        """
        # Validate required keys exist in the dict and add them as attributes
        for key in constants.EFFECT_CONTROL_REQUIRED_KEYS:
            if key in control_as_dict.keys():
                if key == "type" and control_as_dict["type"] not in constants.EFFECT_CONTROL_ALLOWED_TYPES:
                    raise OceanFloorError(ErrorMessage.CONTROL_IN_EFFECT_FILE_HAS_UNKNOWN_TYPE.format(control_as_dict["type"], plugin_name, effect_filename))
                self.__dict__[key] = control_as_dict[key]
            else:
                raise OceanFloorError(ErrorMessage.CONTROL_IN_EFFECT_FILE_MISSING_REQUIRED_KEY.format(key, plugin_name, effect_filename))

        # Validate optional keys exist in the dict and add them as attributes
        for key in constants.EFFECT_CONTROL_OPTIONAL_KEYS:
            if key in control_as_dict.keys():
                self.__dict__[key] = control_as_dict[key]


class EffectViewer(wx.Dialog):
    """An dialog that shows an `Effect`'s data.
    """
    def __init__(self, parent, effect):
        """Creates a new `EffectViewer` that shows the data of the specified `effect`.
        """
        super().__init__(parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, title="Effect Viewer")
        self.BackgroundColour = "White"
        self.SetDoubleBuffered(True)

        self.effect_name_text = wx.StaticText(self, label=effect.name, style=wx.ST_ELLIPSIZE_END|wx.ALIGN_CENTER_HORIZONTAL)
        self.plugin_text = wx.StaticText(self, label=effect.plugin_name, style=wx.ST_ELLIPSIZE_END|wx.ALIGN_CENTER_HORIZONTAL)
        self.effect_name_text.Font = wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.plugin_text.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        #self.label_text.MaxSize = [i - 20 for i in constants.TIMELINE_ITEM_PANEL_SIZE]

        self.static_line_left = wx.StaticLine(self)
        self.static_bitmap = wx.StaticBitmap(self, bitmap=effect.bitmap)
        self.static_line_right = wx.StaticLine(self)
        self.static_line_left.Size[1] = 1
        self.static_line_right.Size[1] = 1

        self.description_text = wx.StaticText(self, label=effect.description, style=wx.ST_ELLIPSIZE_END|wx.ALIGN_CENTER_HORIZONTAL)
        self.description_text.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.controls_static_box_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Controls")
        if effect.controls:
            for control in effect.controls:
                inner_sizer = wx.BoxSizer(wx.HORIZONTAL)
                inner_sizer.AddSpacer(10)
                inner_sizer.Add(wx.StaticText(self.controls_static_box_sizer.StaticBox, label=control.name, style=wx.ST_ELLIPSIZE_END), 0, wx.ALIGN_LEFT)
                inner_sizer.AddStretchSpacer()
                inner_sizer.AddSpacer(20)  # Minimal space between name and description
                inner_sizer.Add(wx.StaticText(self.controls_static_box_sizer.StaticBox, label=control.description, style=wx.ST_ELLIPSIZE_END), 0, wx.ALIGN_RIGHT)
                inner_sizer.AddSpacer(10)
                self.controls_static_box_sizer.Add(inner_sizer, 0, wx.EXPAND)
                self.controls_static_box_sizer.AddSpacer(5)
                self.controls_static_box_sizer.Add(wx.StaticLine(self.controls_static_box_sizer.StaticBox), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
                self.controls_static_box_sizer.AddSpacer(5)

        self.show_full_info_button = wx.Button(self, label="Show Full Info")

        self.info_static_box_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Info")
        for item in ["name", "plugin_name", "effect_filename", "description", "magic", "color"]:
            inner_sizer = wx.BoxSizer(wx.HORIZONTAL)
            inner_sizer.AddSpacer(10)
            inner_sizer.Add(wx.StaticText(self.info_static_box_sizer.StaticBox, label=item.replace("_", " ").title(), style=wx.ST_ELLIPSIZE_END), 0, wx.ALIGN_LEFT)
            inner_sizer.AddStretchSpacer()
            inner_sizer.AddSpacer(20)

            if item in ["magic"]:  # Multiline
                inner_sizer.Add(wx.TextCtrl(self.info_static_box_sizer.StaticBox, value=getattr(effect, item), style=wx.TE_MULTILINE|wx.TE_READONLY), 1, wx.ALIGN_RIGHT|wx.EXPAND)
            else:
                inner_sizer.Add(wx.StaticText(self.info_static_box_sizer.StaticBox, label=getattr(effect, item), style=wx.ST_ELLIPSIZE_END), 0, wx.ALIGN_RIGHT)

            inner_sizer.AddSpacer(10)
            self.info_static_box_sizer.Add(inner_sizer, 0, wx.EXPAND)
            self.info_static_box_sizer.AddSpacer(5)
            self.info_static_box_sizer.Add(wx.StaticLine(self.info_static_box_sizer.StaticBox), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
            self.info_static_box_sizer.AddSpacer(5)

        self.bitmap_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bitmap_sizer.AddSpacer(5)
        self.bitmap_sizer.Add(self.static_line_left, 1, wx.CENTER, 0)
        self.bitmap_sizer.AddSpacer(5)
        self.bitmap_sizer.Add(self.static_bitmap)
        self.bitmap_sizer.AddSpacer(5)
        self.bitmap_sizer.Add(self.static_line_right, 1, wx.CENTER, 0)
        self.bitmap_sizer.AddSpacer(5)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.MinSize = (500, 250)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.effect_name_text, 0, wx.CENTER)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.plugin_text, 0, wx.CENTER)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.bitmap_sizer, 0, wx.CENTER|wx.EXPAND)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.description_text, 0, wx.CENTER)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.controls_static_box_sizer, 0, wx.CENTER|wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.show_full_info_button, 0, wx.CENTER)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.info_static_box_sizer, 0, wx.CENTER|wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        self.main_sizer.AddSpacer(5)

        self.SetSizerAndFit(self.main_sizer)
        self.info_static_box_sizer.StaticBox.Hide()
        self.Layout()
        self.SetSizerAndFit(self.main_sizer)
        self.show_full_info_button.Bind(wx.EVT_BUTTON, self.on_show_full_info)

    def on_show_full_info(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Show Full Info" button is clicked.
        Shows the info static box if it's hidden, and vice vera.
        """
        if self.show_full_info_button.Label == "Show Full Info":
            self.show_full_info_button.Label = "Hide"
            self.info_static_box_sizer.StaticBox.Show(True)
        else:
            self.show_full_info_button.Label = "Show Full Info"
            self.info_static_box_sizer.StaticBox.Hide()

        self.Layout()
        self.SetSizerAndFit(self.main_sizer)


class InputOutputVideoPanel(wx.Panel):
    """A panel that shows the input/output video path.
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DOUBLE)
        self.BackgroundColour = utils.color_from_hex("F799AB")

        self.path_text = wx.StaticText(self, label="\\", style=wx.ST_ELLIPSIZE_END)
        self.path_text.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.path_text.MaxSize = [i - 20 for i in constants.TIMELINE_ITEM_PANEL_SIZE]

        self.static_line_left = wx.StaticLine(self)
        self.static_bitmap = wx.StaticBitmap(self, bitmap=Bitmap("inputoutput.png"))
        self.static_line_right = wx.StaticLine(self)
        self.static_line_left.Size[1] = 1
        self.static_line_right.Size[1] = 1

        self.edit_button = BitmapButton("edit.png", parent=self, size=(24, 24))
        self.edit_button.callback_data = self

        self.bitmap_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bitmap_sizer.AddSpacer(5)
        self.bitmap_sizer.Add(self.static_line_left, 1, wx.CENTER, 0)
        self.bitmap_sizer.AddSpacer(5)
        self.bitmap_sizer.Add(self.static_bitmap)
        self.bitmap_sizer.AddSpacer(5)
        self.bitmap_sizer.Add(self.static_line_right, 1, wx.CENTER, 0)
        self.bitmap_sizer.AddSpacer(5)

        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_sizer.AddStretchSpacer()
        self.buttons_sizer.Add(self.edit_button)
        self.buttons_sizer.AddStretchSpacer()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.MinSize = constants.TIMELINE_ITEM_PANEL_SIZE
        self.main_sizer.AddStretchSpacer()
        self.main_sizer.Add(self.path_text, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 5)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.bitmap_sizer, 0, wx.EXPAND, 0)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.CENTER, 0)
        self.main_sizer.AddStretchSpacer()

        self.SetSizerAndFit(self.main_sizer)

    def set_path(self, path):
        base_path = os.path.basename(path)
        if not base_path:
            base_path = "\\"
        self.path_text.Label = base_path
        self.path_text.MaxSize = [i - 20 for i in constants.TIMELINE_ITEM_PANEL_SIZE]

        self.Layout()


class Bitmap(wx.Bitmap):
    """A subclass of `wx.Bitmap` that adds the option to specify a `bitmap_filename` in the constructor.
    This file, from the bitmaps folder, is used on the button.
    """
    def __init__(self, bitmap_filename):
        super().__init__((environment.BITMAPS_PATH / bitmap_filename).as_posix())


class BitmapButton(wx.BitmapButton):
    """A subclass of `wx.BitmapButton` that adds the option to specify a `bitmap_filename` in the constructor.
    This file, from the bitmaps folder, is used on the button.
    """
    def __init__(self, bitmap_filename, *args, **kwargs):
        """Creates a new BitmapButton.
        """
        super().__init__(*args, **kwargs)
        self.BitmapLabel = Bitmap(bitmap_filename)


ArrayStringProperty = wx.propgrid.ArrayStringProperty
BoolProperty = wx.propgrid.BoolProperty
ColourProperty = wx.propgrid.ColourProperty
CursorProperty = wx.propgrid.CursorProperty
DateProperty = wx.propgrid.DateProperty
DirProperty = wx.propgrid.DirProperty
EditEnumProperty = wx.propgrid.EditEnumProperty
EnumProperty = wx.propgrid.EnumProperty
FileProperty = wx.propgrid.FileProperty
FlagsProperty = wx.propgrid.FlagsProperty
FloatProperty = wx.propgrid.FloatProperty
#FontProperty = wx.propgrid.FontProperty
ImageFileProperty = wx.propgrid.ImageFileProperty
#IntProperty = wx.propgrid.IntProperty
LongStringProperty = wx.propgrid.LongStringProperty
MultiChoiceProperty = wx.propgrid.MultiChoiceProperty
PropertyCategory = wx.propgrid.PropertyCategory
StringProperty = wx.propgrid.StringProperty
SystemColourProperty = wx.propgrid.SystemColourProperty
#UIntProperty = wx.propgrid.UIntProperty


# https://github.com/wxWidgets/Phoenix/blob/master/demo/PropertyGrid.py

class RGBColourProperty(wx.propgrid.ColourProperty):
    """A custom `RGBColourProperty` for the `wx.propgrid.PropertyGrid`.
    """
    def get_translated_value(self):
        """Returns the `RGBColourProperty`'s value as a `RRGGBB` string.
        """
        return f"{self.m_value.red:02x}{self.m_value.green:02x}{self.m_value.blue:02x}"

    def set_translated_value(self, translated_value):
        """Sets the `RGBColourProperty`'s value to the specified `translated_value`
        after parsing it to a `wx.Colour`.
        """
        value = wx.Colour(*utils.color_from_hex(translated_value))
        self.SetValue(value)


class FontProperty(wx.propgrid.EnumProperty):
    """A custom `FontProperty` for the `wx.propgrid.PropertyGrid`.
    """
    def __init__(self, label):
        """Creates a new `FontProperty` with the specified `label` and the list of fonts
        generated by scanning the computer's fonts directory.
        """
        self.all_fonts = [font_file for font_file in os.listdir(environment.FONTS_DIR) if os.path.splitext(font_file)[1].lower() in [".ttf", ".otf"]]
        super().__init__(label, labels=self.all_fonts)

    def get_translated_value(self):
        """Returns the selected font.
        """
        return self.all_fonts[self.m_value]

    def set_translated_value(self, translated_value):
        """Tries setting the `FontProperty`'s value to the specified font.
        """
        if translated_value in self.all_fonts:
            self.m_value = self.all_fonts.index(translated_value)

        else:
            show_warning(f"Font {translated_value} not found, selected another font instead.")
            self.m_value = 0


class IntProperty(wx.propgrid.IntProperty):
    """A custom `IntProperty` for the `wx.propgrid.PropertyGrid`.
    """
    def get_translated_value(self):
        """Returns the `IntProperty`'s value as an int.
        """
        return int(self.m_value)

    def set_translated_value(self, translated_value):
        """Sets the `IntProperty`'s value to the specified `translated_value`
        after parsing it to an int.
        """
        self.m_value = int(translated_value)


class UIntProperty(wx.propgrid.UIntProperty):
    """A custom `UIntProperty` for the `wx.propgrid.PropertyGrid`.
    """
    def get_translated_value(self):
        """Returns the `UIntProperty`'s value as an unsigned int.
        """
        return int(self.m_value)

    def set_translated_value(self, translated_value):
        """Sets the `UIntProperty`'s value to the specified `translated_value`
        after parsing it to an unsigned int.
        """
        self.m_value = int(translated_value)


class UnemptyStringProperty(wx.propgrid.StringProperty):
    """A custom `UnemptyStringProperty` for the `wx.propgrid.PropertyGrid`.
    """
    def get_translated_value(self):
        """Returns the `UnemptyStringProperty`'s value as a string,
        or "Not set" if it's empty.
        """
        if not self.m_value:
            return "Not set"

        return self.m_value

    def set_translated_value(self, translated_value):
        """Sets the `UnemptyStringProperty`'s value to the specified `translated_value`,
        or "Not set" if it's empty.
        """
        if not translated_value:
            self.m_value = "Not set"

        self.m_value = translated_value


class PluginsTree(wx.TreeCtrl):
    """A tree that shows all the installed plugins and their effects.
    Adding `TimelineItem`s to the `Timeline` is done by selecting an effect from the tree.
    """
    def __init__(self, parent, effects):
        """Creates a `PluginsTree` by using the specified dictionary
        of {(plugin_name, effect_filename):`Effect` object}.
        """
        super().__init__(parent, style=wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_NO_LINES|wx.TR_TWIST_BUTTONS|wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)  # wx.TR_HIDE_ROOT|
        # Validity of images depends on dictionaries maintaining order of item insertion
        # so that two iterations will result in the same order
        # (effects is iterated over twice: once for adding images to the image list,
        # and again for adding the items to the tree - the image list must be set before adding a tree item).
        # This means that on python versions < 3.6, incorrect images may show.
        # For more info: https://stackoverflow.com/a/39537308

        root_node = self.AddRoot(text="")
        image_list = wx.ImageList(25, 25)
        visited_plugins = []
        plugin_nodes = {}

        # Build image list
        for (plugin_name, effect_filename), effect in effects.items():
            if plugin_name not in visited_plugins:
                image_path = (environment.PLUGINS_PATH / plugin_name / "icon.png").as_posix()

                if os.path.exists(image_path):
                    image_list.Add(wx.Bitmap(image_path))
                else:
                    image_path = (environment.BITMAPS_PATH / "unknown.png").as_posix()
                    image_list.Add(wx.Bitmap(image_path))

                visited_plugins.append(plugin_name)

            image_list.Add(effect.bitmap)

        self.AssignImageList(image_list)

        # Create nodes and assign images
        image_index = 0
        for (plugin_name, effect_filename), effect in effects.items():
            if plugin_name in plugin_nodes.keys():
                plugin_node = plugin_nodes[plugin_name]
            else:
                plugin_node = self.AppendItem(root_node, plugin_name, image=image_index)
                plugin_nodes[plugin_name] = plugin_node
                self.SetItemData(plugin_node, plugin_name)

                image_index += 1

            effect_node = self.AppendItem(plugin_node, effect.name, image=image_index)
            self.SetItemData(effect_node, effect)

            image_index += 1

        self.SetDoubleBuffered(True)

    def on_tool_tip(self, event):
        """Callback function - called when the mouse hovers over a tree item.
        Sets the tooltip to the effect's description if it's an effect,
        otherwise to the plugin's name.
        """
        item_data = self.GetItemData(event.GetItem())
        if isinstance(item_data, Effect):
            event.ToolTip = item_data.description
        else:
            event.ToolTip = str(item_data)
        event.Skip()

    def get_selected_effect(self):
        """Returns the `Effect` object associated with the currently selected tree item.
        """
        selection = self.Selection
        if selection.IsOk():
            item_data = self.GetItemData(selection)
            if isinstance(item_data, Effect):
                return item_data


class ScrollableContainer(wx.lib.scrolledpanel.ScrolledPanel):
    """A base class for a scrollable container of items.
    Provides automatic scrolling and some utility functions
    for adding, removing items etc.
    """
    def __init__(self, parent, orientation):
        """Creates a new `ScrollableContainer`. Sets up scrolling.
        """
        super().__init__(parent)
        self.main_sizer = wx.BoxSizer(orientation)
        self.SetSizerAndFit(self.main_sizer)
        self.SetDoubleBuffered(True)

        if orientation == wx.HORIZONTAL:
            self.SetupScrolling(scroll_y=False)
        else:
            self.SetupScrolling(scroll_x=False)

    def append(self, item):
        """Appends the item to the container.
        """
        self.main_sizer.Add(item, 0, wx.EXPAND, 0)
        self.Sizer = self.main_sizer
        self.Scroll((0, 0))
        self.FitInside()  # https://stackoverflow.com/a/22081284

    def insert(self, index, item):
        """Inserts the item to the specified index in the container.
        """
        self.main_sizer.Insert(index, item, 0, wx.EXPAND)
        self.Sizer = self.main_sizer
        self.main_sizer.Layout()

    def remove(self, index):
        """Removes the item at the specified index in the container.
        """
        item = self.main_sizer.Children[index].Window
        self.main_sizer.Detach(item)
        item.Destroy()
        self.main_sizer.Layout()

    def clear(self):
        """Clears all the items in the container.
        """
        self.Freeze()
        for index in reversed(range(len(self.main_sizer.Children))):
            self.remove(index)
        self.Thaw()


class ScrollableContainerItem(wx.Panel):
    """A base class for an item in a `ScrollableContainer`.
    """
    def get_index_in_sizer(self):
        """Returns the index of the `ScrollableContainerItem`
        in the `ScrollableContainer`.
        """
        # http://wxpython-users.1045709.n5.nabble.com/How-to-get-index-of-a-wx-Sizer-item-tp2324859p2324861.html
        sizer = self.GetContainingSizer()

        for index, child in enumerate(sizer.Children):
            if child.Window == self:
                return index

'''
class PreviewPanel(wx.Panel):
    """A panel with a media control that shows a preview of the rendered video.
    """
    def __init__(self, parent):
        """Creates a new `PreviewPanel`.
        """
        super().__init__(parent)
        #self.SetDoubleBuffered(True)
        

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.CENTER)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.media_ctrl, 1, wx.EXPAND, 0)

        self.SetSizerAndFit(self.main_sizer)
        self.media_ctrl.Load("temp\\9.mkv")
        self.Bind(wx.media.EVT_MEDIA_LOADED, lambda e: 1)#self.media_ctrl.Play())
        #self.media_ctrl.SetInitialSize()
'''

class TimelineItemViewer(wx.Dialog):
    """A dialog that lets the user view or edit a `TimelineItem`'s data, depending on
    the specified `mode`.
    """
    def __init__(self, parent, mode="view"):
        """Creates a new `TimelineItemViewer` with the specified `mode`.
        """
        super().__init__(parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.BackgroundColour = "White"

        self.mode = mode

        self.view_effect_button = wx.Button(self, label="View Effect Info")
        self.property_grid = wx.propgrid.PropertyGrid(self, style=wx.propgrid.PG_TOOLTIPS|wx.propgrid.PG_SPLITTER_AUTO_CENTER|wx.propgrid.PG_BOLD_MODIFIED)

        if self.mode == "view":
            self.Title = "Timeline Item Viewer"
            self.buttons_sizer = self.CreateButtonSizer(wx.OK)

        elif self.mode == "edit":
            self.Title = "Timeline Item Editor"
            self.buttons_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.view_effect_button, 0, wx.CENTER)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.property_grid, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.CENTER)
        self.main_sizer.AddSpacer(10)

        self.main_sizer.MinSize = constants.TIMELINE_ITEM_VIEWER_MIN_SIZE
        self.SetSizerAndFit(self.main_sizer)

        self.view_effect_button.Bind(wx.EVT_BUTTON, self.on_view_effect_info)

    def ShowModal(self):
        """Ends editing and shows the `TimelineItemViewer` modally.
        """
        # Values are checked by wxPython when the edit ends (usually by unfocusing).
        # This prevents, for example, changing an IntProperty to a very big number.
        # When ending the modal dialog, unchecked values are moved on and become a problem.
        self.property_grid.EndLabelEdit()
        return super().ShowModal()

    def fill(self, effect):
        """Fills the `TimelineItemViewer`'s property grid using the specified `effect`.
        """
        self.effect = effect
        self.properties = {"timeline_item": {}, "magic_values": {}}
        self.categories = []

        # Timeline Item
        timeline_item_category = self.property_grid.Append(wx.propgrid.PropertyCategory("Timeline Item"))

        label_property = self.property_grid.Append(UnemptyStringProperty("Label"))
        label_property.set_translated_value(effect.name)

        self.properties["timeline_item"]["label"] = label_property
        self.categories.append(timeline_item_category)

        # Magic Values
        if effect.controls:
            magic_values_category = self.property_grid.Append(wx.propgrid.PropertyCategory("Magic Values"))

            for control in effect.controls:
                if control.type in constants.EFFECT_CONTROL_ALLOWED_TYPES:
                    prop = self.property_grid.Append(globals()[control.type](control.name))
                    self.properties["magic_values"][control.magic_name] = prop

            self.categories.append(magic_values_category)

        if self.mode == "view":
            for category in self.categories:
                category.Enable(False)

        self.property_grid.Layout()

    def load(self, timeline_item):
        """Calls `fill` with the `timeline_item`'s effect
        and loads the saved values into the property grid.
        """
        self.fill(timeline_item.effect)

        self.properties["timeline_item"]["label"].set_translated_value(timeline_item.label)

        for magic_name, prop in self.properties["magic_values"].items():
            try:
                prop.set_translated_value(timeline_item.magic_values[magic_name])
            except AttributeError:
                prop.m_value = timeline_item.magic_values[magic_name]

        self.property_grid.Layout()

    def get_magic_values(self):
        """Returns a dictionary of {magic_name:magic_value} generated from the property grid.
        """
        return {magic_name:
                (prop.get_translated_value() if hasattr(prop, "get_translated_value") else prop.m_value)
                for magic_name, prop in self.properties["magic_values"].items()}

    def get_label(self):
        """Returns the `TimelineItem`'s label selected by the user.
        """
        return self.properties["timeline_item"]["label"].get_translated_value()

    def on_view_effect_info(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the `View Effect Info` button is clicked.
        Shows an `EffectViewer` loaded with the `TimelineItem`'s effect.
        """
        EffectViewer(self, self.effect).ShowModal()


class HistoryItemViewer(wx.Dialog):
    """A dialog that shows a `HistoryItem`'s data.
    """
    def __init__(self, parent, history_item):
        """Creates a new `HistoryItemViewer loaded with the specified `history_item`.
        """
        super().__init__(parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, title="History Item Viewer")
        self.BackgroundColour = "White"
        self.SetDoubleBuffered(True)

        self.info_static_box_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Info")
        for key, value in history_item.kwargs.items():
            inner_sizer = wx.BoxSizer(wx.HORIZONTAL)
            inner_sizer.AddSpacer(10)
            inner_sizer.Add(wx.StaticText(self.info_static_box_sizer.StaticBox, label=key, style=wx.ST_ELLIPSIZE_END), 0, wx.ALIGN_LEFT)
            inner_sizer.AddStretchSpacer()
            inner_sizer.AddSpacer(20)

            if str(value.__class__) == "<class 'source.timeline.TimelineItem'>":  # Multiline
                button = BitmapButton("info.png", parent=self, size=(24, 24))
                button.callback_data = value
                button.Bind(wx.EVT_BUTTON, self.on_view_timeline_item)
                inner_sizer.Add(button, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            else:
                inner_sizer.Add(wx.StaticText(self.info_static_box_sizer.StaticBox, label=str(value), style=wx.ST_ELLIPSIZE_END), 0, wx.ALIGN_RIGHT)

            inner_sizer.AddSpacer(10)
            self.info_static_box_sizer.Add(inner_sizer, 0, wx.EXPAND)
            self.info_static_box_sizer.AddSpacer(10)
            self.info_static_box_sizer.Add(wx.StaticLine(self.info_static_box_sizer.StaticBox), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
            self.info_static_box_sizer.AddSpacer(10)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.MinSize = (500, 250)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.info_static_box_sizer, 0, wx.CENTER|wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        self.main_sizer.AddSpacer(10)

        self.SetSizerAndFit(self.main_sizer)

    def on_view_timeline_item(self, event):
        """Callback function - called when an `info` button
        that belongs to a `TimelineItem`-type attribute of the history item
        is clicked.
        Shows a `TimelineItemViewer` loaded with the `TimelineItem`.
        """
        timeline_item = event.EventObject.callback_data
        with TimelineItemViewer(self, mode="view") as timeline_item_viewer:
            timeline_item_viewer.load(timeline_item)
            timeline_item_viewer.ShowModal()


class UploadSettingsDialog(wx.Dialog):
    """A dialog that lets the user choose upload settings (video title, description, etc.)
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, title="Upload to Youtube - Video Options")
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.property_grid = wx.propgrid.PropertyGrid(self, style=wx.propgrid.PG_TOOLTIPS|wx.propgrid.PG_SPLITTER_AUTO_CENTER|wx.propgrid.PG_BOLD_MODIFIED)
        self.title_property = self.property_grid.Append(UnemptyStringProperty("Title", value="My Video"))
        self.description_property = self.property_grid.Append(LongStringProperty("Description", value="Created Using OceanFloor video editor"))
        self.category_property = self.property_grid.Append(EnumProperty("Category", labels=list(constants.YOUTUBE_CATEGORIES.keys())))
        self.tags_property = self.property_grid.Append(ArrayStringProperty("Tags"))
        self.privacy_status_property = self.property_grid.Append(EnumProperty("Privacy Status", labels=constants.YOUTUBE_PRIVACY_STATUSES))

        self.buttons_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)

        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.property_grid, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM)
        self.main_sizer.AddSpacer(10)

        self.main_sizer.MinSize = constants.UPLOAD_DIALOG_MIN_SIZE

        self.SetSizerAndFit(self.main_sizer)

    def get_upload_settings(self):
        """Returns a dictionary of the upload settings as {setting name: setting value}.
        """
        return {
            "title": self.title_property.m_value,
            "description": self.description_property.m_value,
            "category": constants.YOUTUBE_CATEGORIES[list(constants.YOUTUBE_CATEGORIES.keys())[self.category_property.m_value]],
            "tags": self.tags_property.m_value,
            "privacy_status": constants.YOUTUBE_PRIVACY_STATUSES[self.privacy_status_property.m_value].lower()
        }


class ClientSecretsFileNotFoundDialog(wx.MessageDialog):
    """A message dialog that shows an error message regarding a not found client secrets file.
    """
    def __init__(self, parent):
        """Creates a new `ClientSecretsFileNotFoundDialog`.
        """
        super().__init__(parent, "Client secrets file not found.\nFor details on how to obtain a client secrets file, please refer to the user guide.",
                         "Client Secrets File Not Found", style=wx.ICON_ERROR|wx.OK)


class SecretsFileDialog(wx.Dialog):
    """A dialog that prompts the user for a secrets file.
    """
    def __init__(self, parent):
        """Creates a new `SecretsFileDialog`.
        """
        super().__init__(parent, title="Upload to Youtube - Select Client Secrets File")

        self.static_text = wx.StaticText(self, label="Select the client secrets file:")
        self.file_picker_ctrl = wx.FilePickerCtrl(self, wildcard="Client Secrets File (*.json)|*.json")
        self.info_hyperlink = wx.adv.HyperlinkCtrl(self, label="Click here for more information.", url=auth_url)
        self.buttons_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.static_text, 0, wx.CENTER, 0)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.file_picker_ctrl, 0, wx.CENTER, 0)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.info_hyperlink, 0, wx.CENTER|wx.EXPAND, 0)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.CENTER|wx.ALIGN_BOTTOM, 0)
        self.main_sizer.AddSpacer(5)

        self.main_sizer.MinSize = constants.UPLOAD_DIALOG_MIN_SIZE

        self.SetSizerAndFit(self.main_sizer)

    def get_path(self):
        """Returns the selected secrets file's path
        """
        return self.file_picker_ctrl.Path


class YoutubeAuthorizationDialog(wx.Dialog):
    """A dialog that shows a clickable hyperlink generated using the secrets file,
    and prompts the user for the authorization code from the website at the link.
    """
    def __init__(self, parent, flow):
        """Creates a new `YoutubeAuthorizationDialog`.
        """
        super().__init__(parent, title="Upload to Youtube - Authorization")

        self.flow = flow
        self.flow.redirect_uri = self.flow._OOB_REDIRECT_URI
        auth_url, _ = self.flow.authorization_url()

        self.authorization_hyperlink = wx.adv.HyperlinkCtrl(self, label="Click here to authorize OceanFloor (opens a web browser)", url=auth_url)
        self.static_text = wx.StaticText(self, label="Paste the code from the authorization screen here:")
        self.code_text = wx.TextCtrl(self)
        self.buttons_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.authorization_hyperlink, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 10)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.static_text, 0, wx.CENTER, 0)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.code_text, 0, wx.CENTER|wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.CENTER|wx.ALIGN_BOTTOM, 0)
        self.main_sizer.AddSpacer(10)

        self.main_sizer.MinSize = constants.UPLOAD_DIALOG_MIN_SIZE

        self.SetSizerAndFit(self.main_sizer)

    def get_credentials(self):
        """Returns the credentials generated using the authorization code the user entered.
        """
        self.flow.fetch_token(code=self.code_text.Value)
        return self.flow.credentials


class YoutubeUploadSuccessDialog(wx.Dialog):
    def __init__(self, parent, video_id):
        super().__init__(parent, title="Success")
        self.BackgroundColour = "White"
        self.video_hyperlink = wx.adv.HyperlinkCtrl(self, label="Video uploaded successfully. Click to watch it on YouTube.", url=f"www.youtube.com/watch?v={video_id}")
        self.buttons_sizer = self.CreateButtonSizer(wx.OK)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.video_hyperlink, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.main_sizer.AddSpacer(10)

        self.SetSizerAndFit(self.main_sizer)

class AboutDialog(wx.MessageDialog):
    """A dialog that shows information about the program.
    """
    def __init__(self, parent):
        """Creates a new `AboutDialog`.
        """
        super().__init__(parent, message="Oceanfloor - Made by Ofir Ohad\n\n\nPowered by Python & FFMPEG", caption="About Oceanfloor", style=wx.OK|wx.ICON_INFORMATION)
