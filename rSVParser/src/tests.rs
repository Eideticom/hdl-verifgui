use std::path::PathBuf;

use super::includes::glob_files;

mod common {
    pub fn full_recursion() -> Vec<String> {
        vec![String::from("example/rtl/**/*")]
    }

    pub fn extensions(v: bool, sv: bool) -> Vec<String> {
        let mut extensions = Vec::new();

        if v { extensions.push(String::from("v")) }
        if sv { extensions.push(String::from("sv")) }

        extensions
    }
}

#[test]
/// Test that full recursion will add local files
fn local_recursion() {
    let patterns = common::full_recursion();
    let extensions = common::extensions(false, true);
    let results = glob_files(&patterns, &extensions, false).unwrap();

    assert!(results.files.contains(&PathBuf::from("example/rtl/adder.sv")));
    assert!(results.files.contains(&PathBuf::from("example/rtl/alu.sv")));
    assert!(results.files.contains(&PathBuf::from("example/rtl/dummy_test.sv")));
}

#[test]
/// Test that not including the .sv extension will filter out .sv files
fn ignore_sv() {
    let patterns = common::full_recursion();
    let extensions = common::extensions(false, false);
    let results = glob_files(&patterns, &extensions, false).unwrap();

    assert_eq!(results.files.len(), 0);
}

#[test]
/// Tests whether the automated preprocessor include folder generation works
fn include_folders() {
    let patterns = common::full_recursion();
    let extensions = common::extensions(false, true);
    let results = glob_files(&patterns, &extensions, true).unwrap();

    assert!(results.includes.contains(&PathBuf::from("example/rtl")));
    assert!(results.includes.contains(&PathBuf::from("example/rtl/unitblocks")));
    assert_eq!(results.includes.len(), 2);
}
