r"""Part A1 — Token specification loader and validator.

A token specification is a JSON object:

{
  "tokens": [
    {"name": "WS",    "regex": "( |\t|\n)*",        "skip": true},
    {"name": "FLOAT", "regex": "<digit>*.<digit>*", "skip": false},
    {"name": "INT",   "regex": "<digit>*",          "skip": false},
    {"name": "IDENT", "regex": "<letter>(<letter>|<digit>|_)*", "skip": false},
    {"name": "OP",    "regex": "==|=|\+|-|\*|/|<|>", "skip": false}
  ]
}

Regex syntax (a small extension of Sipser §1.3):
  literals          letters, digits, and the operator characters + - * / < > =
                    when they are NOT acting as operators (use \\ to escape
                    operator chars: \\* means literal asterisk)
  <letter>          shorthand class: a-z A-Z
  <digit>           shorthand class: 0-9
  a|b               union
  ab                concatenation
  a*                Kleene star (in this spec: ONE or more repetitions, i.e.
                    the regular operation a(a)*  — "plus" — because a token
                    must be non-empty; see README §A2)
  ( ... )           grouping
  Precedence: * > concatenation > |

`skip: true` token classes (typically whitespace/comments) are recognized
and discarded by the scanner instead of being emitted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class SpecError(ValueError):
    """Raised when a token specification is invalid."""


@dataclass
class TokenClass:
    name: str
    regex: str
    skip: bool = False


@dataclass
class TokenSpec:
    tokens: list[TokenClass] = field(default_factory=list)

    @property
    def names(self) -> list[str]:
        return [t.name for t in self.tokens]


def load_spec(source: str | Path) -> TokenSpec:
    """Load and validate a token specification from a JSON file path or a
    JSON string.

    Must raise SpecError (with a helpful message) for:
      - malformed JSON
      - missing/empty "tokens" list
      - duplicate token names
      - empty regex strings
      - regexes that can match the empty string (tokens must be non-empty)
      - unknown shorthand classes or unbalanced parentheses

    Returns a TokenSpec preserving the declared order (order defines
    priority for maximal-munch tie-breaking: earlier = higher priority).
    """
    # TODO(PART A1): implement
   
r"""Part A1 - Token specification loader and validator."""
import json
from pathlib import Path


class SpecError(ValueError):
    """Raised when a token specification is invalid."""
    pass


class TokenClass:
    def __init__(self, name, regex, skip=False):
        self.name = name
        self.regex = regex
        self.skip = skip


class TokenSpec:
    def __init__(self, tokens=None):
        self.tokens = list(tokens) if tokens is not None else []

    @property
    def names(self):
        return [token.name for token in self.tokens]

    def __iter__(self):
        return iter(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, index):
        return self.tokens[index]
class RegexChecker:
    r"""Walks through a regex once. It checks the syntax (parentheses and
    shorthand classes) and works out if the regex can match the empty string.

    Grammar (Kleene star here means one or more):
        union  -> concat ( '|' concat )*
        concat -> star*
        star   -> atom '*'*
        atom   -> '(' union ')' | <letter> | <digit> | \c | literal
    """

    def __init__(self, regex):
        self.regex = regex
        self.pos = 0

    def check(self):
        """Returns True if the regex can match the empty string."""
        nullable = self.parse_union()
        if self.pos < len(self.regex):
            # parse_union only stops early on a ')' that has no partner
            raise SpecError(
                "Unbalanced closing parenthesis in regex: {}".format(self.regex)
            )
        return nullable

    def parse_union(self):
        nullable = self.parse_concat()
        while self.pos < len(self.regex) and self.regex[self.pos] == "|":
            self.pos += 1
            if self.parse_concat():
                nullable = True
        return nullable

    def parse_concat(self):
        # empty concatenation matches the empty string
        nullable = True
        while self.pos < len(self.regex) and self.regex[self.pos] not in "|)":
            if not self.parse_star():
                nullable = False
        return nullable

    def parse_star(self):
        nullable = self.parse_atom()
        # a* means one or more, so it is empty only if a is empty
        while self.pos < len(self.regex) and self.regex[self.pos] == "*":
            self.pos += 1
        return nullable

    def parse_atom(self):
        regex = self.regex
        char = regex[self.pos]

        if char == "*":
            raise SpecError(
                "Nothing to repeat before '*' in regex: {}".format(regex)
            )

        if char == "(":
            self.pos += 1
            nullable = self.parse_union()
            if self.pos >= len(regex) or regex[self.pos] != ")":
                raise SpecError(
                    "Unbalanced opening parenthesis in regex: {}".format(regex)
                )
            self.pos += 1
            return nullable

        if char == "\\":
            if self.pos + 1 >= len(regex):
                raise SpecError(
                    "Regex ends with a lone backslash: {}".format(regex)
                )
            self.pos += 2
            return False

        if char == "<":
            end = regex.find(">", self.pos)
            if end != -1:
                shorthand = regex[self.pos + 1:end]
                # <word> is a shorthand class. Something like <|> is just
                # the literal characters < and >.
                if shorthand.isalpha():
                    if shorthand not in ("letter", "digit"):
                        raise SpecError(
                            "Unknown shorthand class <{}> in regex: {}".format(
                                shorthand, regex
                            )
                        )
                    self.pos = end + 1
                    return False
            # literal '<'
            self.pos += 1
            return False

        # any other character is a literal
        self.pos += 1
        return False


def validate_regex(regex):
    if not regex.strip():
        raise SpecError("Regex cannot be empty.")

    checker = RegexChecker(regex)
    if checker.check():
        raise SpecError(
            "Regex can match the empty string: {}".format(regex)
        )


def load_spec(source):
    """Load and validate a token specification from a JSON file path or a
    JSON string. Returns a TokenSpec in the declared order."""
    # Work out if source is a file or a JSON string
    file_path = None
    if isinstance(source, Path):
        file_path = source
    else:
        try:
            path_candidate = Path(str(source))
            if path_candidate.is_file():
                file_path = path_candidate
        except (OSError, ValueError):
            # a long JSON string is not a valid path
            file_path = None

    if file_path is not None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SpecError(
                "Failed to read specification file: {}".format(exc)
            ) from exc
    else:
        content = str(source)

    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SpecError("Malformed JSON: {}".format(exc)) from exc

    if not isinstance(data, dict):
        raise SpecError("Token specification root must be a JSON object.")

    if "tokens" not in data:
        raise SpecError("Missing required 'tokens' key.")

    raw_tokens = data["tokens"]
    if not isinstance(raw_tokens, list) or len(raw_tokens) == 0:
        raise SpecError("'tokens' must be a non-empty list.")

    spec = TokenSpec()
    seen_names = set()

    for item in raw_tokens:
        if not isinstance(item, dict):
            raise SpecError("Each token entry must be an object.")

        name = item.get("name")
        regex = item.get("regex")
        skip = item.get("skip", False)

        if not isinstance(name, str) or name == "":
            raise SpecError("Token name must be a non-empty string.")

        if name in seen_names:
            raise SpecError("Duplicate token name: {}".format(name))
        seen_names.add(name)

        if not isinstance(regex, str) or regex == "":
            raise SpecError("Token '{}' has an empty regex.".format(name))

        if not isinstance(skip, bool):
            raise SpecError(
                "Token '{}': 'skip' must be true or false.".format(name)
            )

        validate_regex(regex)

        spec.tokens.append(TokenClass(name, regex, skip))

    return spec
