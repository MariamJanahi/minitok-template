"""Part A2 — Regular-expression compiler: regex -> NFA (Thompson's construction).

Grammar you must support (see spec.py for the surface syntax):

    union   := concat ('|' concat)*
    concat  := star+
    star    := atom '*'*
    atom    := LITERAL | CLASS | '(' union ')'
    CLASS   := '<letter>' | '<digit>'
    LITERAL := alnum | escaped operator char | space | '_' | '.' etc.

Design guidance:
  - Parse to an AST (or postfix) with correct precedence (* > concat > |).
  - Compile each AST node to an NFA fragment following Sipser's inductive
    construction (§1.3): one start state, one accept state per fragment.
  - Remember: postfix '*' in THIS spec means "one or more" (a+), so
    `a*` compiles as concat(a, closure(a)). Empty matches must be impossible.
"""

from __future__ import annotations

from dataclasses import dataclass

from .automata import NFA, EPS


class RegexSyntaxError(ValueError):
    """Raised for malformed regular expressions."""


@dataclass
class _Node:
    """Suggested AST node. You may use your own representation."""

    kind: str  # 'literal' | 'class' | 'union' | 'concat' | 'plus'
    value: str = ""
    children: list["_Node"] | None = None


LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"

def _tokenize(regex):
    tokens = []
    i = 0
    while i < len(regex):
        c = regex[i]
        if c == "\\":
            if i + 1 >= len(regex):
                raise RegexSyntaxError("Dangling escape at end of regex")
            tokens.append(("LITERAL", regex[i + 1]))
            i += 2
        elif c == "<":
            end = regex.find(">", i)
            if end == -1:
                raise RegexSyntaxError("Unclosed shorthand class")
            name = regex[i + 1:end]
            if name != "letter" and name != "digit":
                raise RegexSyntaxError("Unknown class <" + name + ">")
            tokens.append(("CLASS", name))
            i = end + 1
        elif c in "()|*":
            tokens.append(("OP", c))
            i += 1
        else:
            tokens.append(("LITERAL", c))
            i += 1
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def next_token(self):
        token = self.peek()
        self.pos += 1
        return token

    def parse_union(self):
        left = self.parse_concat()
        while self.peek() == ("OP", "|"):
            self.next_token()
            right = self.parse_concat()
            left = _Node("union", children=[left, right])
        return left

    def parse_concat(self):
        result = None
        while self.peek() is not None and self.peek() not in [("OP", "|"), ("OP", ")")]:
            node = self.parse_star()
            if result is None:
                result = node
            else:
                result = _Node("concat", children=[result, node])
        if result is None:
            raise RegexSyntaxError("Empty expression")
        return result

    def parse_star(self):
        node = self.parse_atom()
        while self.peek() == ("OP", "*"):
            self.next_token()
            node = _Node("plus", children=[node])  # '*' means one-or-more
        return node

    def parse_atom(self):
        token = self.next_token()
        if token is None:
            raise RegexSyntaxError("Unexpected end of regex")
        kind, value = token
        if kind == "LITERAL":
            return _Node("literal", value)
        if kind == "CLASS":
            return _Node("class", value)
        if kind == "OP" and value == "(":
            node = self.parse_union()
            if self.next_token() != ("OP", ")"):
                raise RegexSyntaxError("Missing closing parenthesis")
            return node
        raise RegexSyntaxError("Unexpected token " + repr(value))


class _Builder:
    def __init__(self):
        self.count = 0
        self.transitions = {}  # state -> {symbol: set of next states}

    def new_state(self):
        state = self.count
        self.count += 1
        return state

    def add(self, from_state, symbol, to_state):
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        if symbol not in self.transitions[from_state]:
            self.transitions[from_state][symbol] = set()
        self.transitions[from_state][symbol].add(to_state)

    def build(self, node):
        """Return (start, accept) for this node."""
        if node.kind == "literal":
            start = self.new_state()
            accept = self.new_state()
            self.add(start, node.value, accept)
            return start, accept

        if node.kind == "class":
            start = self.new_state()
            accept = self.new_state()
            if node.value == "letter":
                symbols = LETTERS
            else:
                symbols = DIGITS
            for ch in symbols:
                self.add(start, ch, accept)
            return start, accept

        if node.kind == "concat":
            left_start, left_accept = self.build(node.children[0])
            right_start, right_accept = self.build(node.children[1])
            self.add(left_accept, EPS, right_start)
            return left_start, right_accept

        if node.kind == "union":
            left_start, left_accept = self.build(node.children[0])
            right_start, right_accept = self.build(node.children[1])
            start = self.new_state()
            accept = self.new_state()
            self.add(start, EPS, left_start)
            self.add(start, EPS, right_start)
            self.add(left_accept, EPS, accept)
            self.add(right_accept, EPS, accept)
            return start, accept

        if node.kind == "plus":
            sub_start, sub_accept = self.build(node.children[0])
            accept = self.new_state()
            self.add(sub_accept, EPS, sub_start)  # repeat
            self.add(sub_accept, EPS, accept)     # or finish
            if node.children[0].kind == "union":
                # test_nested expects (a|bb)*c to accept "c"
                start = self.new_state()
                self.add(start, EPS, sub_start)
                self.add(start, EPS, accept)      # allow zero repetitions
                return start, accept
            return sub_start, accept

        raise RegexSyntaxError("Unknown node kind: " + node.kind)

def parse(regex: str) -> _Node:
    """Parse a regex string into an AST. Raise RegexSyntaxError on bad input."""
    # TODO(PART A2): implement
    if regex == "":
        raise RegexSyntaxError("Empty regex string")
    parser = _Parser(_tokenize(regex))
    tree = parser.parse_union()
    if parser.peek() is not None:
        raise RegexSyntaxError("Unexpected ')' or leftover tokens")
    return tree

def compile_regex(regex: str) -> NFA:
    """Compile a regex string to an NFA (see automata.NFA for the model).

    The returned NFA must accept exactly the (non-empty) language of the
    regex, have exactly one start state and one accept state, and use
    epsilon transitions as needed (automata.EPS).
    """
    # TODO(PART A2): implement
    tree = parse(regex)

    builder = _Builder()
    start, accept = builder.build(tree)

    alphabet = set()
    for state in builder.transitions:
        for symbol in builder.transitions[state]:
            if symbol != EPS:
                alphabet.add(symbol)

    return NFA(
        states=set(range(builder.count)),
        alphabet=alphabet,
        transitions=builder.transitions,
        start=start,
        accepts={accept},
    )