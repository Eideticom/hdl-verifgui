//-----------------------------------------------------------------------------
// File: src/ports.rs
// Author: David Lenfesty
// Copyright (c) 2020. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------
// TODO find a way to include these once, instead of every time in every file
use std::vec::Vec;

use sv_parser::{unwrap_node, SyntaxTree, RefNode};

use crate::get_identifier;
use crate::ports::{get_ansi_ports, get_nonansi_ports};
use crate::out::SvInterface;

/// Parses full syntax tree for interfaces.
pub fn parse_tree(tree: &SyntaxTree, path: &String) -> Vec<SvInterface> {
    let mut interfaces = Vec::new();

    for node in tree {
        match node {
            RefNode::InterfaceDeclaration(x) => {
                let name = unwrap_node!(x, InterfaceIdentifier).unwrap();
                let name = get_identifier(name).unwrap();
                let name = String::from(tree.get_str(&name).unwrap().trim());

                // TODO not sure if this will actually work on an interface
                let ports = match unwrap_node!(x, ListOfPortDeclarations, ListOfPorts) {
                    Some(RefNode::ListOfPortDeclarations(_)) => {
                        get_ansi_ports(tree, node)
                    },
                    Some(RefNode::ListOfPorts(_)) => {
                        get_nonansi_ports(tree, node)
                    },
                    _ => {
                        println!("    No Ports found!");
                        Vec::new()
                    }
                };

                interfaces.push(SvInterface {
                    name: name.clone(),
                    endname: name,
                    ports: ports,
                    include: false,
                    path: path.clone(),
                });
            },
            _ => (),
        }
    }

    return interfaces;
}
