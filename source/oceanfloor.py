import bisect
import os
import pathlib
import random
import sqlite3
import subprocess
import threading
import time
import webbrowser

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import httplib2
import wx
import wx.adv
import wx.lib.scrolledpanel

from . import constants, environment, utils
from .classes import (AboutDialog, BitmapButton,
                      ClientSecretsFileNotFoundDialog, Effect,
                      HistoryItemViewer, InputOutputVideoPanel, MenuItem,
                      PluginsTree, TimelineItemViewer, UploadSettingsDialog,
                      YoutubeAuthorizationDialog, YoutubeUploadSuccessDialog,
                      show_error)
from .errors import ErrorContext, ErrorMessage, OceanFloorError
from .history import History, HistoryAction, HistoryItem, HistoryPanel
from .orm import ORM
from .timeline import Timeline, TimelineItem, TimelinePanel

#from wx.lib.inspection import InspectionTool


class OceanFloor(wx.Frame):
    """A subclass of wxPython's `wx.Frame`, which serves as the parent frame of the program.
    Only one object of this class is created, when the program is run.
    """
    def __init__(self):
        """Creates a new instance of `OceanFloor`.
        Does a `clean_start` and initiates the GUI using `init_gui`.
        """
        super().__init__(
            parent=None,
            title=constants.PROGRAM_TITLE,
            size=constants.WINDOW_SIZE)

        self.clean_start()
        self.init_gui()

    def clean_start(self):
        """Resets various attributes in order to bring the program
        back to a "clean", "brand new" state.
        """
        self.settings = None
        self.load_plugins()
        self.orm = ORM()
        self.input_video_path = None
        self.output_video_path = None
        self.timeline = Timeline()
        self.history = History()
        self.media_file_path = None
        self.dragged_item = None
        self.drag_delta = None
        self.dragged_item_initial_index = None

    def init_gui(self):
        """Initiates the GUI.
        """
        self.BackgroundColour = "White"
        self.init_menu_bar()
        self.main_panel = wx.Panel(self)

        # Boxes
        self.timeline_box = wx.StaticBox(self.main_panel, label="Timeline")
        self.input_video_panel = InputOutputVideoPanel(self.timeline_box)
        self.timeline_panel = TimelinePanel(self.timeline_box)
        self.output_video_panel = InputOutputVideoPanel(self.timeline_box)

        self.preview_box = wx.StaticBox(self.main_panel, label="Preview")
        #self.render_text = wx.StaticText(self.preview_box, label="Render to reflect changes.", pos=(20, 20))
        #self.render_text.Font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        #self.render_text.ForegroundColour = "Red"
        self.load_button = BitmapButton("load.png", parent=self.preview_box, size=(36, 36))
        self.reload_button = BitmapButton("reload.png", parent=self.preview_box, size=(36, 36))
        self.media_ctrl = wx.media.MediaCtrl(self.preview_box, style=wx.BORDER_DOUBLE, szBackend=wx.media.MEDIABACKEND_WMP10)
        self.media_ctrl.ShowPlayerControls()

        self.plugins_box = wx.StaticBox(self.main_panel, label="Plugins")
        self.plugins_tree = PluginsTree(self.plugins_box, self.effects)

        self.history_box = wx.StaticBox(self.main_panel, label="History")
        self.history_panel = HistoryPanel(self.history_box)

        # Sizing
        self.timeline_inner_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.timeline_inner_sizer.Add(self.input_video_panel, wx.SizerFlags().Align(wx.ALIGN_LEFT))
        self.timeline_inner_sizer.Add(self.timeline_panel, 1, wx.EXPAND)
        self.timeline_inner_sizer.Add(self.output_video_panel, wx.SizerFlags().Align(wx.ALIGN_RIGHT))

        self.preview_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.preview_buttons_sizer.AddStretchSpacer()
        self.preview_buttons_sizer.Add(self.load_button)
        self.preview_buttons_sizer.AddSpacer(2)
        self.preview_buttons_sizer.Add(self.reload_button)
        self.preview_buttons_sizer.AddStretchSpacer()

        self.timeline_box_sizer = wx.StaticBoxSizer(self.timeline_box)
        self.timeline_box_sizer.Add(self.timeline_inner_sizer, 1, wx.ALL^wx.TOP|wx.EXPAND, 5)

        self.preview_box_sizer = wx.StaticBoxSizer(self.preview_box, orient=wx.VERTICAL)
        self.preview_box_sizer.Add(self.preview_buttons_sizer, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        self.preview_box_sizer.AddSpacer(5)
        self.preview_box_sizer.Add(self.media_ctrl, 1, wx.EXPAND|wx.ALL^wx.TOP, 5)

        self.plugins_box_sizer = wx.StaticBoxSizer(self.plugins_box)
        self.plugins_box_sizer.Add(self.plugins_tree, 1, wx.ALL^wx.TOP|wx.EXPAND, 5)

        self.history_box_sizer = wx.StaticBoxSizer(self.history_box)
        self.history_box_sizer.Add(self.history_panel, 1, wx.ALL^wx.TOP|wx.EXPAND, 5)

        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_sizer.Add(self.plugins_box_sizer, 1, wx.EXPAND)
        self.right_sizer.AddSpacer(5)
        self.right_sizer.Add(self.history_box_sizer, 1, wx.EXPAND)

        self.bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_sizer.Add(self.preview_box_sizer, 2, wx.EXPAND)
        self.bottom_sizer.AddSpacer(5)
        self.bottom_sizer.Add(self.right_sizer, 1, wx.EXPAND)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.timeline_box_sizer, 0, wx.ALL^wx.BOTTOM|wx.EXPAND, 5)
        self.main_sizer.AddSpacer(5)
        self.main_sizer.Add(self.bottom_sizer, 1, wx.ALL^wx.TOP|wx.EXPAND, 5)

        self.main_panel.SetSizerAndFit(self.main_sizer)
        #self.main_panel.SetupScrolling()
        self.MinSize = constants.WINDOW_MIN_SIZE
        self.Show(True)

        self.input_video_panel.edit_button.Bind(wx.EVT_BUTTON, self.on_select_input_video)
        self.output_video_panel.edit_button.Bind(wx.EVT_BUTTON, self.on_select_output_video)
        self.media_ctrl.Bind(wx.media.EVT_MEDIA_LOADED, lambda e: self.media_ctrl.Pause())
        self.load_button.Bind(wx.EVT_BUTTON, self.on_load_media)
        self.reload_button.Bind(wx.EVT_BUTTON, self.on_reload_media)
        self.plugins_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_add_timeline_item)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        #InspectionTool().Show()
        #wx.CallAfter(YoutubeUploadSuccessDialog(self, "xrRTNG_5IF8").ShowModal)
        #YoutubeUploadSuccessDialog(self, "xrRTNG_5IF8").ShowModal()

    def init_menu_bar(self):
        """Initiates the menu bar.
        """
        menu_bar = wx.MenuBar()

        # file menu
        file_menu = wx.Menu()

        new_menu_item = MenuItem(id=wx.ID_NEW, bitmap_filename="new.png")
        open_menu_item = MenuItem(id=wx.ID_OPEN, bitmap_filename="open.png")
        save_menu_item = MenuItem(id=wx.ID_SAVE, bitmap_filename="save.png")
        render_menu_item = MenuItem(id=wx.ID_ANY, text="Render\tCtrl+Alt+R", bitmap_filename="render.png")
        youtube_menu_item = MenuItem(id=wx.ID_ANY, text="Upload to YouTube\tCtrl+Alt+Y", bitmap_filename="youtube.png")
        exit_menu_item = MenuItem(id=wx.ID_EXIT, bitmap_filename="exit.png")

        file_menu.Append(new_menu_item)
        file_menu.Append(open_menu_item)
        file_menu.AppendSeparator()
        file_menu.Append(save_menu_item)
        file_menu.Append(render_menu_item)
        file_menu.AppendSeparator()
        file_menu.Append(youtube_menu_item)
        file_menu.AppendSeparator()
        file_menu.Append(exit_menu_item)

        # edit menu
        edit_menu = wx.Menu()

        undo_menu_item = MenuItem(id=wx.ID_UNDO, bitmap_filename="undo.png")
        redo_menu_item = MenuItem(id=wx.ID_REDO, text="Redo\tCtrl+Y", bitmap_filename="redo.png")

        edit_menu.Append(undo_menu_item)
        edit_menu.Append(redo_menu_item)

        # help menu
        help_menu = wx.Menu()

        about_menu_item = MenuItem(id=wx.ID_ABOUT, bitmap_filename="about.png")
        documentation_menu_item = MenuItem(id=wx.ID_ANY, text="Documentation", bitmap_filename="documentation.png")

        help_menu.Append(about_menu_item)
        help_menu.Append(documentation_menu_item)

        menu_bar.Append(file_menu, "File")
        menu_bar.Append(edit_menu, "Edit")
        menu_bar.Append(help_menu, "Help")
        self.MenuBar = menu_bar

        self.Bind(wx.EVT_MENU, self.on_new, new_menu_item)
        self.Bind(wx.EVT_MENU, self.on_open, open_menu_item)
        self.Bind(wx.EVT_MENU, self.on_save, save_menu_item)
        self.Bind(wx.EVT_MENU, self.on_render, render_menu_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_menu_item)
        self.Bind(wx.EVT_MENU, self.on_undo, undo_menu_item)
        self.Bind(wx.EVT_MENU, self.on_redo, redo_menu_item)
        self.Bind(wx.EVT_MENU, self.on_documentation, documentation_menu_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_menu_item)
        self.Bind(wx.EVT_MENU, self.on_upload_to_youtube, youtube_menu_item)

    def _load_from_file(self, file_path):
        """Tries to load a save file into the program from the specified `file_path`.
        """
        self.orm.connect(file_path)

        # Try loading settings table
        try:
            settings = self.orm.load_settings()
        except sqlite3.OperationalError:
            show_error(OceanFloorError(ErrorMessage.SETTINGS_TABLE_NOT_FOUND), ErrorContext.LOAD_SAVE_FILE)
            return

        # Validate required settings exist
        for setting in constants.REQUIRED_SETTINGS:
            if setting not in settings:
                show_error(OceanFloorError(ErrorMessage.REQUIRED_SETTING_NOT_FOUND.format(setting)), ErrorContext.LOAD_SAVE_FILE)
                return

        # Validate input video exists
        input_video_path = settings["input_video_path"]
        if input_video_path and not os.path.exists(input_video_path):
            show_error(OceanFloorError(ErrorMessage.INPUT_VIDEO_NOT_FOUND.format(input_video_path)), ErrorContext.LOAD_SAVE_FILE)
            return

        output_video_path = settings["output_video_path"]

        # Try loading timeline (timeline items & magic values)
        try:
            timeline_items = self.orm.load_timeline(self.effects)
        except OceanFloorError as load_timeline_error:
            show_error(load_timeline_error, ErrorContext.LOAD_SAVE_FILE)
            return

        # Everything loaded successfully
        self.settings = settings
        self.input_video_path = input_video_path
        self.output_video_path = output_video_path

        self.timeline_panel.Freeze()
        for timeline_item in timeline_items:
            self._add_timeline_item(timeline_item)
        self.timeline_panel.Thaw()

        self.input_video_panel.set_path(self.input_video_path if self.input_video_path else "\\")
        self.output_video_panel.set_path(self.output_video_path if self.output_video_path else "\\")

    def load_plugins(self):
        """Loads the installed plugins to the `effects`
        {(plugin_name, effect_filename):`Effect` object} dictionary.
        """
        self.effects = {}

        # Scan the plugins directory for potential plugins
        for potential_plugin in os.scandir(environment.PLUGINS_PATH):
            if potential_plugin.is_dir:
                try:
                    effects_directory = pathlib.Path(potential_plugin.path) / "effects"
                except WindowsError:
                    show_error(OceanFloorError(ErrorMessage.EFFECTS_FOLDER_NOT_FOUND.format(potential_plugin.name)), ErrorContext.LOAD_PLUGINS)
                    continue

                # Scan the plugin directory for potential effects
                for potential_effect in os.scandir(effects_directory):
                    if potential_effect.name.endswith(".json"):
                        try:
                            plugin_name, effect_filename = potential_plugin.name, potential_effect.name
                            self.effects[(plugin_name, effect_filename)] = Effect(plugin_name, effect_filename)
                            # TODO: Check type of parameters
                        except OceanFloorError as load_effects_error:
                            show_error(load_effects_error, ErrorContext.LOAD_EFFECT_FILE)
                            continue

    def unsaved_changes(self):
        """Checks if there are unsaved changes.
        """
        return self.history.unsaved_changes()

    def _new(self):
        """Shows a file dialog that asks the user for a location for the new save file,
        and upon confirmation, creates the file by calling the orm's `create` method.
        """
        if not self.orm.is_connected():  # First run, input and / or output video paths were intentionally selected and are not a left over
            if self.input_video_path:
                self.input_video_panel.set_path(self.input_video_path)
            else:
                self.input_video_panel.set_path("\\")
            if self.output_video_path:
                self.output_video_panel.set_path(self.output_video_path)
            else:
                self.output_video_panel.set_path("\\")
        else:
            self.input_video_panel.set_path("\\")
            self.output_video_panel.set_path("\\")

        wildcard = "OceanFloor Project Files (*.oceanfloor)|*.oceanfloor"
        with wx.FileDialog(self, "Select a filename for the project", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as file_dialog:
            modal_result = file_dialog.ShowModal()
            path = file_dialog.Path

        if modal_result == wx.ID_OK:
            self.orm.create(path)

        self._update_save_status()

    def _open(self):
        """Shows a file dialog that asks the user for the save file to open,
        and upon confirmation, opens it by calling `_load_from_file`.
        """
        self.input_video_panel.set_path("\\")
        self.output_video_panel.set_path("\\")

        wildcard = "OceanFloor Project Files (*.oceanfloor)|*.oceanfloor"
        with wx.FileDialog(self, "Select an OceanFloor project", wildcard=wildcard, style=wx.FD_FILE_MUST_EXIST) as file_dialog:
            modal_result = file_dialog.ShowModal()
            path = file_dialog.Path

        if modal_result == wx.ID_OK:
            self._load_from_file(path)

        self._update_save_status()

    def _save(self):
        """If no file is open, calls `_new`, otherwise saves the pending changes to the save file.
        """
        if not self.orm.is_connected():
            self._new()

        if self.orm.is_connected():  # Can still be not connected if self._new() didn't go through
            self.history.save(self.orm)
            self.orm.set_input_video_path(self.input_video_path)
            self.orm.set_output_video_path(self.output_video_path)

        self._update_save_status()

    def _render(self, render_dialog):
        """Renders the video using a renderlist generated by `utils.generate_renderlist`,
        while updating the `render_dialog` on every step.
        """
        input_video_extension = os.path.splitext(self.input_video_path)[-1]
        temp_filename_1, temp_filename_2 = utils.generate_temp_filenames(2, input_video_extension)

        try:
            renderlist = utils.generate_renderlist(self.timeline, self.input_video_path, self.output_video_path, temp_filename_1, temp_filename_2)
            for percentage, action, popenargs in renderlist:
                wx.CallAfter(render_dialog.Update, percentage, action + "...")
                if subprocess.run(popenargs).returncode != 0:
                    raise OceanFloorError(ErrorMessage.FFMPEG_ERROR.format(f"while {action}"))
            wx.CallAfter(wx.MessageDialog(self, f"Done - Video Saved as \"{self.output_video_path}\"", "Done").ShowModal)
        except OceanFloorError as render_error:
            wx.CallAfter(show_error, render_error, ErrorContext.RENDER)
        finally:
            wx.CallAfter(render_dialog.Destroy)
            for filename in [temp_filename_1, temp_filename_2]:
                try:
                    os.remove(filename)
                except FileNotFoundError:
                    pass

        self._update_save_status()

    def _upload_to_youtube1(self, upload_progress_dialog, options, credentials, message_callback):
        """Uploads the ouput video to youtube, using the specified `options` and `credentials`.
        """
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": options["title"],
                "description": options["description"],
                "tags": options["tags"],
                "categoryId": options["category"]
            },
            "status": {
                "privacyStatus": options["privacy_status"]
            }
        }

        media_body = googleapiclient.http.MediaFileUpload(self.output_video_path, chunksize=constants.YOUTUBE_UPLOAD_CHUNKSIZE, resumable=True)
        insert_request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media_body)

        # Explicitly tell the underlying HTTP transport library not to retry, since
        # we are handling retry logic ourselves.
        httplib2.RETRIES = 1

        response = None
        error = None
        retry = 0
        chunk = 0
        filesize = os.path.getsize(self.output_video_path)

        while not response:
            try:
                message_callback("Uploading file...")
                status, response = insert_request.next_chunk()
                percentage = int(utils.calculate_percentage(chunk * constants.YOUTUBE_UPLOAD_CHUNKSIZE, filesize))
                print(f"Chunk: {chunk}")
                if response:
                    if "id" in response:
                        message_callback("Video id {} was successfully uploaded.".format(response["id"]))
                    else:
                        exit(f"The upload failed with an unexpected response: {response}")

                chunk += 1
            except googleapiclient.errors.HttpError as http_error:
                if http_error.resp.status in constants.YOUTUBE_UPLOAD_RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {http_error.resp.status} occurred:\n{http_error.content}"
                    print(error)
                else:
                    raise
            except constants.YOUTUBE_UPLOAD_RETRIABLE_EXCEPTIONS as retriable_exception:
                error = f"A retriable error occurred: {retriable_exception}"
                print(error)

            if error:
                message_callback(error)
                retry += 1
                if retry > constants.YOUTUBE_UPLOAD_MAX_RETRIES:
                    exit("No longer attempting to retry.")

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                message_callback(f"Sleeping {sleep_seconds} seconds and then retrying...")
                time.sleep(sleep_seconds)

    def _upload_to_youtube(self, options, credentials, upload_dialog):
        #youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": options["title"],
                "description": options["description"],
                "tags": options["tags"],
                "categoryId": options["category"]
            },
            "status": {
                "privacyStatus": options["privacy_status"]
            }
        }

        #media_body = googleapiclient.http.MediaFileUpload(self.output_video_path, chunksize=constants.YOUTUBE_UPLOAD_CHUNKSIZE, resumable=True)
        #insert_request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media_body)

        #filesize = os.path.getsize(self.output_video_path)

        retry = 0
        chunk = 0

        while True:
            retriable_error = None
            percentage = int(utils.calculate_percentage(chunk * constants.YOUTUBE_UPLOAD_CHUNKSIZE, filesize))
            if retry == 0:
                message = f"Uploading... {percentage}%"
            else:
                message = f"Uploading... {percentage}% (Retry #{retry})"
            wx.CallAfter(upload_dialog.Update, percentage, message)

            try:
                status, response = insert_request.next_chunk()
                chunk += 1  # Chunk uploaded successfully: update chunk counter
                retry = 0  # Reset retry counter
                if response:
                    try:
                        video_id = response["id"]  # Video uploaded successfully
                        result = (True, video_id)
                    except IndexError:
                        result = (False, f"The upload failed with an unexpected response: {response}")
                    break
            except googleapiclient.errors.HttpError as http_error:
                if http_error.resp.status in constants.YOUTUBE_UPLOAD_RETRIABLE_STATUS_CODES:
                    retriable_error = f"A retriable HTTP error {http_error.resp.status} occurred:\n{http_error.content}"
                else:
                    result = (False, ErrorMessage.NON_RETRIABLE_HTTP_ERROR.format(http_error.resp.status, http_error.content))
                    break
            except constants.YOUTUBE_UPLOAD_RETRIABLE_EXCEPTIONS as retriable_exception:
                retriable_error = f"A retriable error occurred: {retriable_exception}"
            except:
                result = (False, ErrorMessage.UNKNOWN_ERROR)
                break

            if retriable_error:
                retry += 1
                if retry > constants.YOUTUBE_UPLOAD_MAX_RETRIES:
                    result = (False, ErrorMessage.RETRY_LIMIT_EXCEEDED)
                    break
                wx.CallAfter(upload_dialog.Update, upload_dialog.Value, retriable_error + "\nWaiting 5 seconds to retry...")
                time.sleep(5)

        wx.CallAfter(self._upload_to_youtube_done, result, upload_dialog)

    def _upload_to_youtube_done(self, result, upload_dialog):
        if result[0]:  # Success
            with YoutubeUploadSuccessDialog(self, result[1]) as success_dialog:
                success_dialog.ShowModal()
        else:  # Failure
            show_error(result[1], ErrorContext.UPLOAD)
        upload_dialog.Destroy()

    def _exit(self):
        """Exits the program.
        """
        self.Close(True)

    def _undo(self):
        """If there is a history item that can be undone, undoes it both logically and visually.
        """
        history_item = self.history.undo()
        if not history_item:
            return

        self.history_panel.undo()

        if history_item.action == HistoryAction.APPEND_TIMELINE_ITEM:
            self._undo_add_timeline_item()

        #elif history_item.action == HistoryAction.INSERT_TIMELINE_ITEM:
        #    self._undo_insert_timeline_item(history_item.index)

        elif history_item.action == HistoryAction.REMOVE_TIMELINE_ITEM:
            self._undo_remove_timeline_item(history_item.index, history_item.timeline_item)

        elif history_item.action == HistoryAction.EDIT_TIMELINE_ITEM:
            self._undo_edit_timeline_item(history_item.index, history_item.original_timeline_item)

        elif history_item.action == HistoryAction.MOVE_TIMELINE_ITEM:
            self._undo_move_timeline_item(history_item.original_index, history_item.new_index)

        elif history_item.action == HistoryAction.SET_INPUT_VIDEO_PATH:
            self._undo_set_input_video_path(history_item)

        elif history_item.action == HistoryAction.SET_OUTPUT_VIDEO_PATH:
            self._undo_set_output_video_path(history_item)

        self.Layout()

        self._update_save_status()

    def _redo(self):
        """If there is a history item that can be redone, undoes it both logically and visually.
        """
        history_item = self.history.redo()
        if not history_item:
            return

        self.history_panel.redo()

        if history_item.action == HistoryAction.APPEND_TIMELINE_ITEM:
            self._add_timeline_item(history_item.timeline_item)

        #elif history_item.action == HistoryAction.INSERT_TIMELINE_ITEM:
        #    self._insert_timeline_item(history_item.index)

        elif history_item.action == HistoryAction.REMOVE_TIMELINE_ITEM:
            self._remove_timeline_item(history_item.index)

        elif history_item.action == HistoryAction.EDIT_TIMELINE_ITEM:
            self._edit_timeline_item(history_item.index, history_item.new_timeline_item)

        elif history_item.action == HistoryAction.MOVE_TIMELINE_ITEM:
            timeline_item_panel = self.timeline_panel.main_sizer.Children[history_item.original_index].Window
            self.timeline_panel.effects_sizer.Detach(timeline_item_panel)
            self.timeline_panel.main_sizer.Insert(history_item.new_index, timeline_item_panel)

            self.timeline_panel.main_sizer.Layout()

            self._move_timeline_item(history_item.original_index, history_item.new_index)

        elif history_item.action == HistoryAction.SET_INPUT_VIDEO_PATH:
            self._set_input_video_path(history_item)

        elif history_item.action == HistoryAction.SET_OUTPUT_VIDEO_PATH:
            self._set_output_video_path(history_item)

        self._update_save_status()

    def _select_input_video(self):
        """Shows a file dialog that prompts the user for an input video,
        and upon confirmation, sets `OceanFloor.input_video_path` to it.
        Also updates the input video panel to reflect the new path.
        """
        with wx.FileDialog(self, "Select an input video", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as file_dialog:  # TODO: Add wildcard
            modal_result = file_dialog.ShowModal()
            path = file_dialog.Path
        if modal_result == wx.ID_OK:
            self.input_video_path = path
            self.input_video_panel.set_path(self.input_video_path)

    def _select_output_video(self):
        """Shows a file dialog that prompts the user for an output video,
        and upon confirmation, sets `OceanFloor.output_video_path` to it.
        Also updates the output video panel to reflect the new path.
        """
        with wx.FileDialog(self, "Select an output video", style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as file_dialog:  # TODO: Add wildcard
            modal_result = file_dialog.ShowModal()
            path = file_dialog.Path
        if modal_result == wx.ID_OK:
            self.output_video_path = path
            self.output_video_panel.set_path(self.output_video_path)

    def _update_save_status(self):
        """Sets the title of the program according to the save state:
        if there are unsaved changes, a black circle is shown in the title bar.
        """
        if self.unsaved_changes():
            self.Title = f"● {constants.PROGRAM_TITLE}"
        else:
            self.Title = constants.PROGRAM_TITLE

    def _add_timeline_item(self, timeline_item):
        """Adds the specified `timeline_item` to the `Timeline`.
        Also creates a `TimelineItemPanel` and adds it to the `TimelinePanel`.
        """
        timeline_item_panel = self.timeline_panel.append(timeline_item)
        timeline_item_panel.edit_button.Bind(wx.EVT_BUTTON, self.on_edit_timeline_item)
        timeline_item_panel.close_button.Bind(wx.EVT_BUTTON, self.on_remove_timeline_item)

        timeline_item_panel.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
        timeline_item_panel.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)
        self.timeline_panel.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
        self.timeline_panel.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)

        for child in timeline_item_panel.Children:
            child.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
            if not isinstance(child, wx.AnyButton):
                child.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)

        timeline_item_panel.drag_button.Bind(wx.EVT_LEFT_DOWN, self.on_drag_timeline_item_mouse_down)
        timeline_item_panel.drag_button.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
        timeline_item_panel.drag_button.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)

        self.timeline.append(timeline_item)
        self._update_save_status()

    def _edit_timeline_item(self, index, new_timeline_item):
        """Replaces the `TimelineItem` at the specified `index` with the given `new_timeline_item`.
        Also updates the corresponding `TimelineItemPanel` to reflect the change.
        """
        #print(timeline_item.magic_values)
        #print("3", new_magic_values, "", sep="\n")
        self.timeline.edit(index, new_timeline_item)
        # Need to update the timeline item panel
        timeline_item_panel = self.timeline_panel.main_sizer.Children[index].Window
        timeline_item_panel.set_label(new_timeline_item.label)
        self._update_save_status()

    def _remove_timeline_item(self, index):
        """Removes the `TimelineItem` at the specified `index` in the `Timeline`.
        Also removes the corresponding `TimelineItemPanel` from the `TimellinePanel`.
        """
        self.timeline.remove(index)

        self.timeline_panel.Freeze()
        self.timeline_panel.remove(index)
        self.timeline_panel.Thaw()
        self._update_save_status()

    def _move_timeline_item(self, original_index, new_index):
        """Moves the `TimelineItem` at the specified `original_index` in the `Timeline`
        to the specified `new_index`.
        """
        self.timeline.move(original_index, new_index)
        self._update_save_status()

    def _undo_add_timeline_item(self):
        """Undoes an addition of a `TimelineItem`, by removing it.
        """
        index = len(self.timeline.items) - 1  # Last item
        self._remove_timeline_item(index)

    def _undo_edit_timeline_item(self, index, original_timeline_item):
        """Undoes an edit of a the `TimelineItem` at the specified `index` in the `Timeline`,
        by replacing it back with the `original_timeline_item`.
        """
        self._edit_timeline_item(index, original_timeline_item)

    def _undo_remove_timeline_item(self, index, timeline_item):
        """Undoes a removal of the specified `timeline_item`,
        by inserting it back to the `Timeline` at the specified `index`.
        """
        timeline_item_panel = self.timeline_panel.insert(index, timeline_item)
        self.timeline.insert(index, timeline_item)

        timeline_item_panel.edit_button.Bind(wx.EVT_BUTTON, self.on_edit_timeline_item)
        timeline_item_panel.close_button.Bind(wx.EVT_BUTTON, self.on_remove_timeline_item)

        timeline_item_panel.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
        timeline_item_panel.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)
        self.timeline_panel.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
        self.timeline_panel.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)

        for child in timeline_item_panel.Children:
            child.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
            if not isinstance(child, wx.AnyButton):
                child.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)

        timeline_item_panel.drag_button.Bind(wx.EVT_LEFT_DOWN, self.on_drag_timeline_item_mouse_down)
        timeline_item_panel.drag_button.Bind(wx.EVT_MOTION, self.on_drag_timeline_item_mouse_move)
        timeline_item_panel.drag_button.Bind(wx.EVT_LEFT_UP, self.on_drag_timeline_item_mouse_up)

    def _undo_move_timeline_item(self, original_index, new_index):
        """Undoes a move of a `TimelineItem`,
        by moving it back from the `new_index` in the `Timeline` to the `original_index`.
        """
        timeline_item_panel = self.timeline_panel.main_sizer.Children[new_index].Window
        self.timeline_panel.effects_sizer.Detach(timeline_item_panel)
        self.timeline_panel.main_sizer.Insert(original_index, timeline_item_panel)

        self.timeline_panel.main_sizer.Layout()

        self._move_timeline_item(new_index, original_index)

    def on_close(self, event):
        """Callback function - called when the X button is clicked.
        """
        if event.CanVeto() and self.unsaved_changes():
            if self.orm.is_connected():
                message_dialog = wx.MessageDialog(self, f"Save changes to file {self.orm.save_file}?", caption="Unsaved Changes", style=wx.YES_NO)
            else:
                message_dialog = wx.MessageDialog(self, f"Save changes to a new file?", caption="Unsaved Changes", style=wx.YES_NO)

            choice = message_dialog.ShowModal()
            if choice == wx.ID_YES:
                self._save()
            elif choice == wx.ID_NO:
                pass
            else:
                event.Veto()
                return

        event.Skip()

    def on_new(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "New" menu item is clicked.
        If there are unsaved changes, asks the user if the program should continue anyway;
        else clears the timeline and history panels, does a `clean_start` and calls `_new`.
        """
        if self.unsaved_changes():
            if self.orm.is_connected():
                message_dialog = wx.MessageDialog(self, f"Save changes to file {self.orm.save_file}?", caption="Unsaved Changes", style=wx.YES_NO)
            else:
                message_dialog = wx.MessageDialog(self, f"Save changes to a new file?", caption="Unsaved Changes", style=wx.YES_NO)

            choice = message_dialog.ShowModal()
            if choice == wx.ID_YES:
                self._save()
            elif choice == wx.ID_NO:
                pass
            else:
                return

        self.timeline_panel.clear()
        self.history_panel.clear()

        self.clean_start()
        self._new()

    def on_open(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Open" menu item is clicked.
        If there are unsaved changes, asks the user if the program should continue anyway;
        else clears the timeline and history panels, does a `clean_start` and calls `_open`.
        """
        if self.unsaved_changes():
            if self.orm.is_connected():
                message_dialog = wx.MessageDialog(self, f"Save changes to file {self.orm.save_file}?", caption="Unsaved Changes", style=wx.YES_NO)
            else:
                message_dialog = wx.MessageDialog(self, f"Save changes to a new file?", caption="Unsaved Changes", style=wx.YES_NO)

            choice = message_dialog.ShowModal()
            if choice == wx.ID_YES:
                self._save()
            elif choice == wx.ID_NO:
                pass
            else:
                return

        self.timeline_panel.clear()
        self.history_panel.clear()

        self.clean_start()
        self._open()

    def on_save(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Save" menu item is clicked.
        Calls `_save`.
        """
        self._save()

    def on_render(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Render" menu item is clicked.
        If the input and output videos are not selected, shows a dialog requesting them to be;
        else calls `_save`, shows a progress dialog, and calls `_render` on a separate thread.
        """
        if self.input_video_path and self.output_video_path:
            self._save()
            render_dialog = wx.GenericProgressDialog("Rendering Video", "", 100, self)
            threading.Thread(target=self._render, args=(render_dialog,)).start()

        else:
            wx.MessageDialog(self, message="Please select input & output video paths.", caption="Input & Output video paths", style=wx.OK).ShowModal()

    def on_upload_to_youtube(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Upload to YouTube" menu item is clicked.
        If the `client_secrets.json` file is found, shows an `UploadSettingsDialog`,
        and upon confirmation of the args, attempts to authorize the user
        using the `client_secrets.json` file and a `YoutubeAuthorizationDialog`.
        On success, creates a progress dialog and calls
        `_upload_to_youtube` on a separate thread.
        """
        if not os.path.isfile(constants.YOUTUBE_API_CLIENT_SECRETS_FILE):
            with ClientSecretsFileNotFoundDialog(self) as not_found_dialog:
                not_found_dialog.ShowModal()
            return

        with UploadSettingsDialog(self) as upload_settings_dialog:
            modal_result = upload_settings_dialog.ShowModal()
            upload_settings = upload_settings_dialog.get_upload_settings()

        if modal_result == wx.ID_OK:
            upload_progress_dialog = wx.ProgressDialog("Uploading Video", "", 100, self, style=wx.PD_ELAPSED_TIME|wx.PD_ESTIMATED_TIME|wx.PD_REMAINING_TIME)
            try:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    constants.YOUTUBE_API_CLIENT_SECRETS_FILE,
                    ["https://www.googleapis.com/auth/youtube.upload"]
                )
            except FileNotFoundError:
                with ClientSecretsFileNotFoundDialog(self) as not_found_dialog:
                    not_found_dialog.ShowModal()
                    return
            try:
                with YoutubeAuthorizationDialog(self, flow) as youtube_authorization_dialog:
                    modal_result = youtube_authorization_dialog.ShowModal()
                    credentials = youtube_authorization_dialog.get_credentials()

                if modal_result == wx.ID_OK:
                    threading.Thread(target=self._upload_to_youtube, args=(upload_settings, credentials, upload_progress_dialog)).start()

            except googleapiclient.errors.HttpError as http_error:
                upload_progress_dialog.Destroy()
                show_error(OceanFloorError(ErrorMessage.HTTP_ERROR.format(http_error.resp.status, http_error.content)), ErrorContext.UPLOAD)

    def on_exit(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Exit" menu item is clicked.
        Calls `_exit` if all changes are saved, else prompts the user to save them first.
        """
        if self.unsaved_changes():
            if self.orm.is_connected():
                message_dialog = wx.MessageDialog(self, f"Save changes to file {self.orm.save_file}?", caption="Unsaved Changes", style=wx.YES_NO)
            else:
                message_dialog = wx.MessageDialog(self, f"Save changes to a new file?", caption="Unsaved Changes", style=wx.YES_NO)

            choice = message_dialog.ShowModal()
            if choice == wx.ID_YES:
                self._save()
            elif choice == wx.ID_NO:
                pass
            else:
                return

        self._exit()

    def on_undo(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Undo" menu item is clicked,
        or when the associated shortcut is activated.
        Calls `_undo`.
        """
        self._undo()

    def on_redo(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Redo" menu item is clicked,
        or when the associated shortcut is activated.
        Calls `_redo`.
        """
        self._redo()

    def on_documentation(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "Documentation" menu item is clicked.
        Opens the documentation in a web browser.
        """
        webbrowser.open(constants.DOCUMENTATION_URL)

    def on_about(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the "About" menu item is clicked.
        Shows an `AboutDialog`."""
        AboutDialog(self).ShowModal()

    def on_select_input_video(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the `edit_button` on the input video panel (of type InputOutputVideoPanel) is clicked.
        Calls `_select_input_video`.
        """
        self._select_input_video()

    def on_select_output_video(self, event):  # pylint: disable=unused-argument
        """Callback function - called when the `edit_button` on the output video panel (of type InputOutputVideoPanel) is clicked.
        Calls `_select_output_video`.
        """
        self._select_output_video()

    def on_add_timeline_item(self, event):
        """Callback function - called when an item on the `PluginsTree` is activated.
        Shows a `TimelineItemViewer` loaded with the effect, and upon confirmation of the magic values,
        calls `_add_timeline_item`.
        """
        plugins_tree = event.EventObject
        effect = plugins_tree.get_selected_effect()

        if effect:
            with TimelineItemViewer(self, mode="edit") as timeline_item_viewer:
                timeline_item_viewer.fill(effect)
                timeline_item_viewer.Center()
                modal_result = timeline_item_viewer.ShowModal()
                label = timeline_item_viewer.get_label()
                magic_values = timeline_item_viewer.get_magic_values()

            if modal_result != wx.ID_OK:
                return

            timeline_item = TimelineItem(effect, label, magic_values)
            self._add_timeline_item(timeline_item)

            history_item = HistoryItem(action=HistoryAction.APPEND_TIMELINE_ITEM, timeline_item=timeline_item)
            self.history.record(history_item)
            history_item_panel = self.history_panel.record("Append", timeline_item.label)
            history_item_panel.info_button.Bind(wx.EVT_BUTTON, self.on_history_item_panel_info)

    def on_edit_timeline_item(self, event):
        """Callback function - called when a timeline item's `edit_button` is clicked.
        Calls `_edit_timeline_item`.
        """
        timeline_item_panel = event.EventObject.callback_data

        index = timeline_item_panel.get_index_in_sizer()
        timeline_item = self.timeline.items[index]

        with TimelineItemViewer(self, mode="edit") as timeline_item_viewer:
            timeline_item_viewer.load(timeline_item)
            timeline_item_viewer.Center()
            modal_result = timeline_item_viewer.ShowModal()
            new_label = timeline_item_viewer.get_label()
            new_magic_values = timeline_item_viewer.get_magic_values()

        if modal_result == wx.ID_OK:
            original_label = timeline_item.label
            original_magic_values = timeline_item.magic_values
            #print("4", new_magic_values, "", sep="\n")
            if original_label != new_label or original_magic_values != new_magic_values:
                new_timeline_item = TimelineItem(timeline_item.effect, new_label, new_magic_values)

                self._edit_timeline_item(index, new_timeline_item)

                history_item = HistoryItem(action=HistoryAction.EDIT_TIMELINE_ITEM,
                                           index=index,
                                           original_timeline_item=timeline_item,
                                           new_timeline_item=new_timeline_item)
                self.history.record(history_item)
                history_item_panel = self.history_panel.record("Edit", timeline_item.label)
                history_item_panel.info_button.Bind(wx.EVT_BUTTON, self.on_history_item_panel_info)

    def on_remove_timeline_item(self, event):
        """Callback function - called when a timeline item's `close_button` is clicked.
        Prompts a dialog to confirm removal of the timeline item, and upon approval, calls `_remove_timeline_item`.
        """
        message_dialog = wx.MessageDialog(self, "Are you sure you want to remove this timeline item?", caption="Remove Timeline item", style=wx.YES_NO)
        if message_dialog.ShowModal() != wx.ID_YES:
            return

        timeline_item_panel = event.EventObject.callback_data
        index = timeline_item_panel.get_index_in_sizer()

        timeline_item = self.timeline.items[index]

        self._remove_timeline_item(index)

        history_item = HistoryItem(action=HistoryAction.REMOVE_TIMELINE_ITEM, timeline_item=timeline_item, index=index)
        self.history.record(history_item)
        history_item_panel = self.history_panel.record("Remove", timeline_item.label)
        history_item_panel.info_button.Bind(wx.EVT_BUTTON, self.on_history_item_panel_info)

    def on_drag_timeline_item_mouse_down(self, event):
        """Callback function - called when a timeline item is in the process of being dragged - specifically, when the mouse is first down.
        Sets parameters required for the dragging to take effect: the item that is being dragged, its initial index in the timeline, and the drag delta.
        """
        self.dragged_item = event.EventObject.callback_data
        self.dragged_item_initial_index = self.dragged_item.get_index_in_sizer()
        self.drag_delta = self.dragged_item.Position.x - wx.GetMousePosition().x, self.dragged_item.Position.y - wx.GetMousePosition().y

    def on_drag_timeline_item_mouse_move(self, event):  # pylint: disable=unused-argument
        """Callback function - called when a timeline item is in the process of being dragged - specifically, when the mouse is moved.
        Moves the timeline item to the position of the mouse and raises it above the other timeline entries.
        """
        if self.dragged_item:
            self.dragged_item.Position = wx.GetMousePosition().x + self.drag_delta[0], self.dragged_item.Position.y  # Draggable along the horizontal axis only
            #self.dragged_item.SetPosition((wx.GetMousePosition().x + self.drag_delta[0], wx.GetMousePosition().y + self.drag_delta[1]))  # Draggable along both axes
            self.dragged_item.Raise()

    def on_drag_timeline_item_mouse_up(self, event):  # pylint: disable=unused-argument
        """Callback function - called when a timeline item is in the process of being dragged - specifically, when the mouse is released.
        Detaches the timeline item from the containing sizer, inserts it to the new index, sets the parameter that keeps track of the dragged item to None,
        and calls `_move_timeline_item` if the initial index is different than the new index.
        """
        if self.dragged_item:
            self.timeline_panel.effects_sizer.Detach(self.dragged_item)
            new_index = bisect.bisect_left([child.Window.Position.x for child in self.timeline_panel.effects_sizer.Children], self.dragged_item.Position.x)
            self.timeline_panel.effects_sizer.Insert(new_index, self.dragged_item)
            self.timeline_panel.effects_sizer.Layout()
            self.dragged_item = None

            original_index = self.dragged_item_initial_index
            timeline_item = self.timeline.items[original_index]
            if original_index != new_index:
                self._move_timeline_item(self.dragged_item_initial_index, new_index)

                history_item = HistoryItem(action=HistoryAction.MOVE_TIMELINE_ITEM, original_index=original_index, new_index=new_index, timeline_item=timeline_item)
                self.history.record(history_item)
                history_item_panel = self.history_panel.record("Move", timeline_item.label)
                history_item_panel.info_button.Bind(wx.EVT_BUTTON, self.on_history_item_panel_info)

    def on_history_item_panel_info(self, event):
        """Callback function - called when an `HistoryItemPanel`'s info button is clicked.
        Shows a `HistoryItemViewer` loaded with the corresponding `HistoryItem`.
        """
        history_item_panel = event.EventObject.callback_data
        index = history_item_panel.get_index_in_sizer()
        history_item = self.history.items[index]
        HistoryItemViewer(self, history_item).Show()

    def on_load_media(self, event):
        with wx.FileDialog(self, "Select a file to preview", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as file_dialog:
            modal_result = file_dialog.ShowModal()
            path = file_dialog.Path

        self.media_file_path = path
        self.media_ctrl.Load(path)

    def on_reload_media(self, event):
        if self.media_file_path:
            self.media_ctrl.Load(self.media_file_path)
