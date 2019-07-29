import sqlite3

from . import queries
from .errors import ErrorMessage, OceanFloorError
from .timeline import TimelineItem


class ORM:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.save_file = None

    def create(self, file_path):
        with open(file_path, "w"):
            pass  # Empties the file

        self.connect(file_path)

        self.cursor.execute(queries.CREATE_TIMELINE_TABLE)
        self.cursor.execute(queries.CREATE_MAGIC_VALUES_TABLE)
        self.cursor.execute(queries.CREATE_SETTINGS_TABLE)
        self.set_input_video_path(None)
        self.set_output_video_path(None)

        self.connection.commit()

    def connect(self, save_file):
        self.connection = sqlite3.connect(save_file)
        self.cursor = self.connection.cursor()

        self.save_file = save_file

    def is_connected(self):
        return bool(self.connection)

    def load_settings(self):
        return {k: v for k, v in self.cursor.execute(queries.LOAD_SETTINGS_TABLE).fetchall()}

    def load_timeline(self, effects):
        # Try loading the timeline table
        try:
            timeline_raw_data = self.cursor.execute(queries.LOAD_TIMELINE_TABLE).fetchall()
        except sqlite3.OperationalError:
            raise OceanFloorError(ErrorMessage.TIMELINE_TABLE_NOT_FOUND)

        timeline_items = []

        for timeline_item_line in timeline_raw_data:
            effect_id, _, effect_plugin, effect_filename, item_label = timeline_item_line

            try:
                effect = effects[(effect_plugin, effect_filename)]
            except IndexError:
                raise OceanFloorError(ErrorMessage.EFFECT_NOT_RECOGNIZED.format(effect_filename, effect_plugin))

            # Try loading the magic values for the timeline item
            try:
                magic_values_raw_data = self.cursor.execute(queries.LOAD_MAGIC_VALUES_TABLE, (effect_id,)).fetchall()
            except sqlite3.OperationalError:
                raise OceanFloorError(ErrorMessage.MAGIC_VALUES_TABLE_NOT_FOUND)

            magic_values = {}

            for magic_value_line in magic_values_raw_data:
                _, magic_name, magic_value = magic_value_line
                magic_values[magic_name] = magic_value

            timeline_items.append(TimelineItem(effect, item_label, magic_values))

        return timeline_items

    def set_input_video_path(self, path):
        self.cursor.execute(queries.SET_INPUT_VIDEO_PATH, (path,))
        self.connection.commit()

    def set_output_video_path(self, path):
        self.cursor.execute(queries.SET_OUTPUT_VIDEO_PATH, (path,))
        self.connection.commit()

    def save_magic_values(self, magic_values):
        # Save magic values
        # It's okay to rely on them belonging to the timeline item with the highest effect ID
        # because they are never edited in place, they always belong to the last effect touched
        # (on insert, edit, append etc.)
        for magic_name, magic_value in magic_values.items():
            self.cursor.execute(queries.SAVE_CHANGE_SAVE_MAGIC_VALUES, (magic_name, magic_value))
            self.connection.commit()

    def append_timeline_item(self, timeline_item):
        # Append timeline item
        self.cursor.execute(queries.SAVE_CHANGE_APPEND_EFFECT, (timeline_item.effect.plugin_name, timeline_item.effect.effect_filename, timeline_item.label))
        self.connection.commit()
        # Save magic values
        self.save_magic_values(timeline_item.magic_values)

    def insert_timeline_item(self, index, timeline_item):
        # Make place for the insertion
        self.cursor.execute(queries.SAVE_CHANGE_INSERT_MAKE_PLACE, (index,))
        self.connection.commit()
        # Insert timeline item
        self.cursor.execute(queries.SAVE_CHANGE_INSERT_EFFECT, (index, timeline_item.effect.plugin_name, timeline_item.effect.effect_filename, timeline_item.label))
        self.connection.commit()
        # Save magic values
        self.save_magic_values(timeline_item.magic_values)

    def remove_timeline_item(self, index):
        # Remove magic values
        self.cursor.execute(queries.SAVE_CHANGE_REMOVE_MAGIC_VALUES, (index,))
        self.connection.commit()
        # Remove timeline item
        self.cursor.execute(queries.SAVE_CHANGE_REMOVE_EFFECT, (index,))
        self.connection.commit()
        # Eliminate the empty place
        self.cursor.execute(queries.SAVE_CHANGE_REMOVE_EMPTY_PLACE, (index,))
        self.connection.commit()

    def edit_timeline_item(self, index, new_timeline_item):
        # Edit = remove original -> insert new
        self.remove_timeline_item(index)
        self.insert_timeline_item(index, new_timeline_item)

    def move_timeline_item(self, original_index, new_index, timeline_item):
        # Move = remove at original_index, insert at new_index

        # Remove at original_index
        self.remove_timeline_item(original_index)
        # Insert at new_index
        self.insert_timeline_item(new_index, timeline_item)

    def undo_append_timeline_item(self):
        # Remove magic values
        self.cursor.execute(queries.SAVE_CHANGE_UNDO_SAVE_MAGIC_VALUES)
        self.connection.commit()
        # Remove timeline item
        self.cursor.execute(queries.SAVE_CHANGE_UNDO_APPEND_EFFECT)
        self.connection.commit()

    def undo_insert_timeline_item(self, index):
        # Undo insert = remove
        self.remove_timeline_item(index)

    def undo_remove_timeline_item(self, index, timeline_item):
        # Undo remove = insert
        self.insert_timeline_item(index, timeline_item)

    def undo_edit_timeline_item(self, index, original_timeline_item):
        # Undo edit = remove new -> insert original
        self.edit_timeline_item(index, original_timeline_item)

    def undo_move_timeline_item(self, original_index, new_index, timeline_item):
        # Undo move = move back
        self.move_timeline_item(new_index, original_index, timeline_item)
