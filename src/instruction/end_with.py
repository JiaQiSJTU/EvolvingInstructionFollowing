# encoding = "utf-8"

import random
from typing import Dict, List, Tuple

from .base import Instruction
from .instruction_utils import (
    get_letters,
    get_emojis,
    get_keywords,
    get_quotation_pairs,
    get_all_punctuations,
)


class EndWithInstruction(Instruction):

    def __init__(self):
        super().__init__()
        self.id = "endwith"
        self.args: Dict[str, str] = {}
        self._description: str = ""

    def initialization(self, topic_name, forbidden_keywords=None, args=None):
        """Initialize with optional args or randomly choose an end-with rule.
        Args can include: {mode: letter|emoji|keyword|quotation, value: str, left, right}
        """

        # Input args; validate their validity
        if isinstance(args, dict) and args.get("mode") is not None:
            mode = args.get("mode")
            allowed_modes = {"letter", "emoji", "keyword", "quotation"}
            if mode not in allowed_modes:
                self.args = {}
                return self

            if mode == "quotation":
                left = args.get("left")
                right = args.get("right")
                pairs = set(get_quotation_pairs())
                if isinstance(left, str) and isinstance(right, str) and (left, right) in pairs:
                    self.args = {"mode": mode, "left": left, "right": right}
                else:
                    self.args = {}
            else:
                v = args.get("value")
                valid = False
                if mode == "letter":
                    valid = isinstance(v, str) and v in get_letters()
                elif mode == "emoji":
                    valid = isinstance(v, str) and v in get_emojis()
                elif mode == "keyword":
                    valid = isinstance(v, str) and v in get_keywords(
                        topic_name) and (v not in forbidden_keywords)
                if valid:
                    self.args = {"mode": mode, "value": v}
                else:
                    self.args = {}
        else:
            # No args provided: initialize by randomly choosing an end-with constraint
            mode = random.choice(
                ["letter", "emoji", "keyword", "quotation"])  # end-with type
            if mode == "letter":
                value = random.choice(get_letters())
                self.args = {"mode": mode, "value": value}
            elif mode == "emoji":
                value = random.choice(get_emojis())
                self.args = {"mode": mode, "value": value}
            elif mode == "keyword":
                candidates = [k for k in get_keywords(
                    topic_name) if k not in forbidden_keywords]
                if len(candidates) > 0:
                    value = random.choice(candidates)
                    self.args = {"mode": mode, "value": value}
                else:
                    self.args = {}
            else:  # quotation
                bracket_pairs: List[Tuple[str, str]] = get_quotation_pairs()
                left, right = random.choice(bracket_pairs)
                self.args = {"mode": mode, "left": left, "right": right}

        return self

    def build_description(self):
        """Build a one-sentence English instruction description from args."""
        if isinstance(self.args, dict) and self.args.get("mode") is not None:
            mode = self.args.get("mode")
            if mode == "letter":
                value = self.args.get("value")
                self._description = f"End the response with the letter '{value}'."
            if mode == "emoji":
                value = self.args.get("value")
                self._description = f"End the response with the emoji '{value}'."
            if mode == "keyword":
                value = self.args.get("value")
                self._description = f"End the response with the keyword '{value}'."
            if mode == "quotation":
                left, right = self.args.get("left"), self.args.get("right")
                self._description = f"End the response with a quotation starting with '{left}' and ending with '{right}'."

        return self._description

    def get_instruction_args(self):
        return dict(self.args)

    def modification(self, topic_name, forbidden_keywords=None):
        """modify the arguments of the instruction"""

        original = dict(self.args)
        original_description = self.build_description()

        for _ in range(10):
            self.initialization(topic_name, forbidden_keywords)
            if self.args != original:
                break
        self._description = self.build_description()

        return original_description, self._description

    def check_following(self, generation):
        """Check whether the generation satisfies the end-with rule.
        Trailing whitespace (and BOM) is ignored.
        """
        if not isinstance(generation, str):
            return False
        text = generation.rstrip("\ufeff\n\r\t ")

        mode = self.args.get("mode") if isinstance(self.args, dict) else None

        if mode == "quotation":
            # quotation: ensure it ends with the right symbol and the left appears somewhere before it
            left = self.args.get("left")
            right = self.args.get("right")
            if not left or not right:
                return False
            if not text.endswith(right):
                return False
            # ensure left exists before the final right
            end_index = len(text) - len(right)
            return left in text[:end_index]

        # strip structured wrappers like json/xml/csv/table/html/markdown (conservative)
        try:
            from instruction_utils import strip_structured_wrappers
            text = strip_structured_wrappers(text)
        except Exception:
            pass
        # print(text)
        if mode != "quotation":
            expected = self.args.get("value")
            if expected == "":
                return True
            # Normalize: strip trailing punctuation and compare case-insensitively
            all_tail = "".join(get_all_punctuations())
            text = text.rstrip(all_tail)
            # For letter mode: find the last alphabetic character and compare ignoring case
            if mode == "letter":
                import re
                matches = list(re.finditer(r"[A-Za-z]", text))
                if not matches:
                    return False
                last_char = matches[-1].group(0)
                return last_char.casefold() == str(expected).casefold()
            try:
                return text.casefold().endswith(str(expected).casefold())
            except Exception:
                return text.endswith(str(expected))

        return True

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):

        mode = cur_args.get("mode") if isinstance(cur_args, dict) else None
        if not isinstance(query, str) or not query.strip():
            return False
        q = query.casefold()
        if mode == "quotation":
            left = cur_args.get("left")
            return left.casefold() in q
        else:
            value = cur_args.get("value")
            return str(value).casefold() in q
