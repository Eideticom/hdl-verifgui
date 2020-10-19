//-----------------------------------------------------------------------------
// File: src/hierarchy.rs
// Author: David Lenfesty
// Copyright (c) 2020. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------
use std::collections::HashMap;

use serde_yaml::Value;
use serde_yaml::mapping::Mapping;

use crate::out::{SvModule, SvHierarchy};

/// Creates a hierarchy of all modules in the design.
pub fn build(modules: &HashMap<String, SvModule>, top_module: Option<&String>) -> HashMap<String, SvHierarchy> {
    // Build list of top-level modules
    let mut top: Vec<&String> = modules.keys().collect();
    for module in modules.values() {
        for submod in module.submodules.keys() {
            // Remove any "top" modules that are submodules
            if let Some(module) = top_module {
                top.retain(|x| {*x == module || *x != submod});
            } else {
                top.retain(|x| {*x != submod});
            }
        }
    }
    // Remove top level modules that are not defined here
    println!("Ignoring modules not found in files...");
    let defined_modules: Vec<&String> = modules.keys().collect();
    top.retain(|x| defined_modules.contains(x));

    let mut yaml_out = HashMap::new();
    for module in top {
        let mut hier = Mapping::new();
        hier.insert(Value::String(module.clone()), build_tree(module, &modules));

        let include = match top_module {
            Some(top_module) => {
                if module == top_module {
                    true
                } else {
                    false
                }
            },
            None => false,
        };
        yaml_out.insert(module.clone(), SvHierarchy {
            include: include,
            tree: Value::Mapping(hier),
        });
    }

    return yaml_out;
}

/// Recursive function to build trees that describe module hierarchies.
fn build_tree(top: &String, modules: &HashMap<String, SvModule>) -> Value {
    match modules.get(top) {
        Some(module) => {
            let mut map = Mapping::new();
            for submod in module.submodules.keys() {
                map.insert(Value::String(submod.clone()), build_tree(submod, modules));
            }

            Value::Mapping(map)
        },
        None => {
            Value::Mapping(Mapping::new())
        },
    }
}
