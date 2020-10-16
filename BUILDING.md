# Getting Started with development.

Building and install the GUI is quite easy, but may take a bit of setup.

## Setup

Ensure you have a recent version of python (>= 3.7). Then install the rust
toolchain. I recommend using [rustup.rs](https://rustup.rs). As well, install
maturin:

```
pip install maturin
```

## Building rSVParser

```
cd rSVParser
maturin develop --release
```

`maturin develop` installs rSVParser as a python package, and if you need to create
a wheel file, `maturin build` will do that for you. (Not the parser is much slower
when compiled in debug mode, which will happen if you don't specify `--release`).

If you just want to work with rSVParser, you can run it with `cargo` directly, i.e.
with `cargo run` or `cargo install`.

## Installing pyVerifGUI

This one-liner will install and launch pyVerifGUI for a quick workflow. It will also install
dependencies.

```
python setup.py install && VerifGUI
```

*Note: python development headers for pyside2 maybe needed to install the app
correctly. This has been seen on Ubuntu and Fedora, where the packages can be
installed with`python<version>-dev` and `python<version>-devel`,
respectively.*

## Documentation

### pyVerifGUI (Doxygen)

You need to install [Doxygen](https://www.doxygen.nl/index.html) and graphviz.

On ubuntu, these are found with the `doxygen` and `graphviz` packages.

Then:

```
cd pyVerifGUI
doxygen Doxyfile
```

### rSVParser (cargo docs)

Rust has default built-in documentation tools, so we use those.

To build them:

```
cd rSVParser
cargo docs
```
