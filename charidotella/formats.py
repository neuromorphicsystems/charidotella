import pathlib
import types
import typing

import aedat
import event_stream
import numpy

TYPE_EVENT_STREAM: int = 0
TYPE_AEDAT: int = 1


class Decoder:
    def __init__(self, path: pathlib.Path):
        self.width: int
        self.height: int
        if path.suffix == ".es":
            self.type = TYPE_EVENT_STREAM
        elif path.suffix == ".aedat4":
            self.type = TYPE_AEDAT
        else:
            with open(path, "rb") as file:
                magic = file.read(12)
            if magic == b"Event Stream":
                self.type = TYPE_EVENT_STREAM
            elif magic == b"#!AER-DAT4.0":
                self.type = TYPE_AEDAT
            else:
                raise Exception(f"unsupported file {path}")
        self.t0 = None
        if self.type == TYPE_EVENT_STREAM:
            self.decoder = event_stream.Decoder(path)
            assert self.decoder.type == "dvs"
            self.width = self.decoder.width
            self.height = self.decoder.height
        else:
            self.decoder = aedat.Decoder(path)  # type: ignore
            found = False
            for stream in self.decoder.id_to_stream().values():
                if stream["type"] == "events":
                    self.width = stream["width"]
                    self.height = stream["height"]
                    found = True
                    break
            if not found:
                raise Exception(f"the file {path} contains no events")

    def __iter__(self):
        return self

    def __next__(self) -> numpy.ndarray:
        assert self.decoder is not None
        if self.type == TYPE_EVENT_STREAM:
            return self.decoder.__next__()
        while True:
            packet = self.decoder.__next__()
            if "events" in packet:
                events = packet["events"]
                if len(events) > 0:
                    if self.t0 is None:
                        self.t0 = events["t"][0]
                    events["t"] -= self.t0
                    events["y"] = self.height - 1 - events["y"]
                return events

    def __enter__(self) -> "Decoder":
        return self

    def __exit__(
        self,
        exception_type: typing.Optional[typing.Type[BaseException]],
        value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> bool:
        assert self.decoder is not None
        if self.type == TYPE_EVENT_STREAM:
            result = self.decoder.__exit__(exception_type, value, traceback)
        else:
            result = False
        self.decoder = None
        return result
