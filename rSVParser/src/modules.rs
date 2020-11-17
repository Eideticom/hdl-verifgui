//-----------------------------------------------------------------------------
// File: src/modules.rs
// Author: David Lenfesty
// Copyright (c) 2020. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------
use std::vec::Vec;
use std::collections::HashMap;

use sv_parser::{unwrap_node, SyntaxTree, RefNode};

use crate::get_identifier;
use crate::ports::{get_ansi_ports, get_nonansi_ports};
use crate::out::SvModule;

/// Parses full syntax tree for modules.
pub fn parse_tree(tree: &SyntaxTree, path: &String) -> Vec<SvModule> {
    let mut modules = Vec::new();
    for node in tree {
        match node {
            RefNode::ModuleDeclaration(x) => {
                // Get Module name
                let name = unwrap_node!(x, ModuleIdentifier).unwrap();
                let name = get_identifier(name).unwrap();
                let name = String::from(tree.get_str(&name).unwrap().trim());

                // Get module parameters
                let parameters = get_params(tree, RefNode::ModuleDeclaration(x));

                // Get module ports
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

                let submodules = get_submodules(tree, RefNode::ModuleDeclaration(x));

                modules.push(SvModule {
                        name: name.clone(),
                        parameters: parameters,
                        ports: ports,
                        // XXX incorrect, but we'll leave it for now
                        endname: name,
                        // default to false, the modules included will be set true later
                        include: false,
                        path: path.clone(),
                        submodules: submodules,
                });
            },
            _ => (),
        }
    }

    return modules
}

/// Gets a list of submodules found in a module declaration.
/// More accurately finds all ModuleInstantiations under a given node.
fn get_submodules(tree: &SyntaxTree, module: RefNode) -> HashMap<String, String> {
    let mut submodules = HashMap::new();

    for node in module {
        match node {
            RefNode::ModuleInstantiation(x) => {
                // Module identifier
                let ident = unwrap_node!(x, ModuleIdentifier).unwrap();
                let ident = get_identifier(ident).unwrap();
                let ident = String::from(tree.get_str(&ident).unwrap());

                // Instance name
                let name = unwrap_node!(x, InstanceIdentifier).unwrap();
                let name = get_identifier(name).unwrap();
                let name = String::from(tree.get_str(&name).unwrap());

                submodules.insert(ident, name);
            },
            _ => (),
        }
    }

    return submodules;
}


/// Returns all (non-local) params of a module.
fn get_params(tree: &SyntaxTree, module: RefNode) -> Vec<[String; 7]> {
    let mut params = Vec::new();

    for node in module {
        match node {
            RefNode::ParameterDeclaration(param) => {
                let name = unwrap_node!(param, ParameterIdentifier).unwrap();
                let name = get_identifier(name).unwrap();
                let name = String::from(tree.get_str(&name).unwrap().trim());

                let dimension = match unwrap_node!(param, UnpackedDimension) {
                    Some(RefNode::UnpackedDimension(x)) => String::from(tree.get_str(x).unwrap().trim()),
                    _ => String::new(),
                };
                let value = match unwrap_node!(param, ConstantParamExpression) {
                    Some(RefNode::ConstantParamExpression(x)) => String::from(tree.get_str(x).unwrap().trim()),
                    _ => String::new(),
                };

                params.push([
                    String::from("parameter"),
                    String::new(),
                    String::new(),
                    dimension,
                    name,
                    String::new(),
                    value,
                ]);
            },
            _ => continue,
        }
    }

    return params;
}