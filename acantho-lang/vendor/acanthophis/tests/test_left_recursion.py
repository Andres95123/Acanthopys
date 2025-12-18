import unittest
from parser import Parser
from utils.generators import CodeGenerator
from testing.runner import run_tests_in_memory
from utils.logging import Logger

class TestLeftRecursion(unittest.TestCase):
    def test_left_recursion(self):
        grammar_text = r"""
grammar LeftRec:
    tokens:
        NUM: \d+
        PLUS: \+
        WS: skip \s+
    end

    start rule Expr:
        | left:Expr PLUS right:Term -> Add(left, right)
        | t:Term -> pass
    end

    rule Term:
        | n:NUM -> Num(int(n))
    end
    
    test ExprTests:
        "1 + 2" => Yields(Add(Num(1), Num(2)))
        "1 + 2 + 3" => Yields(Add(Add(Num(1), Num(2)), Num(3)))
    end
end
"""
        
        parser = Parser()
        grammars = parser.parse(grammar_text)
        self.assertEqual(len(grammars), 1)
        grammar = grammars[0]
        
        generator = CodeGenerator(grammar)
        code = generator.generate()
        
        # Print code for debugging if needed
        # print(code)
        
        logger = Logger(use_color=False)
        success = run_tests_in_memory(grammar, code, logger=logger)
        self.assertTrue(success, "Integrated tests failed for left recursion grammar")

    def test_complex_grammar_coverage(self):
        grammar_text = r"""
grammar Complex:
    tokens:
        NUM: \d+
        ID: [a-z]+
    end
    
    start rule Main:
        | items:Item+ -> List(items)
        | opt:Item? -> Opt(opt)
        | star:Item* -> Star(star)
    end
    
    rule Item:
        | i:ID -> Id(i)
    end
end
"""
        parser = Parser()
        grammars = parser.parse(grammar_text)
        # Enable recovery to cover that path in generator
        generator = CodeGenerator(grammars[0], enable_recovery=True)
        code = generator.generate()
        
        logger = Logger(use_color=False, verbose=True)
        # We don't have integrated tests in this grammar, so run_tests_in_memory might just return True or do nothing.
        # But generating the code is what we need for generator coverage.
        run_tests_in_memory(grammars[0], code, logger=logger)

if __name__ == '__main__':
    unittest.main()
