# hdl-verifgui

This project aims to provide a GUI (Python/Qt5) for managing verification, coverage, and regression testing of synthesizable HDL in Linux like OS *(Windows - WSL2, WIP)*.

SystemVerilog is the default supported HDL (via Verilator and custom tooling). Nevertheless the project is structured to provide easy integration of other tools or languages like VHDL.

Included in this repository are two tools, `pyVerifGUI` and `rSVParser`. More specific information about these can be found in their respective README files.

## Installation

Install via python virtual environments (recommended)

Dependencies: (located by the tools with PATH)

- Python (>= 3.7)
- Verilator ([veripool](https://www.veripool.org/projects/verilator/wiki/Installing)) - ensure Verilator is added to the user PATH
- rSVParser, a rust [sv-parser](https://github.com/dalance/sv-parser) wrapper (included in this repo)

```bash
cd ~/
git clone https://github.com/Eideticom/hdl-verifgui.git

```

### rSVParser

***A rust [sv-parser](https://github.com/dalance/sv-parser) wrapper***

Dependencies:

- rust/cargo ([rustup.rs](https://rustup.rs))

rSVParser must be installed either with maturin directly or by using a provided wheel file
in order to use it with pyVerifGUI.

```bash
pip install maturin
cd rSVParser
maturin develop --release # use 'maturin build' to generate a wheel
```

Note: On release, wheel files will also be included in the download, and can be installed via `pip`.

### pyVerifGUI

pyVerifGUI must be installed either using `setup.py` or the wheel package.

*Note: Once a release is out, it will also be available on [PyPI ](https://pypi.org/) or [Conda ](https://docs.conda.io/en/latest/)(TBD)*

```bash
python setup.py install
# Launch app
VerifGUI
```

A wheel file for pyVerifGUI will also be included in the downloadable.

*Note: python development headers for pyside2 maybe needed to install the app correctly. This has been seen on Ubuntu and Fedora, where the packages can be installed with`python<version>-dev` and `python<version>-devel`, respectively.*

## License

hdl-verifgui is licensed under the [BSD 3-Clause license](https://github.com/Eideticom/hdl-verifgui/blob/master/LICENSE).
