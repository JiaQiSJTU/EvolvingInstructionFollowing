# encoding = "utf-8"

import random
from typing import Dict

from .base import Instruction
from .instruction_utils import (
    get_uncommon_punctuations,
    get_common_punctuations,
)


class PunctuationInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "punctuation"
        self.args: Dict[str, object] = {}
        self._description: str = ""

    def initialization(self, args=None):
        """Initialize punctuation constraint.
        Modes:
        - must_include: require the response to contain a specific punctuation (value: str)
        - must_not_include: require the response to not contain a specific punctuation (value: str)
        """
        allowed_modes = {"must_include", "must_not_include"}

        if isinstance(args, dict) and args.get("mode") is not None:
            mode = args.get("mode")
            if mode not in allowed_modes:
                self.args = {}
                return self

            if mode == "must_include":
                candidates = set(get_uncommon_punctuations())
            else:
                candidates = set(get_common_punctuations())

            v = args.get("value")
            if isinstance(v, str) and v in candidates:
                self.args = {"mode": mode, "value": v}
            else:
                self.args = {}

        else:
            # random initialization when args not provided
            mode = random.choice(["must_include", "must_not_include"])  # 约束类型
            puncts = (
                get_uncommon_punctuations() if mode == "must_include" else get_common_punctuations()
            )
            value = random.choice(puncts)
            self.args = {"mode": mode, "value": value}

        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("mode") is not None:
            mode = self.args.get("mode")
            v = self.args.get("value")

            if mode == "must_include":
                self._description = f"The response must contain the punctuation '{v}'."
            if mode == "must_not_include":
                self._description = f"The response must not contain the punctuation: '{v}'."
        return self._description

    def get_instruction_args(self):
        return dict(self.args)

    def modification(self):
        original = dict(self.args)
        original_description = self.build_description()

        for _ in range(10):
            # re-randomize; keep the same distribution behavior
            self.initialization()
            if self.args != original:
                break
        self._description = self.build_description()
        return original_description, self._description

    def check_following(self, generation):
        if not isinstance(generation, str):
            return False
        if not isinstance(self.args, dict) or self.args.get("mode") is None:
            return True
        text = generation
        mode = self.args.get("mode")
        if mode == "must_include":
            p = self.args.get("value")
            if not isinstance(p, str):
                return True
            return p in text
        if mode == "must_not_include":
            p = self.args.get("value")
            if not isinstance(p, str):
                return True
            return p not in text
        return True

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        # If punctuation is half-width (ASCII), return True.
        # Otherwise, check whether the punctuation symbol appears in the query.
        # Non-ASCII punctuation: require it to show up in the query
        if not isinstance(query, str):
            return False
        value = cur_args.get("value")

        try:
            is_half_width = ord(value) < 128
        except Exception:
            is_half_width = False
        if is_half_width:
            return True
        else:
            return value in query


if __name__ == "__main__":
    query = "Okay, quick twist—switch out 'no periods allowed' with something a little spicier: make sure every answer slides in the epic '……' punctuation instead. Let’s see you handle THIS……"
    prev_args = {"mode": "must_not_include", "value": "."}
    cur_args = {"mode": "must_include", "value": "……"}
    print(PunctuationInstruction.check_query_completeness(
        query, prev_args, cur_args))
