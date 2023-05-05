import importlib.resources
import pathlib
import subprocess
import typing

EXTENSION = ".png"


def run(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
):
    arguments = [
        str(importlib.resources.files("charidotella").joinpath("assets/spectrogram")),
        str(input),
        str(output),
        str((output.parent / output.stem).with_suffix(".json")),
        f"--begin={begin}",
        f"--end={end}",
        f"--tau={parameters['tau']}",
        f"--mode={parameters['mode']}",
        f"--maximum={parameters['maximum']}",
        f"--frequencies={parameters['frequencies']}",
        f"--times={parameters['times']}",
        f"--gamma={parameters['gamma']}",
    ]
    if "minimum" in parameters:
        arguments.append(f"--minimum={parameters['minimum']}")
    if "region-of-interest" in parameters:
        arguments.append(f"--left={parameters['region-of-interest'][0]}")
        arguments.append(f"--bottom={parameters['region-of-interest'][1]}")
        arguments.append(f"--width={parameters['region-of-interest'][2]}")
        arguments.append(f"--height={parameters['region-of-interest'][3]}")
    subprocess.run(
        arguments,
        check=True,
    )
