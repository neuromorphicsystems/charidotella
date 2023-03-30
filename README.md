Charidotella (https://en.wikipedia.org/wiki/Charidotella_sexpunctata) is a toolbox to organise and visualise Event Stream (.es) recordings.

## Get started

1. Install the Python package

    ```sh
    pip3 install charidotella
    ```

2. Create a directory _my-wonderful-project_ with the following structure (the file names do not matter as long as their extension is *.es*)

    ```txt
    my-wonderful-project
    └── recordings
        ├── file_1.es
        ├── file_2.es
        ├── ...
        └── file_n.es
    ```

3. Generate a configuration file

    ```sh
    cd my-wonderful-project
    charidotella configure ./recordings
    ```

The directory now has the following structure

    ```txt
    my-wonderful-project
    ├── recordings
    │   ├── file_1.es
    │   ├── file_2.es
    │   ├── ...
    │   └── file_n.es
    └── charidotella-configuration.toml
    ```

4. (Optional) Edit `charidotella-coniguration.toml` to change the jobs' parameters

5. Run the jobs

    ```
    charidotella run
    ```
    The directory now has the following structure
    ```txt
    my-wonderful-project
    ├── recordings
    │   ├── file_1.es
    │   ├── file_2.es
    │   ├── ...
    │   └── file_n.es
    ├── renders
    │   ├── adjective-animal-1
    │   │    ├── filtered-recording.es
    │   │    ├── rendered-file-1.es
    │   │    ├── ...
    │   │    └── rendered-file-m.es
    │   ├── adjective-animal-2
    │   ├── ...
    │   └── adjective-animal-n
    └── charidotella-configuration.toml
    ```


6. (Optional) Edit or create new jobs and run `charidotella run` again (only new jobs will run)

See `charidotella --help` for a list of other options.

## Contribute

After code edits, run the formatters and linters.

```
isort .; black .; pyright .
```
