# Classes

This document is a guide to the descriptions, data attributes and methods of OceanFloor's classes.

## OceanFloor

A subclass of wxPython's `wx.Frame`, which serves as the parent frame of the program. Only one object of this class is created, when the program is run.

##### Data Attributes

Data Attribute|Description|Data Type
---|---|---
`base_video_path`|The path of the base video, to which all the effects are applied at render time|str
`project_identifier`|The unique identifier of the project, composed of the unix time of when it was made and the process ID of the running OceanFloor instance at that time. The project identifier is used to identify the temp files of the project that are not contained within the save file, such as the low-res preview that was rendered for it|str
`effects`|List of the effects selected|list of `Effect` objects

##### Methods

Method|Description
---|---
`__init__() -> OceanFloor`|Creates the frame
`build_gui() -> None`|Builds the visual GUI objects (menu bar, status bar, ...) on top of the frame
`save() -> None`|Saves the effects to the save file, and prompts a file dialog if no save file is associated with the current instance
`render() -> None`|Renders the video with FFmpeg

---

## Classes Relating to Effects

Read the [effects](./effects.md) document for a general idea of what OceanFloor effects are.

## EffectDefinition

An effect definition, deserialized from a JSON object as defined in the containing [plugin](./plugins.md).

##### Data Attributes

Data Attribute|Description|Data Type
---|---|---
`name`|The name of the effect (shown in its [`EffectMenuItem`](#effectmenuitem) and in the title of the [`AddEffectDialog`](#addeffectdialog))|str
`description`|A short description (shown in the status bar when hovering over the [`EffectMenuItem`](#effectmenuitem)|str
`magic`|The content of the actual FFmpeg command that will be run when the effect is rendered, with named parameters enclosed in curly brackets|str
`controls`|A list of the effect's [`EffectControl`](#effectcontrol) objects (that will be used on its [`AddEffectDialog`](#addeffectdialog))|list

##### Methods

Method|Description
---|---
`__init__(plugin, filename) -> Effect`|Creates a new `Effect` object by deserializing a [json effect object](./plugins.md#effect-objects)

## AddedEffect

##### Data Attributes

Data Attribute|Description|Data Type
---|---|---
`effect_definition`|The added effect's definition|EffectDefinition
`effect_parameters_values`|The values chosen by the user for the various parameters needed to make the effect work|dict

##### Methods

Method|Description
---|---
`save_to_file(database_connection: sqlite3.Connection) -> None`|Saves the `AddedEffect` object to the save file as described in the [save file structure document](./save-file-structure.md)
`@classmethod load_from_file(database_connection: sqlite3.Connection, effect_id: int) -> AddedEffect`|Looks at the plugin and the name of the effect in the save file and creates a new `AddedEffect` object using this data, then updates the values of its parameters to those in the file

## EffectControl


Effect controls are objects that allow the user to interact with the effect and give it the information necessary to make it work, as certain named parameters.

This interaction is enabled by wrapping GUI objects that are created from subclasses of wxPython controls, with custom properties. The named parameters the effect needs are mapped to the properties of the GUI objects.

##### Data Attributes

Data Attribute|Description|Data Type
---|---|---
`name`|Control name (shown in the effect run dialog and in window titles)|str
`description`|Control description (shown when looking for help)|str
`wrapped`|The class of the actual control GUI object|class
`hooks`|A dict of the named parameters from the effect's `magic` attribute mapped to the names of the corresponding properties of the control|dict

##### Methods

Method|Description
---|---
`__init__(deserialized_json_object: dict) -> EffectControl`|Creates a new `EffectControl` object from a deserialized [json effect control object](./plugins.md#effect-control-objects)
`show(parent: AddEffectDialog) -> None`|Shows the control on the parent `AddEffectDialog`
`hooks_values() -> dict`|Returns a dictionary of the named parameters from the effect's `magic` attribute as keys, and the values of the object's attributes as values (as defined in the `hooks` data attribute)

## EffectMenuItem


A subclass of wxPython's `wx.MenuItem`. When the program's GUI ([the parent frame](#oceanfloor)) is built, all the plugins installed get a menu with `EffectMenuItem`s which, when clicked, prompt an [`AddEffectDialog`](#addeffectdialog) to request extra parameters from the user for the effect they wish to add.

Each `EffectMenuItem`'s text, bitmap, help string are taken from the `EffectDefinition` object which is supplied to it.

##### Data Attributes

Data Attribute|Description|Data Type
---|---|---
`plugin`||str
`effect_filename`||str

##### Methods

Method|Description
---|---
`__init__(effect_definition) -> EffectMenuItem`|Creates a new `EffectMenuItem` object using

## OceanFloorError

An `Exception` subclass that gets raised when certain errors occur during operation of OceanFloor.
See the [errors documentation](./errors.md) for a list of errors.

##### Data Attributes

Data Attribute|Description|Data Type
---|---|---
`context`|The context in which the error occured (during rendering, loading a save file etc.)|ErrorContext
`message`|The error that occured|ErrorMessage
`details`|Dictionary of specific details for formatting the text of the error message|dict

##### Methods

Method|Description
---|---
`__init__(context: ErrorContext, message: ErrorMessage, details: dict) -> OceanFloorException`|Creates a new `OceanFloorError` object with the specified context and error code
`__str__() -> str`|Returns a string of the error's information, for use with an error message dialog

## ErrorContext

An `Enum` that defines all the error contexts.

##### Data Attributes

See the [errors documentation](./errors.md).

##### Methods

None.

## ErrorMessage

An `Enum` that defines all the error messages.

##### Data Attributes

See the [errors documentation](./errors.md).

##### Methods

None.

---

**[Back to the Documentation](../documentation.md)**

**[Back to the README](../readme.md)**
