import httplib2
import googleapiclient.errors

# GUI

PROGRAM_TITLE = "OceanFloor - The Video Editor that loves you back"
WINDOW_SIZE = 1000, 1000
WINDOW_MIN_SIZE = 750, 500
TIMELINE_ITEM_PANEL_SIZE = 125, 125
HISTORY_ITEM_PANEL_SIZE = 150, 30
UPLOAD_DIALOG_MIN_SIZE = 300, -1
TIMELINE_ITEM_VIEWER_MIN_SIZE = 500, 250
UNDONE_COLOR = 150, 150, 150

# PLUGINS

EFFECT_REQUIRED_KEYS = "name", "description", "magic", "controls", "color"
EFFECT_OPTIONAL_KEYS = ()
EFFECT_CONTROL_REQUIRED_KEYS = "name", "magic_name", "description", "type"
EFFECT_CONTROL_OPTIONAL_KEYS = ()
EFFECT_CONTROL_ALLOWED_TYPES = "UIntProperty", "IntProperty", "StringProperty", "ColourProperty", "FileProperty", "TimeProperty", "FloatProperty", "RGBColourProperty", "FontProperty"

# SAVE FILES

REQUIRED_SETTINGS = "input_video_path", "output_video_path"

# MISC

DOCUMENTATION_URL = "https://github.com/OceanFloor/OceanFloor/blob/master/documentation.md"

# YOUTUBE DATA API

YOUTUBE_CATEGORIES = {'Film & Animation': '1', 'Autos & Vehicles': '2', 'Music': '10',
                      'Pets & Animals': '15', 'Sports': '17', 'Short Movies': '18',
                      'Travel & Events': '19', 'Gaming': '20', 'Videoblogging': '21',
                      'People & Blogs': '22', 'Comedy': '34', 'Entertainment': '24',
                      'News & Politics': '25', 'Howto & Style': '26', 'Education': '27',
                      'Science & Technology': '28', 'Nonprofits & Activism': '29',
                      'Movies': '30', 'Anime/Animation': '31', 'Action/Adventure': '32',
                      'Classics': '33', 'Documentary': '35', 'Drama': '36', 'Family': '37',
                      'Foreign': '38', 'Horror': '39', 'Sci-Fi/Fantasy': '40', 'Thriller':
                      '41', 'Shorts': '42', 'Shows': '43', 'Trailers': '44'}
YOUTUBE_PRIVACY_STATUSES = "Public", "Private", "Unlisted"
YOUTUBE_API_CLIENT_SECRETS_FILE = "youtube/client_secret.json"
YOUTUBE_UPLOAD_CHUNKSIZE = 4 * 1024 * 1024  # 4MB: https://github.com/google/google-api-dotnet-client/issues/677
YOUTUBE_UPLOAD_MAX_RETRIES = 10
YOUTUBE_UPLOAD_RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, googleapiclient.errors.ResumableUploadError)
YOUTUBE_UPLOAD_RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
