//-----------------------------------------------------------------------------
// File: src/out.rs
// Author: David Lenfesty
// Copyright (c) 2020. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------
use std::string::String;
use std::collections::HashMap;

use serde::Serialize;

/// Describes a module (non-local) parameter.
//#[derive(Debug, Serialize)]
//    pub struct ModuleParameter {
//    pub dimension: String, - fields[3]
//    pub name: String, - fields[4]
//    pub value: String, - [fields[6]]
//}

/// Describes a module or interface port.
//#[derive(Debug, Serialize)]
//pub struct Port {
//    pub direction: String, - fields[0]
//    pub net_type: String, - fields[1]
//    pub dimension: String, - fields[3]
//    pub name: String, - fields[4]
//}

/// Describes a module declaration.
#[derive(Debug, Serialize)]
pub struct SvModule {
    pub name: String,
    pub parameters: Vec<[String; 7]>,
    pub ports: Vec<[String; 6]>,
    pub endname: String, // Is this the module identifier?
    pub include: bool,
    pub path: String,
    pub submodules: HashMap<String, String>,
}

/// Describes an interface declaration.
#[derive(Debug, Serialize)]
pub struct SvInterface {
    pub name: String,
    pub endname: String,
    pub ports: Vec<[String; 6]>,
    pub include: bool,
    pub path: String,
}

/// Describes a package declaration.
#[derive(Debug, Serialize)]
pub struct SvPackage {
    pub name: String,
    pub endname: String,
    pub include: bool,
    pub path: String,
}

/// Describes hierarchy of a given module.
#[derive(Debug, Serialize)]
pub struct SvHierarchy {
    pub include: bool,
    pub tree: serde_yaml::Value,
}
