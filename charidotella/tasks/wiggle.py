import importlib.resources
import pathlib
import shutil
import subprocess
import tempfile
import typing

from .. import utilities

EXTENSION = ".gif"


def run(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
):
    frametime = int(
        round(
            (end - begin) / utilities.timecode(parameters["forward_duration"]) * 20000.0
        )
    )
    tau = int(round(parameters["tau_to_frametime_ratio"] * frametime))
    print(f"{begin=}, {end=}, {frametime=}, {tau=}")
    with tempfile.TemporaryDirectory() as temporary_directory_string:
        temporary_directory = pathlib.Path(temporary_directory_string)
        base_frames = temporary_directory / "base_frames"
        base_frames.mkdir(exist_ok=True)
        es_to_frames_arguments = [
            str(
                importlib.resources.files("charidotella").joinpath(
                    "assets/es_to_frames"
                )
            ),
            f"--input={input}",
            f"--output={base_frames}",
            f"--begin={begin}",
            f"--end={end}",
            f"--frametime={frametime}",
            f"--scale={parameters['scale']}",
            f"--style={parameters['style']}",
            f"--tau={tau}",
            f"--oncolor={parameters['on_color']}",
            f"--offcolor={parameters['off_color']}",
            f"--idlecolor={parameters['idle_color']}",
            f"--cumulative-ratio={parameters['cumulative_ratio']}",
        ]
        if "lambda_max" in parameters:
            es_to_frames_arguments.append(f"--lambda-max={parameters['lambda_max']}")
        if parameters["timecode"]:
            es_to_frames_arguments.append("--add-timecode")
        subprocess.run(
            es_to_frames_arguments,
            check=True,
        )
        sorted_frames = temporary_directory / "sorted_frames"
        sorted_frames.mkdir(exist_ok=True)
        paths: list[pathlib.Path] = []
        for path in sorted(base_frames.iterdir()):
            if path.suffix == ".ppm":
                paths.append(path)
        selected_paths: list[pathlib.Path] = []
        if len(paths) >= round(parameters["tau_to_frametime_ratio"]) + 2:
            for index, path in enumerate(paths):
                if (
                    index >= round(parameters["tau_to_frametime_ratio"])
                    and index % 2 == 1
                ):
                    selected_paths.append(path)
        else:
            selected_paths = paths
        output_index = 0
        for path in selected_paths:
            shutil.copyfile(path, sorted_frames / f"{output_index:>06d}.ppm")
            output_index += 1
        for path in reversed(selected_paths[1:-1]):
            path.rename(sorted_frames / f"{output_index:>06d}.ppm")
            output_index += 1
        subprocess.run(
            [
                parameters["ffmpeg"],
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(sorted_frames / "%06d.ppm"),
                "-framerate",
                "25",
                "-filter_complex",
                "[0:v] split [a][b];[a] palettegen=reserve_transparent=true [p];[b][p] paletteuse=dither=none",
                "-loop",
                "0",
                "-f",
                "gif",
                "-y",
                str(output),
            ],
            check=True,
        )
