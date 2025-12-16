# encoding = "utf-8"

import random
import re
from typing import Dict

from .base import Instruction


class ChangeCaseInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "case"
        self.args: Dict[str, object] = {}
        self._description: str = ""

    def initialization(self, args=None):
        """Initialize case constraint.
        Modes:
        - all_upper: all letters in response must be uppercase (ASCII)
        - all_lower: all letters in response must be lowercase (ASCII)
        - min_upper: at least N uppercase words (ASCII letters only), args: {min: int>=1%} 
        """
        # Use ordered list to avoid set-order nondeterminism
        allowed = ["all_upper", "all_lower", "min_upper"]
        if isinstance(args, dict) and args.get("mode") is not None:
            mode = args.get("mode")
            if mode not in allowed:
                self.args = {}
                return self
            if mode == "min_upper":
                n = args.get("min")
                if isinstance(n, int) and n >= 1:
                    self.args = {"mode": mode, "min": n}
                else:
                    self.args = {}
            else:
                self.args = {"mode": mode}
        else:
            mode = random.choice(allowed)
            if mode == "min_upper":
                n = random.randint(1, 100)
                self.args = {"mode": mode, "min": n}
            else:
                self.args = {"mode": mode}
        self._description = self.build_description()
        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("mode") is not None:
            mode = self.args.get("mode")
            if mode == "all_upper":
                self._description = "The response must use ALL UPPERCASE letters."
            if mode == "all_lower":
                self._description = "The response must use all lowercase letters."
            if mode == "min_upper":
                n = self.args.get("min")
                self._description = f"Approximately {n}% of the letters in the response should be uppercase."
        return self._description

    def get_instruction_args(self):
        return dict(self.args)

    def modification(self):
        original = dict(self.args)
        original_description = self.build_description()

        for _ in range(10):
            self.initialization()
            if self.args != original:
                break

        self._description = self.build_description()

        return original_description, self._description

    def check_following(self, generation):
        if not isinstance(generation, str):
            return False
        mode = self.args.get("mode") if isinstance(self.args, dict) else None
        if not mode:
            return True
        text = generation
        if mode == "all_upper":
            # Fail if any ASCII lowercase letter appears
            return re.search(r"[a-z]", text) is None
        if mode == "all_lower":
            # Fail if any ASCII uppercase letter appears
            return re.search(r"[A-Z]", text) is None
        if mode == "min_upper":
            n = self.args.get("min")
            if not isinstance(n, int) or n < 0:
                return True
            tol = 3  # tolerance ±3%
            # Compute percentage of uppercase letters among all ASCII letters
            letters = re.findall(r"[A-Za-z]", text)
            total_letters = len(letters)
            if total_letters == 0:
                return True
            uppercase_letters = sum(1 for ch in letters if ch.isupper())
            percent_upper = (uppercase_letters * 100) / total_letters
            return abs(percent_upper - n) <= tol
        return True

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):

        mode = cur_args.get("mode") if isinstance(cur_args, dict) else None
        if not mode:
            return True
        if not isinstance(query, str) or not query.strip():
            return False
        q = query.lower()

        uppercase_syn = r"(case|up|cap|all)"
        lowercase_syn = r"(case|low|all)"
        if mode == "all_upper":
            return re.search(uppercase_syn, q, flags=re.IGNORECASE) is not None
        if mode == "all_lower":
            return re.search(lowercase_syn, q, flags=re.IGNORECASE) is not None
        if mode == "min_upper":
            n = cur_args.get("min")
            if not isinstance(n, int) or n < 0:
                return False
            return str(n) in q
        return True
