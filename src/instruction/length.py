# encoding = "utf-8"

import random
import re
from typing import Dict

from .base import Instruction
from .instruction_utils import count_sentences


class LengthInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "length"
        self.args: Dict[str, object] = {}
        self._description: str = ""

    def initialization(self, args=None):
        """Initialize length constraint.
        Args can include: {mode: word|paragraph|characters|sentence, relation: less_than|more_than, number: int>=0}
        """
        # Use ordered lists to avoid set-order nondeterminism
        allowed_modes = ["word", "paragraph", "characters", "sentence"]
        allowed_relations = ["less_than", "more_than", "exactly"]
        if isinstance(args, dict) and args.get("mode") is not None:
            mode = args.get("mode")
            relation = args.get("relation")
            number = args.get("number")
            if (mode in allowed_modes and relation in allowed_relations and
                    isinstance(number, int) and number >= 0):
                self.args = {"mode": mode,
                             "relation": relation, "number": number}
            else:
                self.args = {}
        else:
            mode = random.choice(allowed_modes)
            relation = random.choice(allowed_relations)
            # choose a reasonable random threshold
            default_ranges = {
                "word": [x for x in range(100, 2000, 100)],
                "paragraph": [x for x in range(2, 7, 1)],
                "characters": [x for x in range(100, 2500, 100)],
                "sentence": [x for x in range(5, 50, 5)],
            }
            candidate_list = default_ranges.get(mode)
            number = random.choice(candidate_list)
            self.args = {"mode": mode, "relation": relation, "number": number}

        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("mode") is not None:
            mode = self.args.get("mode")
            relation = self.args.get("relation")
            number = self.args.get("number")
            target = {
                "word": "words",
                "paragraph": "paragraphs",
                "characters": "characters",
                "sentence": "sentences",
            }.get(mode, "items")

            if relation == "less_than":
                relation_text = "less than"
            elif relation == "more_than":
                relation_text = "more than"
            elif relation == "exactly":
                relation_text = "exactly"
            self._description = f"The response must contain {relation_text} {number} {target}."

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
        if not isinstance(self.args, dict):
            return True
        mode = self.args.get("mode")
        relation = self.args.get("relation")
        number = self.args.get("number")
        if mode is None or relation is None or not isinstance(number, int):
            return True
        text = generation
        if mode == "word":
            count = len(re.findall(r"\w+", text, flags=re.UNICODE))
        elif mode == "paragraph":
            # split by blank lines into paragraphs, counting non-empty blocks
            stripped = text.strip()
            if stripped == "":
                count = 0
            else:
                parts = re.split(r"(?:\r?\n\s*){2,}", stripped)
                parts = [p for p in (s.strip() for s in parts) if p != ""]
                count = len(parts)
        elif mode == "sentence":
            stripped = text.strip()
            if stripped == "":
                count = 0
            else:
                try:
                    count = count_sentences(stripped)
                except Exception:
                    # Fallback to 1 if non-empty
                    count = 1
        else:  # characters
            count = len(text)

        if relation == "less_than":
            return count < number
        elif relation == "more_than":
            return count > number
        elif relation == "exactly":
            return count == number
        return True

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        mode = cur_args.get("mode") if isinstance(cur_args, dict) else None
        relation = cur_args.get("relation") if isinstance(
            cur_args, dict) else None
        number = cur_args.get("number") if isinstance(cur_args, dict) else None
        if not isinstance(query, str) or not query.strip():
            return False
        q = query.casefold()
        # Any one token match is sufficient: mode OR number OR relation
        # 1) mode token
        if isinstance(mode, str) and mode:
            if mode.casefold() in q:
                return True

        # 2) number token
        if isinstance(number, int):
            if str(number) in q:
                return True

        # 3) relation token (support underscore and spaced phrase)
        if isinstance(relation, str) and relation:
            relation = relation.split("_")[0].casefold()
            if relation in q:
                return True

        return False
