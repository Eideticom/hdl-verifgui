//-----------------------------------------------------------------------------
// File: src/packages.rs
// Author: David Lenfesty
// Copyright (c) 2020. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------
use std::vec::Vec;

use sv_parser::{unwrap_node, SyntaxTree, RefNode};

use crate::get_identifier;
use crate::out::SvPackage;

/// Parses full file tree for package information.
pub fn parse_tree(tree: &SyntaxTree, path: &String) -> Vec<SvPackage> {
    let mut packages = Vec::new();

    for node in tree {
        match node {
            RefNode::PackageDeclaration(x) => {
                // XXX this could probably be a macro
                let name = unwrap_node!(x, PackageIdentifier).unwrap();
                let name = get_identifier(name).unwrap();
                let name = String::from(tree.get_str(&name).unwrap().trim());

                packages.push(SvPackage {
                    name: name.clone(),
                    endname: name,
                    include: false,
                    path: path.clone(),
                });
            },
            _ => (),
        }
    }

    return packages;
}