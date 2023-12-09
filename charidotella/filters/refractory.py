from __future__ import annotations

import pathlib
import typing

import event_stream
import numpy

from .. import formats, utilities


def apply(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
) -> None:
    with formats.Decoder(input) as decoder:
        refractory = numpy.uint64(utilities.timecode(parameters["refractory"]))
        threshold_t = numpy.zeros((decoder.width, decoder.height), dtype=numpy.uint64)
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
                mask = numpy.full(len(events), False, dtype=bool)
                for index, (t, x, y, _) in enumerate(events):
                    if t >= threshold_t[x, y]:
                        mask[index] = True
                        threshold_t[x, y] = t + refractory
                encoder.write(events[mask])
