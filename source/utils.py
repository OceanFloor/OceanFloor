import os
import shlex

from . import environment


def color_from_hex(hex_value):
    [r, g, b] = [int(channel, 16) for channel in [hex_value[0:2], hex_value[2:4], hex_value[4:6]]]
    return [r, g, b]


def generate_temp_filenames(count, extension):
    return [(environment.TEMP_PATH / f"{os.getpid()}{i}{extension}").as_posix() for i in range(count)]


def calculate_percentage(part, whole):
    return 100 * part / whole


def generate_renderlist(timeline, input_video_path, output_video_path, temp_filename_1, temp_filename_2):
    """Generates a (percentage, action, popenargs) renderlist
    using the `timeline`, input and output video paths, and temp filenames.
    """
    temp_input = temp_filename_1
    temp_output = temp_filename_2

    count = len(timeline.items)
    if count > 0:
        for i, timeline_item in enumerate(timeline.items):
            # To avoid copying the input video to a temp file, it's used as the first temp input.
            # Later, only the temp files are used (and switched after every command).
            if i == 0:
                temp_input = input_video_path
                temp_output = temp_filename_2
            elif i == 1:
                temp_input = temp_filename_2
                temp_output = temp_filename_1

            command = timeline_item.effect.magic.format(**(timeline_item.magic_values))
            popenargs = [environment.FFMPEG_PATH.as_posix(), "-y", "-i", temp_input, *(shlex.split(command)), temp_output]

            percentage = int(calculate_percentage(i, count + 1))  # Count + 1: The final save/transcode rendering is also counted
            action = f"Rendering effect #{i + 1}/{count} ({timeline_item.effect.plugin_name}/{timeline_item.effect.name})"  # i + 1: zero-based -> one-based
            yield (percentage, action, popenargs)

            temp_input, temp_output = temp_output, temp_input

        percentage = int(calculate_percentage(count, count + 1))
    else:
        temp_input = input_video_path
        percentage = 0

    action = "Saving / Transcoding"
    popenargs = [environment.FFMPEG_PATH.as_posix(), "-y", "-i", temp_input, "-c", "copy", output_video_path]

    yield (percentage, action, popenargs)
