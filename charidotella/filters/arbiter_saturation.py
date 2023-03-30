import pathlib
import typing

import event_stream
import numpy


def consume_packets(
    events_packets: list[numpy.ndarray],
    last: bool,
    threshold: int,
):
    events = numpy.concatenate(events_packets)
    if last:
        events_packets = []
    else:
        mask = events["t"] < events["t"][-1]
        events_packets = [events[numpy.logical_not(mask)]]
        events = events[mask]
    deltas = numpy.concatenate(
        [numpy.diff(events["t"]), numpy.array([1], dtype=numpy.uint64)],
        dtype=numpy.int64,
    )
    jumps_indices = numpy.concatenate(
        [numpy.array([0], dtype=numpy.uint64), numpy.nonzero(deltas)[0] + 1],
        dtype=numpy.int64,
    )
    large_jump_indices = numpy.nonzero(numpy.diff(jumps_indices) > threshold)[0]
    mask = numpy.ones(len(events), dtype=bool)
    for large_jump_index in large_jump_indices:
        begin = jumps_indices[large_jump_index]
        end = jumps_indices[large_jump_index + 1]
        same_t_events = events[begin:end]
        assert numpy.all(same_t_events["t"] == same_t_events["t"][0])
        same_t_ys = numpy.unique(same_t_events["y"])
        if len(same_t_ys) == 1:
            mask[begin:end] = False
        else:
            for y in same_t_ys:
                y_indices = numpy.nonzero(same_t_events["y"] == y)[0]
                if len(y_indices) > threshold:
                    mask[y_indices + begin] = False
    return events_packets, events[mask], len(events)


def apply(
    input: pathlib.Path,
    output: pathlib.Path,
    begin: int,
    end: int,
    parameters: dict[str, typing.Any],
) -> None:
    events_packets = []
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
                events_packets.append(events)
                if events["t"][-1] > events_packets[0]["t"][0]:
                    events_packets, events, count = consume_packets(
                        events_packets=events_packets,
                        last=False,
                        threshold=parameters["threshold"],
                    )
                    encoder.write(events)
            events_packets, events, count = consume_packets(
                events_packets=events_packets,
                last=True,
                threshold=parameters["threshold"],
            )
            encoder.write(events)
