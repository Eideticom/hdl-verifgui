# Python Verification GUI

This aims to be a useful GUI for managing verification, coverage, and
regression for our synthesizable verilog.

Help documentation is available in the application from the "Help" menu
at the top. This provides a link to a general getting started user guide.
The files for this documentation exist in `pyVerifGUI/assets/help`.

## Key Features

- Design information and Hierarchy
- Verilator Linting

### (To Be Released)
- Verilator Coverage
- Verilator Regression

## Running

The python package distributes an executable named `VerifGUI`.

```
VerifGUI -h # for usage help
```

Running the python directly from this directory does not work, so for
development it is recommended to use the command:

```
python setup.py install && VerifGUI
```

## Plugins

You can add new GUI elements (tabs) and new runners (tasks) via a plugin
system. By default the GUI loads these from `pyVerifGUI/gui/tabs/` and
`pyVerifGUI/tasks`, respectively, however you can also select external
folders (and individual files if choosing a whole folder to import causes
issues) via `--tabs` and `--tasks`. Implementing one of these plugins simply
means subclassing the correct task and attaching a decorator to it. There are
several caveats due to how plugins are imported:

- Module (and thus file) names must be unique, this is because the plugin
  directories are added to the PYTHONPATH temporarily to be imported.
  Choose a very unique name for your plugins to avoid this.
- All imports must be absolute.

To start implementing a plugin, it's recommended you start by creating a new
file in one of the built-in plugin directories, so you get code completion.
If you are developing one that is broadly useful we highly suggest upstreaming
it via a pull request to this repository. Otherwise, you can move it to an
external folder so you can use a packaged version.
