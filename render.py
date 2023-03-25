import argparse
import json
import os
import pathlib
import re
import sys
import tempfile
import typing
import uuid

import event_stream
import jsonschema
import toml

import animals
import filters.arbiter_saturation
import filters.default
import tasks.colourtime
import tasks.event_rate
import tasks.video

parser = argparse.ArgumentParser(
    description="Process Event Stream files",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
subparsers = parser.add_subparsers(dest="command")
configure_parser = subparsers.add_parser(
    "configure", help="Generate a configuration file"
)
configure_parser.add_argument(
    "directory",
    help="Directory to scan (recursively) for Event Stream files",
)
configure_parser.add_argument(
    "--configuration",
    "-c",
    default="render-configuration.toml",
    help="Render configuration file path",
)
configure_parser.add_argument(
    "--force",
    "-f",
    action="store_true",
    help="Replace the configuration if it exists",
)
run_parser = subparsers.add_parser("run", help="Process a configuration file")
run_parser.add_argument(
    "--configuration",
    "-c",
    default="render-configuration.toml",
    help="Render configuration file path",
)
run_parser.add_argument(
    "--force",
    "-f",
    action="store_true",
    help="Replace files that already exist",
)
args = parser.parse_args()


TIMECODE_PATTERN = re.compile(r"^(\d+):(\d+):(\d+)(?:\.(\d+))?$")

filter_apply = typing.Callable[
    [
        pathlib.Path,
        pathlib.Path,
        int,
        int,
        dict[str, typing.Any],
    ],
    None,
]

FILTERS: dict[str, filter_apply] = {
    "default": filters.default.apply,
    "arbiter_saturation": filters.arbiter_saturation.apply,
}

task_run = typing.Callable[
    [
        pathlib.Path,
        pathlib.Path,
        int,
        dict[str, typing.Any],
    ],
    None,
]

TASKS: dict[str, tuple[str, task_run]] = {
    "colourtime": (tasks.colourtime.EXTENSION, tasks.colourtime.run),
    "event_rate": (tasks.event_rate.EXTENSION, tasks.event_rate.run),
    "video": (tasks.video.EXTENSION, tasks.video.run),
}

ANSI_COLORS_ENABLED = os.getenv("ANSI_COLORS_DISABLED") is None


def format_bold(message: str) -> str:
    if ANSI_COLORS_ENABLED:
        return f"\033[1m{message}\033[0m"
    return message


def info(icon: str, message: str):
    sys.stdout.write(f"{icon} {message}\n")
    sys.stdout.flush()


def error(message: str):
    sys.stderr.write(f"❌ {message}\n")
    sys.exit(1)


def timestamp_to_timecode(timestamp: int):
    hours = timestamp // (60 * 60 * 1000000)
    timestamp -= hours * 60 * 60 * 1000000
    minutes = timestamp // (60 * 1000000)
    timestamp -= minutes * 60 * 1000000
    seconds = timestamp // 1000000
    timestamp -= seconds * 1000000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{timestamp:06d}"


def timestamp_to_short_timecode(timestamp: int):
    hours = timestamp // (60 * 60 * 1000000)
    timestamp -= hours * 60 * 60 * 1000000
    minutes = timestamp // (60 * 1000000)
    timestamp -= minutes * 60 * 1000000
    seconds = timestamp // 1000000
    timestamp -= seconds * 1000000
    timestamp_string = "" if timestamp == 0 else f".{timestamp:06d}".rstrip("0")
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}{timestamp_string}"
    if minutes > 0:
        return f"{minutes}:{seconds:02d}{timestamp_string}"
    return f"{seconds}{timestamp_string}"


def timecode(value: str) -> int:
    if value.isdigit():
        return int(value)
    match = TIMECODE_PATTERN.match(value)
    if match is None:
        raise argparse.ArgumentTypeError(
            f"expected an integer or a timecode (12:34:56.789000), got {value}"
        )
    result = (
        int(match[1]) * 3600000000 + int(match[2]) * 60000000 + int(match[3]) * 1000000
    )
    if match[4] is not None:
        fraction_string: str = match[4]
        if len(fraction_string) == 6:
            result += int(fraction_string)
        elif len(fraction_string) < 6:
            result += int(fraction_string + "0" * (6 - len(fraction_string)))
        else:
            result += round(float("0." + fraction_string) * 1e6)
    return result


class Encoder(toml.TomlEncoder):
    def dump_list(self, v):
        return f"[{', '.join(str(self.dump_value(u)) for u in v)}]"


def render_configuration_schema():
    with open(
        pathlib.Path(__file__).resolve().parent / "render-configuration-schema.json"
    ) as schema_file:
        return json.load(schema_file)


def with_suffix(path: pathlib.Path, suffix: str):
    return path.parent / f"{path.name}{suffix}"


def load_parameters(path: pathlib.Path):
    if path.is_file():
        with open(path) as file:
            return toml.load(file)
    return None


def save_parameters(path: pathlib.Path, parameters: dict[str, typing.Any]):
    with open(path.with_suffix(".part"), "w") as file:
        toml.dump(parameters, file)
    path.with_suffix(".part").rename(path)


def compare_parameters(a: dict[str, typing.Any], b: dict[str, typing.Any]):
    return json.dumps(a, sort_keys=True, separators=(",", ":")) == json.dumps(
        b, sort_keys=True, separators=(",", ":")
    )


if args.command == "configure":
    configuration_path = pathlib.Path(args.configuration).resolve()
    if not args.force and configuration_path.is_file():
        error(f'"{configuration_path}" already exists (use --force to override it)')
    directory = pathlib.Path(args.directory).resolve()
    paths = list(directory.rglob("*.es"))
    paths.sort(key=lambda path: (path.stem, path.parent))
    if len(paths) == 0:
        error('no .es files found in "{directory}"')
    names = animals.generate_names(len(paths))
    jobs = []
    for index, (name, path) in enumerate(zip(names, paths)):
        info(
            animals.composite_name_to_icon(name),
            f'{index + 1}/{len(paths)} reading range for {format_bold(name)} ("{path}")',
        )
        begin: typing.Optional[int] = None
        end: typing.Optional[int] = None
        with event_stream.Decoder(path) as decoder:
            for packet in decoder:
                if begin is None:
                    begin = int(packet["t"][0])
                end = int(packet["t"][-1])
        if begin is None:
            begin = 0
            end = begin + 1
        else:
            assert end is not None
            end += 1
        jobs.append(
            {
                "name": name,
                "begin": timestamp_to_timecode(0),
                "end": timestamp_to_timecode(end - begin),
                "filters": ["default"],
                "tasks": [
                    "colourtime-viridis",
                    "colourtime-prism",
                    "event-rate",
                    "video",
                ],
            }
        )
    with open(with_suffix(configuration_path, ".part"), "w") as configuration_file:
        configuration_file.write("# output directory\n")
        toml.dump({"directory": "renders"}, configuration_file, encoder=Encoder())

        configuration_file.write(
            "\n\n# filters configuration (filters are applied before tasks)\n\n"
        )
        toml.dump(
            {
                "filters": {
                    "default": {"type": "default", "icon": "⏳", "suffix": ""},
                    "arbiter_saturation": {
                        "type": "arbiter_saturation",
                        "icon": "🌩 ",
                        "suffix": "as20",
                        "threshold": 20,
                    },
                    "hot_pixels": {
                        "type": "hot_pixels",
                        "icon": "🌶",
                        "suffix": "hp3",
                        "ratio": 3.0,
                    },
                }
            },
            configuration_file,
            encoder=Encoder(),
        )

        configuration_file.write("\n\n# tasks configuration\n\n")
        toml.dump(
            {
                "tasks": {
                    "colourtime-viridis": {
                        "type": "colourtime",
                        "icon": "🎨",
                        "colormap": "viridis",
                        "alpha": 0.1,
                        "png_compression_level": 6,
                        "background_color": "#191919",
                    },
                    "colourtime-prism": {
                        "type": "colourtime",
                        "icon": "🎨",
                        "colormap": "prism",
                        "alpha": 0.1,
                        "png_compression_level": 6,
                        "background_color": "#191919",
                    },
                    "event-rate": {
                        "type": "event_rate",
                        "icon": "🎢",
                        "long_tau": timestamp_to_timecode(1000000),
                        "short_tau": timestamp_to_timecode(10000),
                        "long_tau_color": "#4285F4",
                        "short_tau_color": "#C4D7F5",
                        "axis_color": "#000000",
                        "main_grid_color": "#555555",
                        "secondary_grid_color": "#DDDDDD",
                        "width": 1280,
                        "height": 720,
                    },
                    "video": {
                        "type": "video",
                        "icon": "🎬",
                        "frametime": timestamp_to_timecode(20000),
                        "tau": timestamp_to_timecode(200000),
                        "style": "exponential",
                        "on_color": "#F4C20D",
                        "off_color": "#1E88E5",
                        "idle_color": "#191919",
                        "cumulative_ratio": 0.01,
                        "timecode": True,
                        "h264_crf": 15,
                        "ffmpeg": "ffmpeg",
                    },
                },
            },
            configuration_file,
            encoder=Encoder(),
        )
        configuration_file.write(
            "\n\n# jobs\n# the same source file can be used in multiple jobs if begin, end, or filters are different\n\n"
        )
        toml.dump(
            {"jobs": jobs},
            configuration_file,
            encoder=Encoder(),
        )
        toml.dump(
            {"sources": {name: str(path) for name, path in zip(names, paths)}},
            configuration_file,
            encoder=Encoder(),
        )
    with open(with_suffix(configuration_path, ".part")) as configuration_file:
        jsonschema.validate(
            toml.load(configuration_file),
            render_configuration_schema(),
        )
    with_suffix(configuration_path, ".part").rename(configuration_path)
    sys.exit(0)

if args.command == "run":
    configuration_path = pathlib.Path(args.configuration).resolve()
    with open(configuration_path) as configuration_file:
        configuration = toml.load(configuration_file)
    jsonschema.validate(configuration, render_configuration_schema())
    for job in configuration["jobs"]:
        if not job["name"] in configuration["sources"]:
            error(f"\"{job['name']}\" is not listed in sources")
        if "filters" in job:
            for filter in job["filters"]:
                if not filter in configuration["filters"]:
                    error(f"unknown filter \"{filter}\" in \"{job['name']}\"")
        if "tasks" in job:
            for task in job["tasks"]:
                if not task in configuration["tasks"]:
                    error(f"unknown task \"{task}\" in \"{job['name']}\"")
        try:
            timecode(job["begin"])
        except Exception as exception:
            error(
                f"parsing \"begin\" ({job['begin']}) in \"{job['name']}\" failed ({exception})"
            )
        try:
            timecode(job["end"])
        except Exception as exception:
            error(
                f"parsing \"end\" ({job['end']}) in \"{job['name']}\" failed ({exception})"
            )
    configuration["filters"] = {
        name: {
            "type": filter["type"],
            "icon": filter["icon"],
            "suffix": filter["suffix"],
            "parameters": {
                key: value
                for key, value in filter.items()
                if key != "type" and key != "icon" and key != "suffix"
            },
        }
        for name, filter in configuration["filters"].items()
    }
    configuration["tasks"] = {
        name: {
            "type": task["type"],
            "icon": task["icon"],
            "parameters": {
                key: value
                for key, value in task.items()
                if key != "type" and key != "icon"
            },
        }
        for name, task in configuration["tasks"].items()
    }
    directory = pathlib.Path(configuration["directory"])
    if directory.is_absolute():
        directory = directory.resolve()
    else:
        directory = (configuration_path.parent / directory).resolve()
    info("📁", f'output directory "{directory}"\n')
    directory.mkdir(parents=True, exist_ok=True)
    for index, job in enumerate(configuration["jobs"]):
        begin = timecode(job["begin"])
        end = timecode(job["end"])
        name = f"{job['name']}-b{timestamp_to_short_timecode(begin)}-e{timestamp_to_short_timecode(end)}"
        if "filters" in job and len(job["filters"]) > 0:
            for filter_name in job["filters"]:
                if len(configuration["filters"][filter_name]["suffix"]) > 0:
                    name += f'-{configuration["filters"][filter_name]["suffix"]}'
        (directory / name).mkdir(exist_ok=True)
        info(
            animals.composite_name_to_icon(job["name"]),
            f"{index + 1}/{len(configuration['jobs'])} {format_bold(name)}",
        )
        output_path = directory / name / f"{name}.es"
        parameters_path = directory / name / "parameters.toml"
        parameters = load_parameters(parameters_path)
        if parameters is None:
            parameters = {}
        if not "filters" in parameters:
            parameters["filters"] = {}
        if not "tasks" in parameters:
            parameters["tasks"] = {}
        if len(job["filters"]) == 1:
            filter_name = job["filters"][0]
            filter = configuration["filters"][filter_name]
            if (
                not args.force
                and filter_name in parameters["filters"]
                and compare_parameters(
                    parameters["filters"][filter_name], filter["parameters"]
                )
                and output_path.is_file()
            ):
                info("⏭ ", f"skip filter {filter_name}")
            else:
                info(filter["icon"], f"apply filter {filter_name}")
                FILTERS[filter["type"]](
                    pathlib.Path(configuration["sources"][job["name"]]),
                    with_suffix(output_path, ".part"),
                    begin,
                    end,
                    filter["parameters"],
                )
                with_suffix(output_path, ".part").rename(output_path)
                parameters["filters"][filter_name] = filter["parameters"]
                save_parameters(parameters_path, parameters)
        else:
            if (
                not args.force
                and all(
                    (
                        filter_name in parameters["filters"]
                        and compare_parameters(
                            parameters["filters"][filter_name],
                            configuration["filters"][filter_name]["parameters"],
                        )
                    )
                    for filter_name in job["filters"]
                )
                and output_path.is_file()
            ):
                info("⏭ ", f"skip filters {' + '.join(job['filters'])}")
            else:
                with tempfile.TemporaryDirectory(
                    suffix=job["name"]
                ) as temporary_directory_name:
                    temporary_directory = pathlib.Path(temporary_directory_name)
                    input = pathlib.Path(configuration["sources"][job["name"]])
                    for index, filter_name in enumerate(job["filters"]):
                        if index == len(job["filters"]) - 1:
                            output = with_suffix(output_path, ".part")
                        else:
                            output = temporary_directory / f"{uuid.uuid4()}.es"
                        filter = configuration["filters"][filter_name]
                        info(filter["icon"], f"apply filter {filter_name}")
                        FILTERS[filter["type"]](
                            input,
                            output,
                            begin,
                            end,
                            filter["parameters"],
                        )
                        input = output
                        parameters["filters"][filter_name] = filter["parameters"]
                with_suffix(output_path, ".part").rename(output_path)
                save_parameters(parameters_path, parameters)
        for task_name in job["tasks"]:
            task = configuration["tasks"][task_name]
            task_output_path = (
                directory / name / f"{name}-{task_name}{TASKS[task['type']][0]}"
            )
            if (
                not args.force
                and task_name in parameters["tasks"]
                and compare_parameters(
                    parameters["tasks"][task_name], task["parameters"]
                )
                and output_path.is_file()
            ):
                info("⏭ ", f"skip task {task_name}")
            else:
                info(task["icon"], f"run task {task_name}")
                TASKS[task["type"]][1](
                    output_path,
                    with_suffix(task_output_path, ".part"),
                    end - begin,
                    task["parameters"],
                )
                with_suffix(task_output_path, ".part").rename(task_output_path)
                parameters["tasks"][task_name] = task["parameters"]
                save_parameters(parameters_path, parameters)

        if index < len(configuration["jobs"]) - 1:
            sys.stdout.write("\n")
    sys.exit(0)
