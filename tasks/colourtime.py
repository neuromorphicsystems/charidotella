import pathlib
import typing

import colourtime
import event_stream
import matplotlib
import matplotlib.colors

EXTENSION = ".png"


def run(
    input: pathlib.Path,
    output: pathlib.Path,
    duration: int,
    parameters: dict[str, typing.Any],
):
    if "cycle" in parameters:
        time_mapping = colourtime.generate_cyclic_time_mapping(
            duration=parameters["cycle"], begin=0
        )
    else:
        time_mapping = colourtime.generate_linear_time_mapping(begin=0, end=duration)
    with event_stream.Decoder(input) as decoder:
        image = colourtime.convert(
            begin=None,
            end=None,
            width=decoder.width,
            height=decoder.height,
            decoder=decoder,
            colormap=matplotlib.colormaps[parameters["colormap"]],  # type: ignore
            time_mapping=time_mapping,
            alpha=parameters["alpha"],
            background_colour=matplotlib.colors.to_rgba(parameters["background_color"]),
        )
        image.save(
            str(output),
            compress_level=parameters["png_compression_level"],
            format="png",
        )
