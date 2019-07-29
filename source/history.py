import enum

import wx

from . import constants
from .classes import ScrollableContainer, ScrollableContainerItem, BitmapButton


class History:
    def __init__(self):
        """Creates a new `History`.
        """
        self.items = []
        self.last_save_pointer = 0
        self.undo_pointer = 0

    def __str__(self):
        return str([x for x in self.items])

    def unsaved_changes(self):
        """Checks if there are any unsaved changes, by comparing the `last_save_pointer`
        to the `undo_pointer`.
        """
        return self.last_save_pointer != self.undo_pointer

    def record(self, item):
        """Records a `HistoryItem` in the `History`. Destroys any items that were undone,
        and updates the `undo_pointer`.
        """
        if self.undo_pointer != len(self.items):
            self.items = self.items[:self.undo_pointer]

        self.items.append(item)
        self.undo_pointer = len(self.items)

    def undo(self):
        """If there is a history item that can be undone, updates the `undo_pointer`,
        and returns the undone history item.
        """
        if self.undo_pointer > 0:
            self.undo_pointer -= 1
            return self.items[self.undo_pointer]

    def redo(self):
        """If there is a history item that can be redone, updates the `undo_pointer`,
        and returns the redone history item.
        """
        if self.undo_pointer < len(self.items):
            self.undo_pointer += 1
            return self.items[self.undo_pointer - 1]

    def save(self, orm):
        """Saves all pending changes to the open save file using the `ORM`.
        """
        # Save new changes
        if self.last_save_pointer < self.undo_pointer:
            for history_item in self.items[self.last_save_pointer:self.undo_pointer]:
                if history_item.action == HistoryAction.APPEND_TIMELINE_ITEM:
                    orm.append_timeline_item(history_item.timeline_item)

                elif history_item.action == HistoryAction.INSERT_TIMELINE_ITEM:
                    orm.insert_timeline_item(history_item.index, history_item.timeline_item)

                elif history_item.action == HistoryAction.REMOVE_TIMELINE_ITEM:
                    orm.remove_timeline_item(history_item.index)

                elif history_item.action == HistoryAction.EDIT_TIMELINE_ITEM:
                    orm.edit_timeline_item(history_item.index, history_item.new_timeline_item)

                elif history_item.action == HistoryAction.MOVE_TIMELINE_ITEM:
                    orm.move_timeline_item(history_item.original_index, history_item.new_index, history_item.timeline_item)

                elif history_item.action == HistoryAction.SET_INPUT_VIDEO_PATH:
                    orm.set_input_video_path(history_item.path)

                elif history_item.action == HistoryAction.SET_OUTPUT_VIDEO_PATH:
                    orm.set_output_video_path(history_item.path)

            self.last_save_pointer = self.undo_pointer

        # Save undo changes
        elif self.undo_pointer < self.last_save_pointer:
            for history_item in reversed(self.items[self.undo_pointer:self.last_save_pointer]):
                if history_item.action == HistoryAction.APPEND_TIMELINE_ITEM:
                    orm.undo_append_timeline_item()

                elif history_item.action == HistoryAction.INSERT_TIMELINE_ITEM:
                    orm.undo_insert_timeline_item(history_item.index)

                elif history_item.action == HistoryAction.REMOVE_TIMELINE_ITEM:
                    orm.undo_remove_timeline_item(history_item.index, history_item.timeline_item)

                elif history_item.action == HistoryAction.EDIT_TIMELINE_ITEM:
                    orm.undo_edit_timeline_item(history_item.index, history_item.original_timeline_item)

                elif history_item.action == HistoryAction.MOVE_TIMELINE_ITEM:
                    orm.undo_move_timeline_item(history_item.original_index, history_item.new_index, history_item.timeline_item)

                elif history_item.action == HistoryAction.SET_INPUT_VIDEO_PATH:
                    orm.undo_set_input_video_path(history_item)

                elif history_item.action == HistoryAction.SET_OUTPUT_VIDEO_PATH:
                    orm.undo_set_output_video_path(history_item)

            self.last_save_pointer = self.undo_pointer


class HistoryPanel(ScrollableContainer):
    def __init__(self, parent):
        """Creates a new `HistoryPanel`.
        """
        super().__init__(parent, orientation=wx.VERTICAL)
        self.BackgroundColour = (220, 220, 220)
        self.last_save_pointer = 0
        self.undo_pointer = 0

    def record(self, main_title, secondary_title):
        """Records a `HistoryItemPanel` in the `HistoryPanel` with the specified
        `main_title` and `secondary_title`.
        Destroys any items that were undone, and returns the `HistoryItemPanel`.
        """
        self.Freeze()
        if self.undo_pointer != len(self.main_sizer.Children):
            for child in list(self.main_sizer.Children)[self.undo_pointer:]:
                history_item_panel = child.Window
                self.main_sizer.Detach(history_item_panel)
                history_item_panel.Destroy()

        history_item_panel = HistoryItemPanel(self, main_title, secondary_title)
        super().append(history_item_panel)

        self.undo_pointer = len(self.main_sizer.Children)
        self.Thaw()

        return history_item_panel

    def undo(self):
        """If there is a history item that can be undone, updates the `undo_pointer`,
        and calls the history item panel's `undo` method.
        """
        if self.undo_pointer > 0:
            self.undo_pointer -= 1
            history_item_panel = self.main_sizer.Children[self.undo_pointer].Window
            history_item_panel.undo()

    def redo(self):
        """If there is a history item that can be redone, updates the `undo_pointer`,
        and calls the history item panel's `redo` method.
        """
        if self.undo_pointer < len(self.main_sizer.Children):
            history_item_panel = self.main_sizer.Children[self.undo_pointer].Window
            self.undo_pointer += 1
            history_item_panel.redo()


class HistoryItemPanel(ScrollableContainerItem):
    """A panel that represents a `HistoryItem`. Contained in a `HistoryPanel`.
    """
    def __init__(self, parent, main_title, secondary_title=""):
        """Creates a new `HistoryItemPanel` with the specifies `main_title` and `secondary_title`.
        """
        super().__init__(parent, style=wx.BORDER_DOUBLE)
        self.BackgroundColour = 180, 180, 180

        self.main_title_text = wx.StaticText(self, label=main_title, style=wx.ST_ELLIPSIZE_END|wx.ALIGN_CENTER_VERTICAL)
        self.main_title_text.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.main_title_text.ForegroundColour = "White"
        self.secondary_title_text = wx.StaticText(self, label=secondary_title, style=wx.ST_ELLIPSIZE_END|wx.ALIGN_CENTER_VERTICAL)
        self.secondary_title_text.Font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.secondary_title_text.ForegroundColour = "White"
        self.info_button = BitmapButton("info.png", parent=self, size=(24, 24))
        self.info_button.callback_data = self

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.MinSize = constants.HISTORY_ITEM_PANEL_SIZE
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.main_title_text, 0, wx.ALIGN_CENTER_VERTICAL)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.secondary_title_text, 0, wx.ALIGN_CENTER_VERTICAL)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.AddStretchSpacer()
        self.main_sizer.Add(self.info_button, 0, wx.ALIGN_CENTER_VERTICAL)
        self.main_sizer.AddSpacer(5)

        self.SetSizerAndFit(self.main_sizer)

    def undo(self):
        """Greys out the undone `HistoryItemPanel`.
        """
        self.Freeze()
        self.BackgroundColour = constants.UNDONE_COLOR
        self.main_title_text.ForegroundColour = (180, 180, 180)
        self.secondary_title_text.ForegroundColour = (180, 180, 180)
        self.Thaw()

    def redo(self):
        """Recolors the redone `HistoryItemPanel`.
        """
        self.Freeze()
        self.BackgroundColour = 180, 180, 180
        self.main_title_text.ForegroundColour = "White"
        self.secondary_title_text.ForegroundColour = "White"
        self.Thaw()


class HistoryAction(enum.Enum):
    """An enumeration of the possible actions that can be recorded in history.
    """
    APPEND_TIMELINE_ITEM = enum.auto()
    INSERT_TIMELINE_ITEM = enum.auto()
    REMOVE_TIMELINE_ITEM = enum.auto()
    EDIT_TIMELINE_ITEM = enum.auto()
    MOVE_TIMELINE_ITEM = enum.auto()
    SET_INPUT_VIDEO_PATH = enum.auto()
    SET_OUTPUT_VIDEO_PATH = enum.auto()


class HistoryItem:
    """An item in history.
    """
    def __init__(self, **kwargs):
        """Creates a new `HistoryItem` with the specified kwargs.
        """
        self.kwargs = kwargs

    def __getattr__(self, name):
        return self.kwargs[name]
