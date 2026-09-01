"""
SCFV v7.2 - Parser formal del DSL con Lark
"""
import lark
from pathlib import Path
from typing import Dict, List, Any, Optional

class SCFVParser:
    def __init__(self):
        grammar_path = Path(__file__).parent / "grammar.lark"
        with open(grammar_path, "r") as f:
            grammar = f.read()
        self.parser = lark.Lark(grammar, start="start", parser="lalr")

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        try:
            tree = self.parser.parse(text)
        except lark.exceptions.UnexpectedInput as e:
            raise SyntaxError(f"Error de sintaxis en {filepath}: {e}")
        return self._transform_tree(tree)

    def parse_string(self, text: str) -> Dict[str, Any]:
        try:
            tree = self.parser.parse(text)
        except lark.exceptions.UnexpectedInput as e:
            raise SyntaxError(f"Error de sintaxis: {e}")
        return self._transform_tree(tree)

    def _get_node_value(self, node):
        """Obtiene el valor de un nodo (Token o Tree)."""
        if hasattr(node, 'value'):   # es Token
            return node.value
        elif hasattr(node, 'children') and node.children:
            # es Tree, tomar el primer hijo
            return self._get_node_value(node.children[0])
        return None

    def _transform_tree(self, tree: lark.Tree) -> Dict[str, Any]:
        result = {"fractales": {}, "contexto": {}, "tetrada": {}, "booleano": {}}
        for child in tree.children:
            if child.data == "fractal_def":
                name = self._get_node_value(child.children[0])
                rules = []
                for node in child.children[1:]:
                    if node.data == "rule":
                        rule_name = self._get_node_value(node.children[0])
                        cond_expr = self._extract_condition(node)
                        actions = self._extract_actions(node)
                        rules.append({"name": rule_name, "condition": cond_expr, "actions": actions})
                result["fractales"][name] = rules

            elif child.data == "contexto_def":
                for section_node in child.children:
                    if section_node.data == "contexto_section":
                        section_name = self._get_node_value(section_node.children[0])
                        params = self._extract_assignments(section_node)
                        result["contexto"][section_name] = params

            elif child.data == "tetrada_def":
                for item in child.children:
                    if item.data == "tetrada_item":
                        name = self._get_node_value(item.children[0])
                        value = self._get_node_value(item.children[1])
                        if isinstance(value, str) and value.startswith('"'):
                            value = value.strip('"')
                        result["tetrada"][name] = value

            elif child.data == "booleano_def":
                for item in child.children:
                    if item.data == "booleano_item":
                        name = self._get_node_value(item.children[0])
                        value = self._get_node_value(item.children[1])
                        if isinstance(value, str) and value.startswith('"'):
                            value = value.strip('"')
                        result["booleano"][name] = value

        return result

    def _extract_condition(self, node) -> str:
        for child in node.children:
            if child.data == "condition":
                tokens = []
                for sub in child.children:
                    if sub.data == "comparison":
                        left = self._get_node_value(sub.children[0])
                        op = self._get_node_value(sub.children[1]) if sub.children[1].data == "value" else "?"
                        right = self._get_node_value(sub.children[2])
                        tokens.append(f"{left} {op} {right}")
                    elif sub.data == "value":
                        tokens.append(str(self._get_node_value(sub)))
                    else:
                        tokens.append(" " + str(self._get_node_value(sub)))
                return " ".join(tokens)
        return ""

    def _extract_actions(self, node) -> List[str]:
        actions = []
        for child in node.children:
            if child.data == "action":
                if child.children[0].data == "assignment":
                    name = self._get_node_value(child.children[0].children[0])
                    value = self._expr_to_str(child.children[0].children[1])
                    actions.append(f"{name} = {value}")
                elif child.children[0].data == "generate":
                    params = self._extract_param_list(child.children[0])
                    actions.append(f"GENERAR CONSECUENCIA ({', '.join(f'{k}={v}' for k,v in params.items())})")
        return actions

    def _extract_param_list(self, node) -> Dict[str, str]:
        params = {}
        for child in node.children:
            if child.data == "param":
                name = self._get_node_value(child.children[0])
                value = self._get_node_value(child.children[1])
                if isinstance(value, str) and value.startswith('"'):
                    value = value.strip('"')
                params[name] = value
        return params

    def _extract_assignments(self, section_node) -> Dict[str, str]:
        """Extrae asignaciones de una sección (sin comas)."""
        params = {}
        for child in section_node.children:
            if child.data == "assignment":
                name = self._get_node_value(child.children[0])
                value = self._get_node_value(child.children[1])
                if isinstance(value, str) and value.startswith('"'):
                    value = value.strip('"')
                elif isinstance(value, str) and value.startswith('['):
                    try:
                        value = eval(value)
                    except:
                        pass
                params[name] = value
        return params

    def _expr_to_str(self, node) -> str:
        if node.data == "value":
            return str(self._get_node_value(node))
        elif node.data == "comparison":
            left = self._expr_to_str(node.children[0])
            op = self._get_node_value(node.children[1])
            right = self._expr_to_str(node.children[2])
            return f"{left} {op} {right}"
        else:
            return str(self._get_node_value(node))
