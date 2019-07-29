import wx

from . import constants, environment, utils
from .classes import ScrollableContainer, ScrollableContainerItem, BitmapButton


class Timeline:
    """Creates a new `Timeline`."""
    def __init__(self):
        self.items = []

    """Appends `timeline_item` to the timeline."""
    def append(self, timeline_item):
        # append to the queue
        self.items.append(timeline_item)

    """Inserts `timeline_item` at the specified `index` in the timeline."""
    def insert(self, index, timeline_item):
        # insert to the queue
        self.items.insert(index, timeline_item)

    """Removes the `TimelineItem` at the specified `index` in the timeline,
    and returns it."""
    def remove(self, index):
        # remove from the queue
        removed = self.items.pop(index)

        return removed

    """Edits (replaces) the `TimelineItem` at the specified `index` in the timeline
    with `new_timeline_item`. Returns the original timeline item."""
    def edit(self, index, new_timeline_item):
        # remove the original timeline item from the queue
        original_timeline_item = self.items.pop(index)
        # insert the new timeline item to the queue
        self.items.insert(index, new_timeline_item)

        return original_timeline_item

    """Moves the `TimelineItem` at the `original_index` in the timeline
    to the `new_index` in the timeline. Returns the moved timeline item."""
    def move(self, original_index, new_index):
        # remove the timeline item from the original index in the queue
        moved = self.items.pop(original_index)
        # insert at the new index in the queue
        self.items.insert(new_index, moved)

        return moved


class TimelineItem:
    """An item in the timeline."""
    def __init__(self, effect, label, magic_values):
        """Creates a new `TimelineItem` with the specified `effect`, `label`
        and `magic_values`."""
        self.label = label
        self.effect = effect
        self.magic_values = magic_values


class TimelinePanel(ScrollableContainer):
    def __init__(self, parent):
        super().__init__(parent, orientation=wx.HORIZONTAL)
        self.BackgroundColour = (220, 220, 220)
        self.effects_sizer = self.main_sizer

    def append(self, timeline_item):
        timeline_item_panel = TimelineItemPanel(self, timeline_item)
        super().append(timeline_item_panel)

        return timeline_item_panel

    def insert(self, index, timeline_item):
        timeline_item_panel = TimelineItemPanel(self, timeline_item)
        super().insert(index, timeline_item_panel)

        return timeline_item_panel


class TimelineItemPanel(ScrollableContainerItem):
    def __init__(self, parent, timeline_item):
        super().__init__(parent, style=wx.BORDER_DOUBLE)
        self.BackgroundColour = utils.color_from_hex(timeline_item.effect.color)
        self.close_button = wx.BitmapButton.NewCloseButton(self, -1)
        self.close_button.callback_data = self

        self.label_text = wx.StaticText(self, label=timeline_item.label, style=wx.ST_ELLIPSIZE_END)
        self.label_text.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.label_text.MaxSize = [i - 20 for i in constants.TIMELINE_ITEM_PANEL_SIZE]

        self.static_line_left = wx.StaticLine(self)
        self.static_bitmap = wx.StaticBitmap(self, bitmap=timeline_item.effect.bitmap)
        self.static_line_right = wx.StaticLine(self)
        self.static_line_left.Size[1] = 1
        self.static_line_right.Size[1] = 1

        self.edit_button = BitmapButton("edit.png", parent=self, size=(24, 24))
        self.edit_button.callback_data = self
        self.drag_button = BitmapButton("drag.png", parent=self, size=(24, 24))
        self.drag_button.callback_data = self

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
        self.buttons_sizer.AddSpacer(2)
        self.buttons_sizer.Add(self.drag_button)
        self.buttons_sizer.AddStretchSpacer()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.MinSize = constants.TIMELINE_ITEM_PANEL_SIZE
        self.main_sizer.AddStretchSpacer()
        self.main_sizer.Add(self.label_text, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 5)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.bitmap_sizer, 0, wx.EXPAND, 0)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.buttons_sizer, 0, wx.CENTER, 0)
        self.main_sizer.AddStretchSpacer()

        self.SetSizerAndFit(self.main_sizer)

    def set_label(self, label):
        self.label_text.Label = label
        self.label_text.MaxSize = [i - 20 for i in constants.TIMELINE_ITEM_PANEL_SIZE]

        self.Layout()
