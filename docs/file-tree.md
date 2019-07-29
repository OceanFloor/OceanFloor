# File Tree

## The OceanFloor file tree (explanations included)

```java
oceanfloor\                          // Root path
+---- oceanfloor.py                  // Main file
+---- requirements.txt               // For PIP
+---- __init__.py                    // (Module initialization)
+---- source\                        // Source files
|     +---- classes.py               // Class definitions
|     +---- menus.py                 // Menus in the program
|     +---- events.py                // Events bound to functions
|     +---- constants.py             // Program constants (Window size etc.)
|     +---- environment.py           // Environment-specific vars (Windows architechture etc.)
|     +---- queries.py               // SQL queries
|     +---- __init__.py              // (Module initialization)
|     +---- bitmaps\                 // Bitmaps for menu items and such
+---- plugins\                       // Plugins installation folder
|     +---- builtin\                 // Plugin of the built in effects
|     |     +---- about.txt          // Metadata for this plugin (author, version, links)
|     |     +---- effects\           // All effects in this plugin
|     |     |     +---- text.json    // ^ Text effect
|     |     |     +---- mute.json    // ^ Mute effect
|     |     |     +---- zoom.json    // ^ Zoom effect
|     |     +---- bitmaps\           // Bitmaps for the effects
|     |           +---- text.png     // ^ For the text effect
|     |           +---- mute.png     // ^ For the mute effect
|     |           +---- zoom.png     // ^ For the zoom effect
|     +---- myplugin1\               // A custom plugin installed
|     +---- myplugin2\               // Another custom plugin installed
+---- ffmpeg\                        // FFmpeg static builds
|     +---- win32\                   // ^ For Windows 32bit
|     +---- win64\                   // ^ For Windows 64bit
+---- docs\                          // Documentation files
```

--------------------------------------------------------------------------------

**[Back to the Documentation](documentation.md)**

**[Back to the README](../readme.md)**
