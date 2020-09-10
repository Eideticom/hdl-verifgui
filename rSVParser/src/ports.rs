use std::vec::Vec;

use sv_parser::{unwrap_node, SyntaxTree, RefNode};

use crate::get_identifier;

/// Traverses the tree from a node and returns a vector of all port declarations.
/// Works for modules, however it needs a small tweak to work with interfaces as well.
pub fn get_ansi_ports(tree: &SyntaxTree, module: RefNode) -> Vec<[String; 6]> {
    let mut ports = Vec::new();
    for node in module {
        match node {
            RefNode::AnsiPortDeclaration(port) => {
                let direction = match unwrap_node!(port, PortDirection) {
                    Some(RefNode::PortDirection(x)) => {
                        String::from(tree.get_str(x).unwrap().trim())
                    },
                    // Can occur when using interfaces for example
                    _ => String::new(),
                };

                let net_type = match unwrap_node!(port, NetType, DataType) {
                    Some(RefNode::NetType(x)) => String::from(tree.get_str(x).unwrap().trim()),
                    Some(RefNode::DataType(x)) => {
                        // Split out first word. Some data types here get screwy and I don't
                        // feel like traversing the entire tree
                        String::from(tree.get_str(x).unwrap().split(" ").next().unwrap())
                    },
                    _ => String::new(),
                };

                let dimension = match unwrap_node!(port, PackedDimension) {
                    Some(RefNode::PackedDimension(x)) => String::from(tree.get_str(x).unwrap().trim()),
                    _ => String::new(),
                };

                let name = unwrap_node!(port, PortIdentifier).unwrap();
                let name = get_identifier(name).unwrap();
                let name = String::from(tree.get_str(&name).unwrap());

                ports.push([
                    direction,
                    net_type,
                    String::new(),
                    dimension,
                    name,
                    String::new(),
                ]);
            }
            _ => continue,
        }
    }

    return ports;
}

pub fn get_nonansi_ports(tree: &SyntaxTree, module: RefNode) -> Vec<[String; 6]> {
    let mut ports = Vec::new();
    for node in module {
        match node {
            RefNode::PortDeclaration(port) => {
                let direction = match unwrap_node!(port, PortDirection) {
                    Some(RefNode::PortDirection(x)) => {
                        String::from(tree.get_str(x).unwrap().trim())
                    },
                    // Can occur when using interfaces for example
                    _ => String::new(),
                };

                let net_type = match unwrap_node!(port, NetType, DataType) {
                    Some(RefNode::NetType(x)) => String::from(tree.get_str(x).unwrap().trim()),
                    Some(RefNode::DataType(x)) => {
                        // Split out first word. Some data types here get screwy and I don't
                        // feel like traversing the entire tree
                        String::from(tree.get_str(x).unwrap().split(" ").next().unwrap())
                    },
                    _ => String::new(),
                };

                let dimension = match unwrap_node!(port, PackedDimension) {
                    Some(RefNode::PackedDimension(x)) => String::from(tree.get_str(x).unwrap().trim()),
                    _ => String::new(),
                };

                let name = unwrap_node!(port, PortIdentifier).unwrap();
                let name = get_identifier(name).unwrap();
                let name = String::from(tree.get_str(&name).unwrap());

                ports.push([
                    direction,
                    net_type,
                    String::new(),
                    dimension,
                    name,
                    String::new(),
                ]);
            }
            _ => continue,
        }
    }

    return ports;
}
