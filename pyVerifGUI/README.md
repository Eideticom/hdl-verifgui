# Python Verification GUI

This aims to be a useful GUI for managing verification, coverage, and
regression for our synthesizable verilog.

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
