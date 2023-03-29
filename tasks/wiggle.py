import pathlib
import shutil
import subprocess
import tempfile
import typing

import utilities


def run(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
):
    frametime = round(
        utilities.timecode(parameters["forward_duration"]) / (end - begin) * 20000
    )
    tau = parameters["tau_to_frametime_ratio"] * frametime
    with tempfile.TemporaryDirectory() as temporary_directory_string:
        temporary_directory = pathlib.Path(temporary_directory_string)
        base_frames = temporary_directory / "base_frames"
        base_frames.mkdir(exist_ok=True)
        subprocess.run(
            [
                pathlib.Path(__file__).parent.parent
                / "command_line_tools"
                / "build"
                / "release"
                / "es_to_frames",
                f"--input={input}",
                f"--output={base_frames}",
                f"--frametime={frametime}",
                f"--tau={tau}",
                f"--style={parameters['style']}",
                f"--idlecolor={parameters['idle_color']}",
            ],
            check=True,
        )
        sorted_frames = temporary_directory / "sorted_frames"
        sorted_frames.mkdir(exist_ok=True)
        paths: list[pathlib.Path] = []
        for path in sorted(base_frames.iterdir()):
            if path.suffix == ".ppm":
                paths.append(path)
        selected_paths = []
        if len(paths) >= round(parameters["tau_to_frametime_ratio"]) + 2:
            for index, path in enumerate(paths):
                if (
                    index >= round(parameters["tau_to_frametime_ratio"])
                    and index % 2 == 1
                ):
                    selected_paths.append(paths)
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
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "warning",
                "-stats",
                "-i",
                str(sorted_frames / "%06d.ppm"),
                "-framerate",
                "25",
                "-filter_complex",
                "[0:v] split [a][b];[a] palettegen=reserve_transparent=true [p];[b][p] paletteuse=dither=none",
                "-loop",
                "0",
                "-y",
                str(output),
            ],
            check=True,
        )
