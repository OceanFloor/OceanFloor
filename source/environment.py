from pathlib import Path
import os

FFMPEG_PATH = Path("ffmpeg/win64/ffmpeg/bin/ffmpeg.exe")
PLUGINS_PATH = Path("plugins")
BITMAPS_PATH = Path("source/bitmaps")
TEMP_PATH = Path("temp")
FONTS_DIR = (Path(os.environ["systemroot"]) / "fonts").as_posix()
