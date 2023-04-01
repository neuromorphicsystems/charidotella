import pathlib
import typing

import event_stream
import numpy
import scipy.ndimage


def apply(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
) -> None:
    with event_stream.Decoder(input) as decoder:
        count = numpy.zeros((decoder.width, decoder.height), dtype=numpy.uint64)
        for packet in decoder:
            if packet["t"][-1] < begin:
                continue
            if packet["t"][0] >= end:
                break
            if packet["t"][0] < begin and packet["t"][-1] >= end:
                events = packet[
                    numpy.logical_and(packet["t"] >= begin, packet["t"] < end)
                ]
            elif begin is not None and packet["t"][0] < begin:
                events = packet[packet["t"] >= begin]
            elif end is not None and packet["t"][-1] >= end:
                events = packet[packet["t"] < end]
            else:
                events = packet
            numpy.add.at(count, (events["x"], events["y"]), 1)
        shifted: list[numpy.ndarray] = []
        for x, y in ((1, 0), (0, 1), (1, 2), (2, 1)):
            kernel = numpy.zeros((3, 3))
            kernel[x, y] = 1.0
            shifted.append(
                scipy.ndimage.convolve(
                    input=count,
                    weights=kernel,
                    mode="constant",
                    cval=0.0,
                )
            )
        ratios = numpy.divide(count, numpy.maximum.reduce(shifted) + 1.0)
        mask = ratios < parameters["ratio"]
        with event_stream.Decoder(input) as decoder:
            with event_stream.Encoder(
                output,
                "dvs",
                decoder.width,
                decoder.height,
            ) as encoder:
                for packet in decoder:
                    if packet["t"][-1] < begin:
                        continue
                    if packet["t"][0] >= end:
                        break
                    if packet["t"][0] < begin and packet["t"][-1] >= end:
                        events = packet[
                            numpy.logical_and(packet["t"] >= begin, packet["t"] < end)
                        ]
                    elif begin is not None and packet["t"][0] < begin:
                        events = packet[packet["t"] >= begin]
                    elif end is not None and packet["t"][-1] >= end:
                        events = packet[packet["t"] < end]
                    else:
                        events = packet
                    events = events[mask[events["x"], events["y"]]]
                    if len(events) > 0:
                        encoder.write(events)
