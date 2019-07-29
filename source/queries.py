CREATE_TIMELINE_TABLE = '''
CREATE TABLE timeline
(
  effect_id INTEGER PRIMARY KEY NOT NULL,
  effect_ordering INTEGER NOT NULL,
  effect_plugin TEXT NOT NULL,
  effect_filename TEXT NOT NULL,
  item_label TEXT NOT NULL
);
'''

CREATE_MAGIC_VALUES_TABLE = '''
CREATE TABLE magic_values
(
  effect_id INTEGER NOT NULL,
  magic_name TEXT NOT NULL,
  magic_value TEXT NOT NULL,
  FOREIGN KEY (effect_id) REFERENCES timeline (effect_id)
);
'''

CREATE_SETTINGS_TABLE = '''
CREATE TABLE settings
(
  setting_name TEXT PRIMARY KEY NOT NULL,
  setting_value TEXT
);
'''

SET_INPUT_VIDEO_PATH = '''
INSERT OR REPLACE INTO settings (setting_name, setting_value)
VALUES ("input_video_path", ?);
'''  # REPLACE: https://sqlite.org/lang_conflict.html

SET_OUTPUT_VIDEO_PATH = '''
INSERT OR REPLACE INTO settings (setting_name, setting_value)
VALUES ("output_video_path", ?);
'''  # REPLACE: https://sqlite.org/lang_conflict.html

LOAD_TIMELINE_TABLE = '''
SELECT * FROM timeline ORDER BY effect_ordering;
'''

LOAD_MAGIC_VALUES_TABLE = '''
SELECT * FROM magic_values WHERE effect_id = ?;
'''

LOAD_SETTINGS_TABLE = '''
SELECT * FROM settings;
'''

SAVE_CHANGE_APPEND_EFFECT = '''
INSERT INTO timeline (effect_id, effect_ordering, effect_plugin, effect_filename, item_label)
VALUES (
  (SELECT COALESCE(MAX(effect_id), -1) FROM timeline) + 1,
  (SELECT COALESCE(MAX(effect_ordering), -1) FROM timeline) + 1,
  ?, -- ? = plugin
  ?, -- ? = filename
  ? -- ? = label
);
'''

SAVE_CHANGE_INSERT_MAKE_PLACE = '''
UPDATE timeline SET effect_ordering = effect_ordering + 1
WHERE effect_ordering >= ?; -- index of insertion
'''

SAVE_CHANGE_INSERT_EFFECT = '''
INSERT INTO timeline (effect_id, effect_ordering, effect_plugin, effect_filename, item_label)
VALUES (
  (SELECT MAX(effect_id) FROM timeline) + 1,
  ?, -- ? = index of insertion
  ?, -- ? = plugin
  ?, -- ? = filename
  ? -- ? = label
);
'''

SAVE_CHANGE_SAVE_MAGIC_VALUES = '''
INSERT INTO magic_values (effect_id, magic_name, magic_value)
VALUES (
  (SELECT MAX(effect_id) FROM timeline),
  ?, -- ? = name
  ? -- ? = value
);
'''

SAVE_CHANGE_REPLACE_EFFECT = '''
UPDATE timeline SET
  plugin = ?,
  filename = ?
WHERE effect_ordering = ?;
'''

SAVE_CHANGE_REMOVE_MAGIC_VALUES = '''
DELETE FROM magic_values
WHERE effect_id = (
  SELECT MAX(effect_id)
  FROM timeline
  WHERE effect_ordering = ? -- ? = effect ordering
);
'''

SAVE_CHANGE_REMOVE_EFFECT = '''
DELETE FROM timeline
WHERE effect_ordering = ?; -- ? = effect ordering
'''

SAVE_CHANGE_REMOVE_EMPTY_PLACE = '''
UPDATE timeline SET
  effect_ordering = effect_ordering - 1
WHERE effect_ordering > ?; -- ? = effect ordering
'''

SAVE_CHANGE_UNDO_APPEND_EFFECT = '''
DELETE FROM timeline
WHERE effect_ordering = (
  SELECT MAX(effect_ordering)
  FROM timeline
);
'''

SAVE_CHANGE_UNDO_SAVE_MAGIC_VALUES = '''
DELETE FROM magic_values
WHERE effect_id = (
  SELECT MAX(effect_id)
  FROM timeline
  WHERE effect_ordering = (
    SELECT MAX(ordering) FROM timeline
  )
);
'''