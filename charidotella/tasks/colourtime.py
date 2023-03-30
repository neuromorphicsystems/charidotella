import pathlib
import typing

import colourtime
import event_stream
import matplotlib
import matplotlib.colors
import PIL.Image

EXTENSION = ".png"


def run(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
):
    if "cycle" in parameters:
        time_mapping = colourtime.generate_cyclic_time_mapping(
            duration=parameters["cycle"],
            begin=begin,
        )
    else:
        time_mapping = colourtime.generate_linear_time_mapping(begin=begin, end=end)
    with event_stream.Decoder(input) as decoder:
        image = colourtime.convert(
            begin=begin,
            end=end,
            width=decoder.width,
            height=decoder.height,
            decoder=decoder,
            colormap=matplotlib.colormaps[parameters["colormap"]],  # type: ignore
            time_mapping=time_mapping,
            alpha=parameters["alpha"],
            background_colour=matplotlib.colors.to_rgba(parameters["background_color"]),
        )
        image.resize(
            size=(
                image.width * parameters["scale"],
                image.height * parameters["scale"],
            ),
            resample=PIL.Image.Resampling.NEAREST,  # type: ignore
        ).save(
            str(output),
            compress_level=parameters["png_compression_level"],
            format="png",
        )
