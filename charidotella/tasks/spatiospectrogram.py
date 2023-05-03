import atexit
import importlib.resources
import pathlib
import subprocess
import typing

EXTENSION = ".mp4"


def run(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
):
    width, height = (
        int(value)
        for value in subprocess.run(
            [
                str(importlib.resources.files("charidotella").joinpath("assets/size")),
                str(input),
            ],
            check=True,
            capture_output=True,
        ).stdout.split(b"x")
    )
    width *= parameters["scale"]
    height *= parameters["scale"]
    spatiospectrogram_arguments = [
        str(
            importlib.resources.files("charidotella").joinpath(
                "assets/spatiospectrogram"
            )
        ),
        f"--input={input}",
        f"--begin={begin}",
        f"--end={end}",
        f"--frametime={parameters['frametime']}",
        f"--scale={parameters['scale']}",
        f"--tau={parameters['tau']}",
        f"--mode={parameters['mode']}",
        f"--minimum={parameters['minimum']}",
        f"--maximum={parameters['maximum']}",
        f"--frequencies={parameters['frequencies']}",
        f"--frequency-gamma={parameters['frequency-gamma']}",
        f"--amplitude-gamma={parameters['amplitude-gamma']}",
        f"--discard={parameters['discard']}",
    ]
    if parameters["timecode"]:
        spatiospectrogram_arguments.append("--add-timecode")
    spatiospectrogram = subprocess.Popen(
        spatiospectrogram_arguments,
        stdout=subprocess.PIPE,
    )
    assert spatiospectrogram.stdout is not None
    ffmpeg = subprocess.Popen(
        [
            parameters["ffmpeg"],
            "-hide_banner",
            "-loglevel",
            "warning",
            "-stats",
            "-f",
            "rawvideo",
            "-s",
            f"{width}x{height}",
            "-framerate",
            "50",
            "-pix_fmt",
            "rgb24",
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            str(parameters["h264_crf"]),
            "-f",
            "mp4",
            "-y",
            str(output),
        ],
        stdin=subprocess.PIPE,
    )
    assert ffmpeg.stdin is not None
    frame_size = width * height * 3

    def cleanup():
        if es_to_frames is not None:
            es_to_frames.kill()
        if ffmpeg is not None:
            ffmpeg.kill()

    atexit.register(cleanup)
    while True:
        frame = spatiospectrogram.stdout.read(frame_size)
        if len(frame) != frame_size:
            break
        ffmpeg.stdin.write(frame)
    ffmpeg.stdin.close()
    spatiospectrogram.wait()
    es_to_frames = None
    ffmpeg.wait()
    ffmpeg = None
    atexit.unregister(cleanup)
