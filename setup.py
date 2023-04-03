import pathlib
import subprocess
import shutil
import sys

import setuptools
import setuptools.command.build_ext
import setuptools.extension

dirname = pathlib.Path(__file__).resolve().parent

with open(dirname / "README.md") as file:
    long_description = file.read()

executables = ["es_to_frames", "event_rate", "size"]

if not "-h" in sys.argv and not "--help" in sys.argv:
    manifest_lines = [
        "include command_line_tools/source/*.hpp",
        "include command_line_tools/source/*.cpp",
        "include command_line_tools/premake4.lua",
        "include command_line_tools/third_party/pontella/source/pontella.hpp",
        "include command_line_tools/third_party/sepia/source/sepia.hpp",
        "include command_line_tools/third_party/tarsier/source/replicate.hpp",
        "include command_line_tools/third_party/tarsier/source/stitch.hpp",
        "include command_line_tools/third_party/stb_truetype.hpp",
    ]
    if "sdist" in sys.argv:
        manifest_lines.append(f"include configuration-schema.json")
    else:
        shutil.rmtree(dirname / "charidotella" / "assets", ignore_errors=True)
        (dirname / "charidotella" / "assets").mkdir()
        if sys.platform == "win32":
            subprocess.run(
                ["premake4", "vs2010"], cwd=dirname / "command_line_tools", check=True
            )
            for executable in executables:
                subprocess.run(
                    [
                        "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools\\MSBuild\\Current\\Bin\\MsBuild.exe",
                        "/p:PlatformToolset=v142",
                        "/property:Configuration=Release",
                        f"{executable}.vcxproj",
                    ],
                    check=True,
                    cwd=dirname / "command_line_tools" / "build",
                )
                (dirname / "charidotella" / "assets" / executable).unlink(
                    missing_ok=True
                )
                shutil.copy2(
                    dirname
                    / "command_line_tools"
                    / "build"
                    / "release"
                    / f"{executable}.exe",
                    dirname / "charidotella" / "assets" / executable,
                )
        else:
            if not (dirname / "command_line_tools" / "build" / "Makefile").is_file():
                subprocess.run(
                    ["premake4", "gmake"],
                    check=True,
                    cwd=dirname / "command_line_tools",
                )
            for executable in executables:
                subprocess.run(
                    ["make", executable],
                    check=True,
                    cwd=dirname / "command_line_tools" / "build",
                )
                shutil.copy2(
                    dirname / "command_line_tools" / "build" / "release" / executable,
                    dirname / "charidotella" / "assets" / executable,
                )
        for executable in executables:
            manifest_lines.append(f"include charidotella/assets/{executable}")
        shutil.copy2(
            dirname / "configuration-schema.json",
            dirname / "charidotella" / "assets" / "configuration-schema.json",
        )
        manifest_lines.append(f"include charidotella/assets/configuration-schema.json")
    with open("MANIFEST.in", "w") as manifest:
        content = "\n".join(manifest_lines)
        manifest.write(f"{content}\n")


setuptools.setup(
    name="charidotella",
    version="0.5",
    url="https://github.com/neuromorphicsystems/charidotella",
    author="Alexandre Marcireau",
    author_email="alexandre.marcireau@gmail.com",
    description="Charidotella is a toolbox to organise and visualise Event Stream (.es) recordings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=[
        "charidotella",
        "charidotella.filters",
        "charidotella.tasks",
        "charidotella.assets",
    ],
    include_package_data=True,
    package_data={"": ["charidotella/assets/*"]},
    install_requires=[
        "colourtime",
        "coolname",
        "event_stream",
        "jsonschema",
        "matplotlib",
        "scipy",
        "toml",
    ],
    ext_modules=[
        setuptools.extension.Extension(
            "charidotella_extension_placeholder",
            language="cpp",
            sources=["charidotella/charidotella_extension_placeholder.c"],
        ),
    ],
    entry_points={
        "console_scripts": [
            "charidotella = charidotella:main",
        ]
    },
)
