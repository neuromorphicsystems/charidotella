import argparse
import os
import pathlib
import re
import sys

ANSI_COLORS_ENABLED = os.getenv("ANSI_COLORS_DISABLED") is None

TIMECODE_PATTERN = re.compile(r"^(\d+):(\d+):(\d+)(?:\.(\d+))?$")


def with_suffix(path: pathlib.Path, suffix: str):
    return path.parent / f"{path.name}{suffix}"


def format_bold(message: str) -> str:
    if ANSI_COLORS_ENABLED:
        return f"\033[1m{message}\033[0m"
    return message


def info(icon: str, message: str):
    sys.stdout.write(f"{icon} {message}\n")
    sys.stdout.flush()


def error(message: str):
    sys.stderr.write(f"❌ {message}\n")
    sys.exit(1)


def timestamp_to_timecode(timestamp: int):
    hours = timestamp // (60 * 60 * 1000000)
    timestamp -= hours * 60 * 60 * 1000000
    minutes = timestamp // (60 * 1000000)
    timestamp -= minutes * 60 * 1000000
    seconds = timestamp // 1000000
    timestamp -= seconds * 1000000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{timestamp:06d}"


def timestamp_to_short_timecode(timestamp: int):
    hours = timestamp // (60 * 60 * 1000000)
    timestamp -= hours * 60 * 60 * 1000000
    minutes = timestamp // (60 * 1000000)
    timestamp -= minutes * 60 * 1000000
    seconds = timestamp // 1000000
    timestamp -= seconds * 1000000
    timestamp_string = "" if timestamp == 0 else f".{timestamp:06d}".rstrip("0")
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}{timestamp_string}"
    if minutes > 0:
        return f"{minutes}:{seconds:02d}{timestamp_string}"
    return f"{seconds}{timestamp_string}"


def timecode(value: str) -> int:
    if value.isdigit():
        return int(value)
    match = TIMECODE_PATTERN.match(value)
    if match is None:
        raise argparse.ArgumentTypeError(
            f"expected an integer or a timecode (12:34:56.789000), got {value}"
        )
    result = (
        int(match[1]) * 3600000000 + int(match[2]) * 60000000 + int(match[3]) * 1000000
    )
    if match[4] is not None:
        fraction_string: str = match[4]
        if len(fraction_string) == 6:
            result += int(fraction_string)
        elif len(fraction_string) < 6:
            result += int(fraction_string + "0" * (6 - len(fraction_string)))
        else:
            result += round(float("0." + fraction_string) * 1e6)
    return result
