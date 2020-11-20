from py_sv_parser import SyntaxTree, SyntaxNode, unwrap_node, unwrap_locate


def get_str_or_default(tree: SyntaxTree, node: SyntaxNode, type: str):
    node = unwrap_node(node, [type])
    if node is not None:
        node = unwrap_locate(node)
        return tree.get_str(node).strip()
    else:
        return ""
