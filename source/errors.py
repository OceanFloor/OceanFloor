class OceanFloorError(Exception):
    """A custom exception.
    """
    pass


class ErrorContext:
    """An enumeration for all the error contexts in the program.
    """
    GENERAL_ERROR = "Could not complete requested action"
    LOAD_PLUGINS = "Could not load plugin"
    LOAD_SAVE_FILE = "Could not load save file"
    RENDER = "Could not render video"
    UPLOAD = "Could not upload video"
    LOAD_EFFECT_FILE = "Could not load effect"


class ErrorMessage:
    """An enumeration for all the error messages in the program.
    """
    UNKNOWN_ERROR = "Unknown Error"
    TIMELINE_TABLE_NOT_FOUND = "Timeline table not found"
    MAGIC_VALUES_TABLE_NOT_FOUND = "Magic values table not found"
    REQUIRED_SETTING_NOT_FOUND = "Required setting not found ({})"
    SETTINGS_TABLE_NOT_FOUND = "Settings table not found"
    PLUGIN_NOT_RECOGNIZED = "Plugin not recognized ({})"
    EFFECT_NOT_RECOGNIZED = "Effect not recognized ({} in plugin {})"
    #EFFECT_PARAMETER_NOT_RECOGNIZED = "Effect parameter not recognized (\"{}\" of {} in plugin {})"
    #EFFECT_PARAMETER_ORPHANED = "Effect Parameter {} points to an effect object which doesn't exist (found ID: {})"
    #REQUIRED_EFFECT_PARAMETER_NOT_FOUND = "Required effect parameter not found (parameter \"{}\" of effect {} in plugin {})"
    EFFECTS_FOLDER_NOT_FOUND = "Effects folder not found (plugin {})"
    EFFECT_FILE_CONTAINS_INVALID_JSON = "invalid json ({}/{})"
    EFFECT_FILE_MISSING_REQUIRED_KEY = "missing required key\n(key \"{}\" in {}/{})"
    CONTROL_IN_EFFECT_FILE_MISSING_REQUIRED_KEY = "control missing required key\n(key \"{}\" in {}/{})"
    CONTROL_IN_EFFECT_FILE_HAS_UNKNOWN_TYPE = "unknown control type\n(control type \"{}\" in {}/{})"
    INPUT_VIDEO_NOT_FOUND = "input video not found ({})"
    FFMPEG_ERROR = "Error in FFMPEG {}"
    HTTP_ERROR = "An HTTP error {} occured ({})"
    NON_RETRIABLE_HTTP_ERROR = "A non-retriable HTTP error {} occurred:\n{}"
    RETRY_LIMIT_EXCEEDED = "Retry limit exceeded"
