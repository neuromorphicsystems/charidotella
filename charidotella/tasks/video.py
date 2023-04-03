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
                str(
                    importlib.resources.files("charidotella").joinpath(
                        "assets/size"
                    )
                ),
                str(input),
            ],
            check=True,
            capture_output=True,
        ).stdout.split(b"x")
    )
    width *= parameters["scale"]
    height *= parameters["scale"]
    es_to_frames_arguments = [
        str(
            importlib.resources.files("charidotella").joinpath(
                "assets/es_to_frames"
            )
        ),
        f"--input={input}",
        f"--begin={begin}",
        f"--end={end}",
        f"--frametime={parameters['frametime']}",
        f"--scale={parameters['scale']}",
        f"--style={parameters['style']}",
        f"--tau={parameters['tau']}",
        f"--oncolor={parameters['on_color']}",
        f"--offcolor={parameters['off_color']}",
        f"--idlecolor={parameters['idle_color']}",
        f"--cumulative-ratio={parameters['cumulative_ratio']}",
    ]
    if "lambda_max" in parameters:
        es_to_frames_arguments.append(f"--lambda-max={parameters['lambda_max']}")
    if parameters["timecode"]:
        es_to_frames_arguments.append("--add-timecode")
    es_to_frames = subprocess.Popen(
        es_to_frames_arguments,
        stdout=subprocess.PIPE,
    )
    assert es_to_frames.stdout is not None
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
        frame = es_to_frames.stdout.read(frame_size)
        if len(frame) != frame_size:
            break
        ffmpeg.stdin.write(frame)
    ffmpeg.stdin.close()
    es_to_frames.wait()
    es_to_frames = None
    ffmpeg.wait()
    ffmpeg = None
    atexit.unregister(cleanup)
