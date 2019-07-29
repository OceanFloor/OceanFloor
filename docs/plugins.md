# Plugins for OceanFloor

In OceanFloor, plugins are essentially effect packs you can install to get access to more functionality. All of OceanFloor's built in effects are by themselves contained in a plugin.

## Plugin Structure

A plugin is installed as a folder of files inside the `oceanfloor\plugins` folder.
(The following excerpt is taken from the [OceanFloor File Tree document](./file-tree.md)).

```java
plugins\                       // Plugins installation folder
+---- builtin\                 // Plugin of the built in effects
|     +---- about.txt          // Information about this plugin (author, version, links)
|     +---- effects\           // All effects in this plugin
|     |     +---- text.json    // ^ Text effect
|     |     +---- mute.json    // ^ Mute effect
|     |     +---- zoom.json    // ^ Zoom effect
|     +---- bitmaps\           // Bitmaps for the effects
|           +---- text.png     // ^ For the text effect
|           +---- mute.png     // ^ For the mute effect
|           +---- zoom.png     // ^ For the zoom effect
+---- myplugin1\               // A custom plugin installed
+---- myplugin2\               // Another custom plugin installed
```

### Effect Objects

Effects are defined as JSON objects - each in a separate `.json` file inside the plugin's `effects` folder.

*Deserialize into python [Effect](./classes.md#effect) objects.*

##### Required Keys

Key|Description|Value Type
---|---|---
`name`|The name of the effect|string
`description`|A short description (this will be shown in the status bar when hovering over the effect's menu item)|string
`magic`|The content of the actual FFmpeg command that will be run when the effect is rendered, with named parameters enclosed in curly brackets|string
`controls`|The effect's [controls](#control-objects)|array of objects

##### Optional Keys

Key|Description|Value Type
---|---|---
`shortcut`|Effect shortcut|array of strings

### Effect Control Objects

The value of the effect object's `controls` key is an array of objects that define the controls needed to make the effect work.

*Deserialize into python [EffectControl](./classes.md#effectcontrol) objects.*

##### Required Keys
Key|Description|Value Type
---|---|---
`name`|Control name|string
`description`|Control description|string
`type`|The type of the control (list of control types [here](./effect-control-types.md))|string
`hooks`|The named parameters from the effect's `magic` mapped to the corresponding attributes of the control|object



## Example - Creating a Plugin

Creating a plugin for OceanFloor is as easy as making a few folders and text files.

### Setup

From the root of your OceanFloor installation, navigate to `plugins`.
In there, create a folder `MyPlugin` with two subfolders: `effects` and `bitmaps`.

```
> cd plugins
> md MyPlugin
> md MyPlugin\effects
> md MyPlugin\bitmaps
```

### Describing the Plugin

We'll start with general information about the plugin. Open your favorite text editor and write a few sentences to describe your plugin (this can be anything you want):

```
This is my awesome plugin for OceanFloor!
Version: 1.0.0
Author: example@example.com

Follow me on Twitter: @example
```

Save this file as `about.txt` in `MyPlugin`.
This information will be shown to users who click on the plugin's "About" button.

### Implementing an Effect

What good is a plugin without any effects? for this example, we'll implement an effect that adds text to the video. The users will be able to select text size, color, and location (this is the same as the built in `Text` effect).

#### Name, Description, Magic

Let's create a new `JSON` file and make the effect object, starting with the [required keys](#effect-objects) `name`, `description` and `magic`:

```json
{
  "name": "My Text Effect",
  "description": "Render text on the video.",
  "magic": "-vf \"drawtext=fontfile='C\\:\\\\Windows\\\\Fonts\\\\{font_file}': fontcolor='0x{font_color}': fontsize={font_size}: text='{input_text}': x={x}: y={y}\" -c:a copy",
}
```

#### Controls

After looking at the [list of control types](./effect-control-types.md), we can add in the array of controls we want:

```json
{
  "controls": [{
    "name": "Font, Size",
    "description": "Font and size of the text to render.",
    "type": "FontPickerCtrl",
    "hooks": {
        "font_file": "FontFile",
        "font_size": "FontSize"
    }
  },
  {
    "name": "Colour",
    "description": "Colour of the text to render.",
    "type": "ColourPickerCtrl",
    "hooks": {
        "font_color": "Colour"
    }
  },
  {
    "name": "Position",
    "description": "Position of the text on the video.",
    "type": "PositionCtrl",
    "hooks": {
        "x": "X",
        "y": "Y"
    }
  }]
}
```

#### Shortcut

We can include the optional `shortcut` key:

```json
{
  "shortcut": ["F7"]
}
```

#### Full Code

```json
{
  "name": "My Text Effect",
  "description": "Render text on the video.",
  "magic": "-vf \"drawtext=fontfile='C\\:\\\\Windows\\\\Fonts\\\\{font_file}': fontcolor='0x{font_color}': fontsize={font_size}: text='{input_text}': x={x}: y={y}\" -c:a copy",
  "controls": [{
    "name": "Font, Size",
    "description": "Font and size of the text to render.",
    "type": "FontPickerCtrl",
    "hooks": {
        "font_file": "FontFile",
        "font_size": "FontSize"
    }
  },
  {
    "name": "Colour",
    "description": "Colour of the text to render.",
    "type": "ColourPickerCtrl",
    "hooks": {
        "font_color": "Colour"
    }
  },
  {
    "name": "Position",
    "description": "Position of the text on the video.",
    "type": "PositionCtrl",
    "hooks": {
        "x": "X",
        "y": "Y"
    }
  }],
  "shortcut": ["F7"]
}
```

Save the file as `MyEffect.json` in the `MyPlugin\effects` folder.

#### Bitmap

Optionally, you can add a bitmap that will be shown next to your effect. Simply create a new PNG image and save it in `MyPlugin\bitmaps`, as `MyEffect.png` (use the same name you used for the effect's JSON file).

### Sharing the Plugin

That's it! you now have a fully functional plugin. To share it, simply give the `MyPlugin` folder to your friends and have them put it in their own `plugins` folder.

***IMPORTANT:*** **Only use plugins from credible sources. Beware of malicious plugins.**

---

**[Back to the Documentation](documentation.md)**

**[Back to the README](../readme.md)**
