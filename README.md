Render is a toolbox to organise and visualise Event Stream (.es) recordings.

## Install render

1. Clone this repository (notice the `--recursive` flag)

```sh
git clone --recursive https://github.com/neuromorphicsystems/render
```

2. Install the dependencies for your platform for command_line_tools (see https://github.com/neuromorphic-paris/command_line_tools#dependencies)

3. Compile command_line_tools

```sh
cd render/command_line_tools
premake4 gmake
cd build
make
```

3. Install Python dependencies

```sh
pip3 install -r requirements.txt
```

## Use render

1.  Generate a configuration file

```sh
python3 render.py configure /path/to/recordings/directory
```

2. Edit the generated _render-configuration.toml_

3. Run the configured tasks

```sh
python3 render.py run
```

## Format and lint

```
isort .; black .; pyright .
```
