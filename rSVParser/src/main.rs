//-----------------------------------------------------------------------------
// File: src/main.rs
// Author: David Lenfesty
// Copyright (c) 2020. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------
//! # rSVParser
//! Drop in replacement for pySVParser.
//!
//! Generates a series of files in sv_* pattern, specific to Eideticom
//! VerifTools needs.
//!
//! ## Left to Do
//! TODO: interfaces aren't fully fleshed out
//!
//! TODO: add support for CLI-provided `define values
//!
//! TODO: Better error handling. Lots of places that could easily panic
//! with no info provided.

// not ideal, but eh
#![allow(non_snake_case)]

use std::collections::HashMap;
use std::path::PathBuf;
use std::fs::File;
use std::io::Read;

use sv_parser::{parse_sv, unwrap_node, Locate, RefNode};
use serde_yaml;
use structopt::StructOpt;
use includes::glob_files;

mod out;
mod modules;
mod interfaces;
mod packages;
mod hierarchy;
mod ports;
mod includes;

#[cfg(test)]
mod tests;

//use out::Port;

/// Static version string for CLI
const VERSION: &'static str = env!("CARGO_PKG_VERSION");

/// CLI Options
#[derive(Debug, StructOpt)]
#[structopt(name = "rSVParser", about = "Rust-based SystemVerilog parser utility.", version = VERSION)]
struct Opt {
    /// Name of project (will be used in top level directory name)
    pub project_name: String,

    /// Redo operations (i.e. delete old work)
    #[structopt(short, long)]
    pub redo: bool,

    /// Use project name as top module
    #[structopt(long = "--top_module")]
    pub top_module: bool,

    /// Includes the directory and all subdirectories in parsing
    #[structopt(short = "-I", long = "--include")]
    pub includes: Vec<String>,

    /// Include directories to pass only to parser preprocessor
    #[structopt(long)]
    pub pp_includes: Vec<PathBuf>,

    /// Only pass manually specified include directories (with --pp-includes) to parser preprocessor
    #[structopt(long)]
    pub manual_pp_includes: bool,

    /// Skip parsing files with "sv" extensions
    #[structopt(long)]
    pub skip_sv: bool,

    /// Skip parsing files with "v" extensions
    #[structopt(long)]
    pub skip_v: bool,

    /// Specify another file extension to parse as SystemVerilog
    #[structopt(long = "--extension")]
    pub extensions: Vec<String>,
}

fn main() -> Result<(), std::io::Error> {
    let opt = Opt::from_args();

    // Output directory path
    let base_path = PathBuf::from(format!("sv_{}", opt.project_name));
    std::fs::create_dir_all(&base_path).unwrap();
    backup_files(&base_path);

    // Construct list of allowed extensions
    let mut extensions = Vec::new();
    if !opt.skip_sv {
        extensions.push(String::from("sv"));
    }
    if !opt.skip_v {
        extensions.push(String::from("v"));
    }
    extensions.extend(opt.extensions);

    let mut globs = glob_files(&opt.includes, &extensions, !opt.manual_pp_includes)?;
    globs.includes.extend(opt.pp_includes);

    let mut sv_files = HashMap::new();
    let mut sv_modules = HashMap::new();
    let mut sv_interfaces = HashMap::new();
    let mut sv_packages = HashMap::new();
    let mut error = false;
    for file in &globs.files {
        // Build up sv_files
        // XXX I'm sure there's a cleaner way to do this
        let path = String::from(file.to_str().unwrap());
        let mut f = HashMap::new();
        // XXX lots of clones going on here
        f.insert(path.clone(), false);
        let filename = file.file_name().unwrap().to_str().unwrap();
        sv_files.insert(String::from(filename),f);

        // Parse files
        // parse_sv(
        //  path: T,
        //  pre_defines: &Defines<V>,
        //  include_paths: &[U],
        //  ignore_include: bool,
        //  allow_incomplete: bool,
        // )
        let result = parse_sv(&file, &HashMap::new(), &globs.includes, false, false);

        match result {
            Ok((syntax_tree, _)) => {
                println!("Parsing file {}...", path);

                for module in modules::parse_tree(&syntax_tree, &path) {
                    println!("- Found module {}", module.name);
                    sv_modules.insert(module.name.clone(), module);
                }
                for interface in interfaces::parse_tree(&syntax_tree, &path) {
                    println!("- Found interface {}", interface.name);
                    sv_interfaces.insert(interface.name.clone(), interface);
                }
                for package in packages::parse_tree(&syntax_tree, &path) {
                    println!("- Found package {}", package.name);
                    sv_packages.insert(package.name.clone(), package);
                }
            },
            Err(sv_parser::Error::Parse(Some((file, location)))) => {
                println!("- parse error");
                error = true;
                print_parse_error(file, location)?;
            },
            Err(e) => {
                eprintln!("{}", e);
            },
        }
    }

    let top_module = match opt.top_module {
        true => {
            println!("Top module specified!");
            Some(&opt.project_name)
        },
        false => None,
    };
    println!("Building module hierarchy...");
    let sv_hierarchy = hierarchy::build(&sv_modules, top_module);

    // Set whether files have been included or not
    match top_module {
        Some(_) => {
            for module in sv_modules.values() {
                let name = String::from(PathBuf::from(&module.path).file_name()
                                                                           .unwrap()
                                                                           .to_str()
                                                                           .unwrap());
                let name = String::from(name);
                let file = sv_files.get_mut(&name).unwrap();
                *file.get_mut(&module.path).unwrap() = true;
            }
        }
        None => (),
    }

    // Write outputs to filesystem
    serde_yaml::to_writer(&File::create(base_path.join("sv_modules.yaml")).unwrap(), &sv_modules).unwrap();
    serde_yaml::to_writer(&File::create(base_path.join("sv_interfaces.yaml")).unwrap(), &sv_interfaces).unwrap();
    serde_yaml::to_writer(&File::create(base_path.join("sv_packages.yaml")).unwrap(), &sv_packages).unwrap();
    serde_yaml::to_writer(&File::create(base_path.join("sv_files.yaml")).unwrap(), &sv_files).unwrap();
    serde_yaml::to_writer(&File::create(base_path.join("sv_hierarchy.yaml")).unwrap(), &sv_hierarchy).unwrap();

    if error {
        std::process::exit(-1);
    }
    return Ok(());
}

/// Pulls identifier value from any node.
fn get_identifier(node: RefNode) -> Option<Locate> {
    match unwrap_node!(node, SimpleIdentifier, EscapedIdentifier) {
        Some(RefNode::SimpleIdentifier(x)) => {
            Some(x.nodes.0)
        }
        Some(RefNode::EscapedIdentifier(x)) => {
            Some(x.nodes.0)
        }
        _ => None,
    }
}

/// Saves copies of files from old parse runs before overwriting
fn backup_files(base_path: &PathBuf) {
    for file in ["sv_modules.yaml", "sv_packages.yaml", "sv_interfaces.yaml", "sv_files.yaml", "sv_hierarchy.yaml"].iter() {
        let mut old_path = base_path.clone();
        old_path.push(file);
        let mut bak_path = base_path.clone();
        bak_path.push(String::from(*file) + ".bak");

        // Errors can simply be ignored
        // Actual fs errors will be caught later
        // XXX if we caught errors here we would avoid running when we know
        // we can't access the file system
        let _ = std::fs::rename(old_path, bak_path);
    }
}

/// Print the lines specified by parse errors.
///
/// XXX there's probably a crate that just does this, but better.
fn print_parse_error(file: PathBuf, location: usize) -> Result<(), std::io::Error> {
    let mut pos: usize = 0;
    let mut line = 0;
    let mut last_linefeed = 0;
    let mut f = std::fs::File::open(&file)?;
    let mut contents = String::new();
    let file_size = f.read_to_string(&mut contents)?;
    if file_size < pos {
        panic!();
    }

    while pos < location {
        if contents.as_bytes()[pos] == '\n' as u8 {
            line += 1;
            last_linefeed = pos;
        }
        pos += 1;
    }
    let column = pos - last_linefeed;
    let mut line_len = 1;
    while contents.as_bytes()[last_linefeed + line_len] != '\n' as u8 {
        line_len += 1;
    }

    let text = &contents[last_linefeed+1..last_linefeed+line_len];
    eprintln!("Parse error in {}:{}:{}", file.to_string_lossy(), line, column);
    eprintln!("| {}", text);
    eprintln!("{}^", " ".repeat(column + 2));

    return Ok(());
}
