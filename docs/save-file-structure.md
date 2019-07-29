# The OceanFloor Save File Structure

OceanFloor save files (`*.oceanfloor`) are databases containing tables of the data necessary for loading the project back into an editable state. This document exhibits the structure of the save file, by showing the data tables and examples for information they may contain.

## Tables

### added_effects

The `added_effects` table stores the video effects and the order in which they were chosen by the user, which OceanFloor applies chronologically at render time using FFmpeg calls.

```sql
/* Example added_effects table */
+---------------------+---------------------------+----------------------+------------------------+
| effect_id (INTEGER) | effect_ordering (INTEGER) | effect_plugin (TEXT) | effect_filename (TEXT) |
+---------------------+---------------------------+----------------------+------------------------+
| 0                   | 0                         | "builtin"            | "ADD_VIDEO"            |
+---------------------+---------------------------+----------------------+------------------------+
| 3                   | 1                         | "builtin"            | "TEXT"                 |
+---------------------+---------------------------+----------------------+------------------------+
| 4                   | 2                         | "builtin"            | "MUTE"                 |
+---------------------+---------------------------+----------------------+------------------------+
| 5                   | 3                         | "builtin"            | "ADD_VIDEO"            |
+---------------------+---------------------------+----------------------+------------------------+
```

### added_effects_parameters

Some effects need additional parameters, and so `added_effects_parameters` stores those as key-value pairs, linked to the effect_ids from the `added_effects` table.

```sql
/* Example added_effects_parameters table */
+---------------------+----------------------+-------------------------------------+
| effect_id (INTEGER) | parameter_key (TEXT) | parameter_value (TEXT)              |
+---------------------+----------------------+-------------------------------------+
| 0                   | "file_path"          | "C:/Users/User/Videos/video_01.mp4" |
+---------------------+----------------------+-------------------------------------+
| 3                   | "text"               | "Hello World!"                      |
+---------------------+----------------------+-------------------------------------+
| 3                   | "color"              | "FF00FF"                            |
+---------------------+----------------------+-------------------------------------+
| 3                   | "size"               | "12"                                |
+---------------------+----------------------+-------------------------------------+
| 3                   | "location_x"         | "(w-tw)/2"                          |
+---------------------+----------------------+-------------------------------------+
| 3                   | "location_y"         | "(h-th)-10"                         |
+---------------------+----------------------+-------------------------------------+
| 5                   | "file_path"          | "C:/Users/User/Videos/video_02.mp4" |
+---------------------+----------------------+-------------------------------------+
```

### settings

Other pieces of data required for OceanFloor to load the project or render it are stored in `settings`.

```sql
/* Example settings table */
+----------------------+---------------------------------------+
| setting_name (TEXT)  | setting_value (TEXT)                  |
+----------------------+---------------------------------------+
| "base_video_path"    | "C:/Users/User/Videos/base_video.mp4" |
+----------------------+---------------------------------------+
| "project_identifier" | "1513886199_129"                      |
+----------------------+---------------------------------------+
```

## Queries

### Creating a New File

```sql
/* Creating the added_effects table */
CREATE TABLE added_effects
(
  effect_id INTEGER PRIMARY KEY NOT NULL,
  effect_ordering INTEGER NOT NULL,
  effect_plugin TEXT NOT NULL,
  effect_filename TEXT NOT NULL
);
/* Creating the added_effects_parameters table */
CREATE TABLE added_effects_parameters
(
  effect_id INTEGER NOT NULL,
  parameter_key TEXT NOT NULL,
  parameter_value TEXT NOT NULL,
  FOREIGN KEY (effect_id) REFERENCES added_effects.effect_id
);
/* Creating the settings table */
CREATE TABLE settings
(
  setting_name TEXT NOT NULL,
  setting_value TEXT NOT NULL
);
```

### Saving Effects to the File

```sql
/* Case: Effect is last in the ordering */
/* Saving the effect */
INSERT INTO added_effects (effect_id, effect_ordering, effect_plugin, effect_filename)
VALUES (
  (SELECT COALESCE(MAX(effect_id), -1) FROM added_effects) + 1,
  (SELECT COALESCE(MAX(effect_ordering), -1) FROM added_effects) + 1,
  "?", -- ? = plugin
  "?" -- ? = filename
);

/* Case: Effect is NOT last in the ordering */
/* Making place for the new effect */
UPDATE added_effects SET effect_ordering = effect_ordering + 1
WHERE effect_ordering >= (
  SELECT MAX(effect_ordering) FROM added_effects WHERE effect_id = ? -- ? = effect_id of the successor
);
/* Saving the effect */
INSERT INTO added_effects (effect_id, effect_ordering, effect_plugin, effect_filename)
VALUES (
  (SELECT MAX(effect_id) FROM added_effects) + 1,
  (SELECT MAX(effect_ordering) FROM added_effects WHERE effect_id = ?) - 1, -- ? = effect_id of the successor
  "?", -- ? = plugin
  "?" -- ? = filename
);

/* Saving the effect parameters */
INSERT INTO added_effects_parameters (effect_id, parameter_key, parameter_value)
VALUES (
  (SELECT MAX(effect_id) FROM added_effects),
  "?", -- ? = key
  "?" -- ? = value
);
```

### Loading the File

```sql
/* Loading the settings */
SELECT * FROM settings;
/* Loading the effects */
SELECT * FROM added_effects ORDER BY effect_ordering;
/* Loading the effect parameters (executed for each effect) */
SELECT * FROM added_effects_parameters WHERE effect_id = ?; -- ? = effect_id of the effect
```

### Deleting Effects from the file

```sql
/* Deleting the effect's parameters first */
DELETE FROM added_effects_parameters WHERE effect_id = ?; -- ? = effect_id of the effect
/* Deleting the effects*/
DELETE FROM added_effects WHERE effect_id = ?; -- ? = effect_id of the effect
/* Eliminating the empty place in the ordering */
UPDATE added_effects SET effect_ordering = effect_ordering - 1 WHERE effect_ordering > ?; -- ? = ordering of the effect
```

--------------------------------------------------------------------------------

**[Back to the Documentation](../documentation.md)**

**[Back to the README](../readme.md)**
