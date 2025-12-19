import unittest
import textwrap
from parser import Parser as GrammarParser
from utils.generators import CodeGenerator

class TestGeneratedAPI(unittest.TestCase):
    def setUp(self):
        self.grammar_text = textwrap.dedent("""
        grammar Test:
            tokens:
                NUM: \d+
                PLUS: \+
                WS: skip \s+
            end
            
            start rule Expr:
                | left:Expr PLUS right:Term -> (left, right)
                | t:Term -> t
            end
            
            rule Term:
                | n:NUM -> int(n)
            end
        end
        """)
        parser = GrammarParser()
        grammars = parser.parse(self.grammar_text)
        if not grammars:
            raise ValueError("Failed to parse grammar in setUp")
        self.grammar = grammars[0]
        
        generator = CodeGenerator(self.grammar, enable_recovery=True)
        self.code = generator.generate()
        
        print(self.code) # Debug
        
        self.namespace = {}
        exec(self.code, self.namespace)
        self.Parser = self.namespace['Parser']
        self.Lexer = self.namespace['Lexer']

    def test_parse_success(self):
        result = self.Parser.parse("1 + 2")
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.ast, (1, 2))
        
    def test_parse_simple_types(self):
        # Let's use a grammar that returns tuples or ints
        grammar_text = textwrap.dedent("""
        grammar TestSimple:
            tokens:
                NUM: \d+
            end
            start rule Start:
                | n:NUM -> int(n)
            end
        end
        """)
        parser = GrammarParser()
        grammars = parser.parse(grammar_text)
        generator = CodeGenerator(grammars[0], enable_recovery=True)
        code = generator.generate()
        namespace = {}
        exec(code, namespace)
        Parser = namespace['Parser']
        
        result = Parser.parse("42")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.ast, 42)

    def test_parse_error(self):
        result = self.Parser.parse("1 +")
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        
    def test_parse_invalid_rule(self):
        with self.assertRaises(ValueError):
            self.Parser.parse("1", rule_name="NonExistent")

if __name__ == '__main__':
    unittest.main()
