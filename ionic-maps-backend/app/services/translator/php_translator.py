import re
from tree_sitter import Language, Parser
import tree_sitter_php

MYSQL_RE = re.compile(r'\bmysql_connect\s*\(')
PDO_RE = re.compile(r'\bmysql_query\s*\(')
EREG_RE = re.compile(r'\bereg\s*\(')
EREGI_RE = re.compile(r'\beregi\s*\(')
EREG_REPLACE_RE = re.compile(r'\bereg_replace\s*\(')
SPLIT_RE = re.compile(r'\bsplit\s*\(')
MCRYPT_ENC_RE = re.compile(r'\bmcrypt_encrypt\s*\(')
MCRYPT_DEC_RE = re.compile(r'\bmcrypt_decrypt\s*\(')
AUTOLOAD_RE = re.compile(r'\b__autoload\b')
MAGIC_QUOTES_RE = re.compile(r'\bset_magic_quotes_runtime\s*\(')
GET_MAGIC_GPC_RE = re.compile(r'\bget_magic_quotes_gpc\s*\(')
ARRAY_EMPTY_RE = re.compile(r'\barray\s*\(\s*\)')
VOLD_RE = re.compile(r'\bvar\s+(?=\$)')
PHP_ECHO_RE = re.compile(r'<\?\s+echo\s+', re.IGNORECASE)
CLOSE_PHP_RE = re.compile(r'\?>\s*$')


class PHPTranslator:
    """Traduce codigo PHP 5.6/6 a PHP 8.2+ usando Tree-sitter + reglas."""

    def __init__(self):
        try:
            self.parser = Parser(Language(tree_sitter_php.language_php()))
            self.has_parser = True
        except Exception as e:
            print(f"PHP parser init error: {e}")
            self.has_parser = False

    def translate(self, code: str) -> str:
        result = code

        if self.has_parser:
            result = self._ast_transform(result)

        result = self._regex_transform(result)
        result = self._modernize_syntax(result)

        return result

    def _ast_transform(self, code: str) -> str:
        try:
            tree = self.parser.parse(bytes(code, 'utf-8'))
            return code
        except Exception:
            return code

    def _regex_transform(self, code: str) -> str:
        code = MYSQL_RE.sub('PDO::__construct(', code)
        code = PDO_RE.sub('PDO::query(', code)
        code = EREG_RE.sub('preg_match(', code)
        code = EREGI_RE.sub('preg_match(', code)
        code = EREG_REPLACE_RE.sub('preg_replace(', code)
        code = SPLIT_RE.sub('explode(', code)
        code = MCRYPT_ENC_RE.sub('openssl_encrypt(', code)
        code = MCRYPT_DEC_RE.sub('openssl_decrypt(', code)
        code = AUTOLOAD_RE.sub('spl_autoload_register', code)
        code = MAGIC_QUOTES_RE.sub('/* set_magic_quotes_runtime removed */', code)
        code = GET_MAGIC_GPC_RE.sub('/* get_magic_quotes_gpc always false */ false', code)
        return code

    def _modernize_syntax(self, code: str) -> str:
        code = ARRAY_EMPTY_RE.sub('[]', code)
        code = VOLD_RE.sub('public ', code)
        code = PHP_ECHO_RE.sub('<?php echo ', code)
        return code

    def translate_file(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()
        return self.translate(code)
