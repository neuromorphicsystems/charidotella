Render is a toolbox to sort and visualise Event Stream (.es) data.

## Install render

1. Install the dependencies for your platform for command_line_tools: https://github.com/neuromorphic-paris/command_line_tools#dependencies

2. Compile command_line_tools

```sh
git clone --recursive https://github.com/neuromorphicsystems/render
cd command_line_tools
premake4 gmake
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

2. Edit _render-configuration.toml_

3. Run the configured tasks

```sh
python3 render.py run
```

## Format and lint

```
isort .; black .; pyright .
```
