# User Guide - Setting up a new project

The only thing required to integrate a new project for linting and parsing
is to create a configuration file.

If you are confused about terminology, you can open
[concepts.md](help/concepts.md).

## Installation

As outlined in the main README, the following dependancies must be installed:
- Python >= 3.7
  - Python dependancies can be installed by `pip install -r requirements.txt`
- Verilator
- rSVParser

## Configuration

A basic configuration file could look like this
(found in `configs/example.yaml`):

```YAML
#####
# Minimum required for parsing

top_module: alu
repo_name: alu
core_dir: ../example/alu
working_dir: tb/verilator/
rtl_dirs:
  rtl:
    recurse: false
  rtl/unitblocks:
    recurse: true
parse_args: ""
verif_tools_path: ../../
```

A few things to note here:
- All directories are relative, unless specified as absolute (i.e. leading `/`
  or `C:/`)
  - `core_dir` is relative to where the GUI is launched
  - everything else is relative to `core_dir`

As you may be able to tell, this configuration is for the simple ALU example
found in this repository.

### RTL Includes

The default behaviour is to recursively import all SystemVerilog or
Verilog files within the given RTL directories. The imports can be
specified as non-recursive by setting the `recurse` option to
`false`. There are additional arguments that can be added
to `parse_args` to modify some of this behaviour. Descriptions
of these arguments can be found with the command `rSVParser -h`.

## Launching

Now we can launch the application (no command line arguments are required by
default).

```
python3 gui.py
```

Click `Browse` next to the Configuration line in the `Overview` tab (the tab
you are greeted with). Then you can navigate to wherever your configuration
is located.

*The application can also be launched with the argument
`-c*path/to/config.yaml`, which means you do not have to do this step on
every application open.*

If there has been no work on this configuration before, you will be prompted
to select a task to run. This is because it always generates a defualt build
called `master`. You can either parse, or lint. Parsing goes through
the SystemVerilog files and provides a few files describing the overall
structure of the project.

Linting is dependant on Verilator to provide error and warning messages.

If there has been work done, you will need to select a build first, the
selection box for which is right below the configuration selection.

*Again, to save time on future opening, you can specify the build to load
with the argument `-b <build_name>`.*

Tasks can be reset within a build by clicking the `Reset <Task>` buttons,
present in the overview tab.

### Design Hierarchy

You can see the general tree of your project under the design tab. This tree
view lets you view your module hierarchy and even copy hierarchical names!
(right click on a module or select it and enter `CTRL-H`).

It also displays a simple textual description of the module for a broad overview.

Note that you need to have parsed your RTL before the hierarchy will display.

### Linting

After linting, any warning or error messages will be displayed in the
`Linter` tab. Here you can view and wave messages.

When you select a message, the file will be opened in the editor so you
can evaluate the message, and decide to waive it or not. Right clicking on
the message gives you some options for managing messages.

The `Diff View` section lets you see changes in messages between different
builds.

The `Orphan Cleanup` section lets you manage orphaned waivers when your files
change between linting sessions.
