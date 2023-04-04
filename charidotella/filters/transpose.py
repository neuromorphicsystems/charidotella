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
        if parameters["method"] == "flip_left_right":
            width, height = decoder.width, decoder.height
            method = 0
        elif parameters["method"] == "flip_top_bottom":
            width, height = decoder.width, decoder.height
            method = 1
        elif parameters["method"] == "rotate_90":
            width, height = decoder.height, decoder.width
            method = 2
        elif parameters["method"] == "rotate_180":
            width, height = decoder.width, decoder.height
            method = 3
        elif parameters["method"] == "rotate_270":
            width, height = decoder.height, decoder.width
            method = 4
        elif parameters["method"] == "transpose":
            width, height = decoder.height, decoder.width
            method = 5
        elif parameters["method"] == "transverse":
            width, height = decoder.height, decoder.width
            method = 6
        else:
            raise Exception(f"unknown method \"{parameters['method']}\"")
        with event_stream.Encoder(
            output,
            "dvs",
            width,
            height,
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
                if method == 0:  # flip_left_right
                    events["x"] = width - 1 - events["x"]
                elif method == 1:  # flip_top_bottom
                    events["y"] = height - 1 - events["y"]
                elif method == 2:  # rotate_90
                    new_events = events.copy()
                    new_events["x"] = width - 1 - events["y"]
                    new_events["y"] = events["x"]
                    events = new_events
                elif method == 3:  # rotate_180
                    events["x"] = width - 1 - events["x"]
                    events["y"] = height - 1 - events["y"]
                elif method == 4:  # rotate_270
                    new_events = events.copy()
                    new_events["x"] = events["y"]
                    new_events["y"] = height - 1 - events["x"]
                    events = new_events
                elif method == 5:  # transpose
                    new_events = events.copy()
                    new_events["x"] = events["y"]
                    new_events["y"] = events["x"]
                    events = new_events
                elif method == 6:  # transverse
                    new_events = events.copy()
                    new_events["x"] = width - 1 - events["y"]
                    new_events["y"] = height - 1 - events["x"]
                    events = new_events
                else:
                    raise Exception(f"unknown method {method}")
                encoder.write(events)
