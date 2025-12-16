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


class StartWithInstruction(Instruction):

    def __init__(self):
        super().__init__()
        self.id = "startwith"
        self.args: Dict[str, str] = {}
        self._description: str = ""

    def initialization(self, topic_name, forbidden_keywords=None, args=None):
        """Initialize with optional args or randomly choose a start-with rule.
        Args can include: {mode: letter|emoji|keyword|quotation, value: str, left: str, right: str}
        - topic_name: determines the keyword candidates
        - forbidden_keywords: avoid conflication with the ForbiddenInstruction
        - args: optional designated args for the instruction
        """

        # Input args; validate them. If validation fails, set self.args to empty; if valid, assign to self.args
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

        # No args provided: initialize
        else:
            mode = random.choice(
                ["letter", "emoji", "keyword", "quotation"])  # start-with type
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
                # For quotation, we do not constrain the inner content; only the starting bracket matters for checking
                self.args = {"mode": mode, "left": left, "right": right}

        return self

    def build_description(self):
        """Build a one-sentence English instruction description from args."""

        if isinstance(self.args, dict) and self.args.get("mode") is not None:

            mode = self.args.get("mode")

            if mode == "letter":
                value = self.args.get("value")
                self._description = f"Start the response with the letter '{value}'."
            if mode == "emoji":
                value = self.args.get("value")
                self._description = f"Start the response with the emoji '{value}'."
            if mode == "keyword":
                value = self.args.get("value")
                self._description = f"Start the response with the keyword '{value}'."
            if mode == "quotation":
                left, right = self.args.get("left"), self.args.get("right")
                self._description = f"Start the response with a quotation starting with '{left}' and ending with '{right}'."

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
        """Check whether the generation satisfies the start-with rule.
        Leading whitespace (and BOM) is ignored.
        """
        if not isinstance(generation, str):
            return False
        text = generation.lstrip("\ufeff\n\r\t ")

        mode = self.args.get("mode") if isinstance(self.args, dict) else None

        if mode == "quotation":
            # quotation: only check the starting left symbol, and ensure some right symbol exists later (optional but safer)
            left = self.args.get("left")
            right = self.args.get("right")
            if not left or not right:
                return False
            if not text.startswith(left):
                return False

            # Right symbol can appear anywhere after the first position
            return right in text[len(left):]

        # strip structured wrappers like json/xml/csv/table/html/markdown (conservative)
        try:
            from instruction_utils import strip_structured_wrappers
            text = strip_structured_wrappers(text)
            # print(text)
        except Exception:
            pass
        # print(text)

        # Remove leading unicode invisible/whitespace characters beyond basic lstrip
        try:
            import re
            text = re.sub(
                r'^[\s\ufeff\u00A0\u1680\u180E\u2000-\u200F\u2028\u2029\u202F\u205F\u2060\u3000\uFEFF]+', '', text)
        except Exception:
            pass

        # Remove leading punctuation before checking
        try:
            all_head = "".join(get_all_punctuations())
            text = text.lstrip(all_head)
        except Exception:
            pass

        if mode != "quotation":
            expected = self.args.get("value")
            if expected == "":
                return True

            # For letter mode: find the first alphabetic character and compare ignoring case
            if mode == "letter":
                import re
                m = re.search(r"[A-Za-z]", text)
                # print(text)
                # print(m)
                if not m:
                    return False
                return m.group(0).casefold() == str(expected).casefold()
            # Other modes: case-insensitive prefix check

            try:
                return text.casefold().startswith(str(expected).casefold())
            except Exception:
                return text.startswith(str(expected))

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
