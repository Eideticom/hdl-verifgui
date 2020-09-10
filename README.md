# hdl-verifgui

This project aims to provide a useful GUI for managing verification, coverage, or regression testing of synthesizable HDL. Currently only SystemVerilog and
Verilog are supported (via Verilator and custom tooling), however we aim
to provide enough modularity to support adding other HDLs.

Included in this repository are two tools, `pyVerifGUI` and `rSVParser`.
More specific information about these can be found in their respective
READMEs.

## Installation

It is recommended you use a virtual environment to install all of the
python dependencies, as it will ensure you are using the correct version
of them.

You will need the following dependancies, everything must be in your PATH:

- Python (>= 3.7)
- Verilator
- git
- rSVParser (included in this repo)

### Verilator

Please visit [veripool](https://www.veripool.org/projects/verilator/wiki/Installing) for detailed installation instructions.

Ensure verilator is in your PATH.

### rSVParser

rSVParser can be installed using cargo directly, (cargo can be obtained via
[rustup.rs](https://rustup.rs)), or through the distributed python wheel package.

To install from source, you must have cargo installed:

```
pip install maturin
cd rSVParser
maturin develop --path rSVParser # use 'maturin build' to generate a wheel
```

On release, wheel files will also be included in the download, and can be
installed via `pip`.

### pyVerifGUI

pyVerifGUI must be installed either using `setup.py` or the wheel package.
Once a release is out, it will also be available on PyPI.

```
python setup.py install
```

A wheel file for pyVerifGUI will also be included in the downloadable.

*Note that you may have to install the python development headers for pyside2
to install correctly. This has been seen on Ubuntu and Fedora, where you can
install the packages `python<version>-dev` and `python<version>-devel`,
respectively.*

## License

hdl-verifgui is licensed under the [BSD 3-Clause license](https://github.com/Eideticom/hdl-verifgui/blob/master/LICENSE).
