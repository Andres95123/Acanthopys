import re

GRAMMAR_PATTERN = re.compile(
    r"""
    (?ms)               
    ^\s*grammar\s+      
    (\w+)               
    \s*:\s*             
    (.*?)               
    ^end\b              
    [^\n]*              
""",
    re.VERBOSE,
)

TOKENS_BLOCK_PATTERN = re.compile(
    r"""
    (?ms)
    ^\s*tokens\s*:\s*   
    (.*?)               
    ^\s*end\b           
    [^\n]*              
""",
    re.VERBOSE,
)

RULE_PATTERN = re.compile(
    r"""
    (?ms)
    ^\s*
    (start\s+)?         
    rule\s+             
    (\w+)               
    \s*:\s*             
    (.*?)               
    ^\s*end\b           
    [^\n]*              
""",
    re.VERBOSE,
)

TOKEN_LINE_PATTERN = re.compile(
    r"""
    (?m)
    ^\s*                
    (\w+)               
    \s*:\s*             
    (skip\s+)?          
    ([^#\n]+)           
    (?:\s*\#.*)?        
    $
""",
    re.VERBOSE,
)

EXPRESSION_OPTION_PATTERN = re.compile(
    r"""
    (?m)
    ^\s*\|\s*           
    (.*?)\s*            
    ->\s*               
    ([^#\n]+)           
    (?:\s*\#.*)?        
    $
""",
    re.VERBOSE,
)

TERM_PATTERN = re.compile(
    r"""
    (?:                 
        (\w+)           
        :               
    )?
    (                   
        \w+             
        |               
        '[^']*'         
    )
    ([+*?])?
    """,
    re.VERBOSE,
)

TEST_BLOCK_PATTERN = re.compile(
    r"""
    (?ms)
    ^\s*test\s+         
    (\w+)               
    (?:
        \s+             
        (\w+)           
    )?
    \s*:\s*             
    (.*?)               
    ^\s*end\b           
    [^\n]*              
""",
    re.VERBOSE,
)

TEST_CASE_START_PATTERN = re.compile(
    r"""
    ^\s*
    (?:
        "([^"]*)"       
        |
        '([^']*)'       
    )
    \s*=>\s*            
    """,
    re.VERBOSE | re.MULTILINE,
)

CHECK_GUARD_PATTERN = re.compile(
    r"""
    \s+check\s+
    (.+?)
    \s+then\s+
    (.+?)
    (?:
        \s+else\s+then\s+
        (.+)
    )?
    $
    """,
    re.VERBOSE,
)
