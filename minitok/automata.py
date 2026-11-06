"""Parts A3/A4 — Finite automata models, determinization, and the scanner.

Data model (plain Python, no external deps):

  - An NFA is a set of states with transitions
        nfa.transitions[state][symbol] -> set of states
    symbol is a single character, or EPS (epsilon).
  - A DFA has a total transition function
        dfa.transitions[state][symbol] -> state
  - Accepting states of a tokenizer DFA are *labeled* with the token-class
    name they recognize (dfa.accepts[state] == "IDENT"), because one DFA
    serves the whole token specification.

The scanner performs MAXIMAL MUNCH (longest match wins) with PRIORITY
tie-breaking: among equally-long matches at the same position, the token
class declared earliest in the spec wins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

EPS = ""  # epsilon-transition marker


class ScanError(ValueError):
    """Raised when no token class matches at the current input position.

    `position` is the 0-based character offset of the failure."""

    def __init__(self, message: str, position: int):
        super().__init__(message)
        self.position = position


@dataclass
class NFA:
    states: set[int] = field(default_factory=set)
    alphabet: set[str] = field(default_factory=set)  # excludes EPS
    transitions: dict[int, dict[str, set[int]]] = field(default_factory=dict)
    start: int = 0
    accepts: set[int] = field(default_factory=set)

    def simulate(self, s: str) -> bool:
        """True iff this NFA accepts string s."""
        current = self._closure({self.start})

        for ch in s:
            next_states = set()
            for state in current:
                if state in self.transitions and ch in self.transitions[state]:
                    next_states.update(self.transitions[state][ch])
            current = self._closure(next_states)

        for state in current:
            if state in self.accepts:
                return True
        return False

    def _closure(self, states):
        """All states reachable from `states` using only epsilon moves."""
        result = set(states)
        to_visit = list(states)

        while to_visit:
            state = to_visit.pop()
            if state in self.transitions and EPS in self.transitions[state]:
                for next_state in self.transitions[state][EPS]:
                    if next_state not in result:
                        result.add(next_state)
                        to_visit.append(next_state)
        return result
        # TODO(PART A3): implement
        raise NotImplementedError("DFA.simulate is not implemented yet")


@dataclass
class DFA:
    states: set[int] = field(default_factory=set)
    alphabet: set[str] = field(default_factory=set)
    transitions: dict[int, dict[str, int]] = field(default_factory=dict)
    start: int = 0
    accept: dict[int, str] = field(defualt_factory=dict)


@dataclass
class Token:
    type: str
    lexeme: str
    position: int  # 0-based offset of the first character of the lexeme


def eps_closure(nfa: NFA, states: set[int]) -> set[int]:
    """Epsilon closure of a set of NFA states."""

    result = set(states)
    to_visit = list(states)

    while to_visit:
        state = to_visit.pop()

        if state in nfa.transitions and EPS in nfa.transitions[state]:
            for next_state in nfa.transitions[state][EPS]:
                if next_state not in result:
                    result.add(next_state)
                    to_visit.append(next_state)

    return result
    # TODO(PART A2/A3): implement
    raise NotImplementedError("eps_closure is not implemented yet")



def determinize(nfa: NFA, label_of: dict[int, str], priority: list[str]) -> DFA:
    """Subset construction (Sipser §1.2) producing a tokenizer DFA.

    label_of: NFA accept state -> token-class name.
    priority: token-class names from highest to lowest priority; when a
    DFA state contains several labeled NFA accept states, keep the label
    with the highest priority (this implements tie-breaking).
    Transitions must be total over `nfa.alphabet`.
    """

    start_state = frozenset(eps_closure(nfa, {nfa.start}))

    dfa_states = {start_state}
    unprocessed = [start_state]

    dfa_transitions = {}
    dfa_accepts = {}

    state_ids = {start_state: 0}

    while unprocessed:
        current = unprocessed.pop(0)
        current_id = state_ids[current]

        dfa_transitions[current_id] = {}

        matching_tokens = [
            label_of[state]
            for state in current
            if state in label_of
        ]

        if matching_tokens:
            chosen = min(
                matching_tokens,
                key=lambda token: priority.index(token)
            )
            dfa_accepts[current_id] = chosen

        for symbol in sorted(nfa.alphabet):
            next_states = set()

            for state in current:
                if state in nfa.transitions:
                    next_states.update(
                        nfa.transitions[state].get(symbol, set())
                    )

            next_subset = frozenset(
                eps_closure(nfa, next_states)
            )

            if next_subset not in dfa_states:
                dfa_states.add(next_subset)
                state_ids[next_subset] = len(state_ids)
                unprocessed.append(next_subset)

            dfa_transitions[current_id][symbol] = state_ids[next_subset]

    return DFA(
        states=set(state_ids.values()),
        alphabet=set(nfa.alphabet),
        transitions=dfa_transitions,
        start=0,
        accepts=dfa_accepts
    )
    # TODO(PART A3): implement
    raise NotImplementedError("determinize is not implemented yet")



def build_token_dfa(spec: "TokenSpec") -> DFA:
    """Compile every token class of the spec into one combined DFA.

    Steps: compile each class regex to an NFA (regex_compiler), union the
    NFAs with a new start state and epsilon edges, then determinize with
    per-class labels and spec-order priority.
    """

    token_classes = list(spec)

    priority = [token.name for token in token_classes]

    new_start = 0
    next_state = 1

    combined_states = {new_start}
    combined_alphabet = set()
    combined_transitions = {}
    label_of = {}

    for token in token_classes:
        nfa = compile_regex(token.regex)

        state_map = {}

        for state in sorted(nfa.states):
            state_map[state] = next_state
            combined_states.add(next_state)
            next_state += 1

        combined_transitions.setdefault(new_start, {})
        combined_transitions[new_start].setdefault(EPS, set())
        combined_transitions[new_start][EPS].add(
            state_map[nfa.start]
        )

        combined_alphabet.update(nfa.alphabet)

        for state, transitions in nfa.transitions.items():
            new_state = state_map[state]

            combined_transitions.setdefault(new_state, {})

            for symbol, destinations in transitions.items():
                combined_transitions[new_state].setdefault(
                    symbol, set()
                )

                for destination in destinations:
                    combined_transitions[new_state][symbol].add(
                        state_map[destination]
                    )

        for accept_state in nfa.accepts:
            label_of[state_map[accept_state]] = token.name

    combined_nfa = NFA(
        states=combined_states,
        alphabet=combined_alphabet,
        transitions=combined_transitions,
        start=new_start,
        accepts=set(label_of.keys())
    )

    return determinize(combined_nfa, label_of, priority)
    # TODO(PART A3): implement
    raise NotImplementedError("build_token_dfa is not implemented yet")


def scan(dfa: DFA, spec: "TokenSpec", text: str) -> list[Token]:
    """Tokenize `text` by repeated maximal munch from the DFA start state.

    At each position: walk the DFA as far as possible, remember the last
    accepting label seen and its length; emit that Token (longest match);
    if the class has skip=true, discard instead. On no match, raise
    ScanError with the failing position. Must handle end-of-input while
    inside a token (e.g. text ending in an identifier).
    """
    # TODO(PART A4): implement
    raise NotImplementedError("scan is not implemented yet")
