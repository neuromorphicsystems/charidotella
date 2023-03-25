import pathlib
import typing

import event_stream
import numpy


def apply(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
) -> None:
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
                encoder.write(events)
