use std::fs::read_dir;
use std::path::PathBuf;

use glob::glob;

/// Results from globbing include files
pub struct GlobResults {
    /// List of files to parse
    pub files: Vec<PathBuf>,
    /// Include directories to pass to parser/preprocessor
    pub includes: Vec<PathBuf>,
}

/// Produces a list of all SystemVerilog and Verilog files in the included paths.
///
/// `add_includes` if true, will add all folders that files live in to the preprocessor includes
///
/// Will fail on invalid glob patterns, as well as failure to recurse into directories.
/// Will not fail if it can't read files.
pub fn glob_files(patterns: &Vec<String>, extensions: &Vec<String>, add_includes: bool) -> std::io::Result<GlobResults> {
    use std::io::{Error, ErrorKind};
    let mut files = Vec::new();
    let mut includes = Vec::new();

    for inc in patterns {
        // Attempt to glob string
        let entries = match glob(inc) {
            Ok(paths) => paths,
            Err(e) => {
                eprintln!("Invalid include pattern: {:?}", e);
                return Result::Err(Error::new(ErrorKind::InvalidInput, format!("Invalid glob pattern {}", inc)));
            }
        };

        for entry in entries {
            match entry {
                Ok(path) => {
                    if path.is_file() && check_file_extension(&path, extensions) {
                        add_parent(&path, add_includes, &mut includes);
                        files.push(path);
                    } else if path.is_dir() {
                        add_directory(&path, extensions, &mut files)?;
                    }
                },
                Err(e) => eprintln!("{:?}", e),
            };
        }
    }

    return Result::Ok(GlobResults {
        files: files,
        includes: includes,
    });
}

/// Add all files underneath a directory to the list of files
fn add_directory(path: &PathBuf, extensions: &Vec<String>, files: &mut Vec<PathBuf>) -> std::io::Result<()> {
    let dir_iter = match read_dir(path) {
        Ok(dir_iter) => dir_iter,
        Err(e) => {
            eprintln!("Could not open directory {:?}: {}", path, e);
            return Err(e);
        },
    };

    for dir in dir_iter {
        match dir {
            Ok(entry) => {
                let entry = entry.path();
                if entry.is_file() && check_file_extension(&entry, extensions) {
                    files.push(entry);
                }
            },
            Err(e) => {
                eprintln!("Error iterating over directories {:?}", e);
            },
        };
    }

    Ok(())
}

/// Add the parent of a file to the list of preprocessor includes
fn add_parent(file: &PathBuf, add_includes: bool, includes: &mut Vec<PathBuf>) {
    if !add_includes {
        return;
    }

    let parent = PathBuf::from(file.parent().unwrap());
    if !includes.contains(&parent) {
        includes.push(parent);
    }
}

/// Checks that the file extension of the given file is in the list of allowed extensions
fn check_file_extension(file: &PathBuf, extensions: &Vec<String>) -> bool {
    if let Some(ext) = file.extension() {
        let ext = String::from(ext.to_str().unwrap());
        if extensions.contains(&ext) {
            return true;
        }
    }

    return false;
}
