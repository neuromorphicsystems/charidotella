import importlib.resources
import pathlib
import subprocess
import typing

EXTENSION = ".svg"


def run(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
):
    subprocess.run(
        [
            str(
                importlib.resources.files("charidotella").joinpath(
                    "assets/event_rate"
                )
            ),
            str(input),
            str(output),
            f"--begin={begin}",
            f"--end={end}",
            f"--long={parameters['long_tau']}",
            f"--short={parameters['short_tau']}",
            f"--width={parameters['width']}",
            f"--height={parameters['height']}",
            f"--longcolor={parameters['long_tau_color']}",
            f"--shortcolor={parameters['short_tau_color']}",
            f"--axiscolor={parameters['axis_color']}",
            f"--maingridcolor={parameters['main_grid_color']}",
            f"--secondarygridcolor={parameters['secondary_grid_color']}",
        ],
        check=True,
    )
