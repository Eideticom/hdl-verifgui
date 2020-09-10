# rSVParser

rSVParser is a rust-based wrapper of sv-parser, a SystemVerilog parser.
rSVparser is used by VerifTools, generating the YAML output files the tooling
requires, and is not a generic systemverilog parser by any means.

[sv-parser](https://github.com/dalance/sv-parser)

## Installation

First install the rust toolchain by following the instructions on
(https::/rustup.rs):

(You will likely have to add `~/.cargo/bin` to your path as well.)

Then install!

```
cargo install --path ./
```

## Usage

Refer to the following for more help on specific argument usage.

```
rSVParser -h
```

The intent of this tool is to provide a broad overview of the RTL in
a given directory, sometimes with a specific focus on a provided
top level module.

The minimum usage of rSVParser looks something like this:

```
rSVParser project_name -I /path/to/rtl/dir
```

This will parse every Verilog and SystemVerilog file directly in the provided
directory, and write the output to the folder `sv_project_name`. The output
is 5 YAML files.

To specify a top module, add the flag `--top_module`. This uses
`project_name` as the top module. It will add include flags to files,
specifying which ones are needed by this module, and also ensure that the top
module has an entry in the hierarchy file.
