import re
from tree_sitter import Language, Parser
import tree_sitter_javascript
import tree_sitter_typescript

VAR_RE = re.compile(r'\bvar\s+(?=[a-zA-Z_$])')
REQUIRE_RE = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")
MODULE_EXPORTS_RE = re.compile(r'module\.exports\s*=\s*')
EXPORT_DEFAULT_RE = re.compile(r'(?:module\.)?exports\s*\.\s*(\w+)\s*=\s*')
FUNCTION_NO_RETURN_RE = re.compile(r'(function\s+\w+\s*\([^)]*\))\s*\{')

JS_TO_TS_RULES = [
    (r'\bundefined\b', 'undefined'),
    (r'//\s*@ts-check\n', ''),
]

TYPED_RETURNS = {
    'getElementById': 'HTMLElement | null',
    'querySelector': 'Element | null',
    'fetch': 'Promise<Response>',
    'JSON.parse': 'any',
    'JSON.stringify': 'string',
}


class JSToTSConverter:
    def __init__(self):
        self.js_parser = Parser(Language(tree_sitter_javascript.language()))
        self.ts_parser = Parser(Language(tree_sitter_typescript.language_typescript()))

    def convert(self, code: str) -> str:
        result = code
        result = self._ast_transform(result)
        result = self._transform_requires(result)
        result = self._transform_exports(result)
        result = self._transform_vars(result)
        result = self._add_types(result)
        result = self._regex_transform(result)
        return result

    def _ast_transform(self, code: str) -> str:
        try:
            tree = self.js_parser.parse(bytes(code, 'utf-8'))
            lines = list(code.split('\n'))
            self._visit(tree.root_node, lines)
            return '\n'.join(lines)
        except Exception:
            return code

    def _visit(self, node, lines):
        if node.type == 'variable_declaration':
            self._transform_var_decl(node, lines)
        if node.type == 'function_declaration':
            self._transform_fn_decl(node, lines)
        if node.type == 'arrow_function':
            pass
        for child in node.children:
            self._visit(child, lines)

    def _transform_var_decl(self, node, lines):
        """Convierte 'var' a 'const' o 'let'."""
        for child in node.children:
            if child.type == 'var':
                line = lines[child.start_point[0]]
                col = child.start_point[1]
                line = line[:col] + 'const' + line[col + 3:]
                lines[child.start_point[0]] = line

    def _transform_fn_decl(self, node, lines):
        """Agrega : any a parámetros si no tienen tipo."""
        fn_line = lines[node.start_point[0]]
        if ':' in fn_line[node.start_point[1]:node.end_point[1]]:
            return
        lines[node.start_point[0]] = fn_line.replace(')', '): any')

    def _transform_requires(self, code: str) -> str:
        def replace_require(m):
            var_name = m.group(1)
            module_path = m.group(2)
            if module_path.startswith('.'):
                if not module_path.endswith('.js') and not module_path.endswith('.ts'):
                    module_path += '.js'
                return f'import {var_name} from "{module_path}"'
            return f'import {var_name} from "{module_path}"'
        return REQUIRE_RE.sub(replace_require, code)

    def _transform_exports(self, code: str) -> str:
        code = MODULE_EXPORTS_RE.sub('export default ', code)
        return code

    def _transform_vars(self, code: str) -> str:
        return VAR_RE.sub('const ', code)

    def _add_types(self, code: str) -> str:
        code = FUNCTION_NO_RETURN_RE.sub(r'\1: void {', code)
        return code

    def _regex_transform(self, code: str) -> str:
        for pattern, replacement in JS_TO_TS_RULES:
            code = re.sub(pattern, replacement, code)
        return code

    def convert_file(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()
        return self.convert(code)
