# encoding = "utf-8"

import random
import re
from typing import List

from .base import Instruction
from .instruction_utils import (
    get_keywords,
    normalize_list_of_strings,
)


class ForbiddenInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "forbidden"
        self.args: List[str] = []
        self._description: str = ""

    def initialization(self, topic_name, forbidden_keywords=None, args=None):
        """Initialize forbidden constraint.
        Args:
        - forbidden_keywords: List[str] | None; a mask list used ONLY to exclude these from being selected as forbidden words. Not stored.
        - args: Optional list of forbidden keywords that must NOT appear in the generation
          Example: ["keyword1", "keyword2"]
        Note: matching ignores case; word-boundary when possible, else substring.
        """
        mask = set(normalize_list_of_strings(forbidden_keywords)
                   if forbidden_keywords is not None else [])
        if isinstance(args, dict) and (args.get("keywords") is not None):
            # Support old format {"keywords": [...]}
            kw_list = normalize_list_of_strings(args.get("keywords"))
            if len(mask) > 0:
                kw_list = [k for k in kw_list if k not in mask]
            if len(kw_list) > 0:
                self.args = kw_list
            else:
                self.args = []
        elif isinstance(args, list):
            # New format: directly pass list
            kw_list = normalize_list_of_strings(args)
            if len(mask) > 0:
                kw_list = [k for k in kw_list if k not in mask]
            if len(kw_list) > 0:
                self.args = kw_list
            else:
                self.args = []
        else:
            # Random initialization: choose 1-3 keywords as forbidden, excluding mask
            candidates = [k for k in get_keywords(topic_name) if k not in mask]
            random.shuffle(candidates)
            if len(candidates) == 0:
                self.args = []
            else:
                n = random.randint(1, 3)
                self.args = candidates[:n]
        self._description = self.build_description()
        return self

    def build_description(self):
        if isinstance(self.args, list) and len(self.args) > 0:
            kws: List[str] = self.args
            items = ", ".join([f"'{k}'" for k in kws])
            self._description = f"The response must not contain the following keywords: {items}."
        return self._description

    def get_instruction_args(self):
        return list(self.args) if isinstance(self.args, list) else []

    def modification(self, topic_name, forbidden_keywords=None):
        """Randomly modify forbidden keyword list by adding/removing.
        - forbidden_keywords: Optional[List[str]]; mask to exclude from selection. Not stored.
        Random strategy with guarantee:
        - If the list is empty, perform add.
        - Else randomly choose add or remove; retry up to 10 times to get an actual change.
        """
        mask = set(normalize_list_of_strings(forbidden_keywords)
                   if forbidden_keywords is not None else [])
        original: List[str] = list(self.args) if isinstance(
            self.args, list) else []
        original_description = self.build_description()

        total_keywords_count = len(get_keywords(topic_name)) - len(mask)

        def add_op(base: List[str]) -> List[str]:
            current = list(base)
            candidates = [k for k in get_keywords(
                topic_name) if k not in mask and k not in current]
            random.shuffle(candidates)
            if len(candidates) == 0:
                return current
            k_num = random.randint(1, 3)
            current.extend(candidates[:k_num])
            return current

        def remove_op(base: List[str]) -> List[str]:
            current = list(base)
            if len(current) == 0:
                return current
            random.shuffle(current)
            k_num = random.randint(1, max(1, len(current) // 2))
            return current[k_num:]

        def mutate_once(base: List[str]) -> List[str]:
            if len(base) == 0 or len(base) == 1:  # <fix>
                return add_op(base)
            elif len(base) == total_keywords_count:
                return remove_op(base)
            op = random.choice(["add", "remove"])
            return add_op(base) if op == "add" else remove_op(base)

        new_list = list(original)
        for _ in range(10):
            candidate = mutate_once(original)
            # enforce mask
            candidate = [k for k in candidate if k not in mask]
            if candidate != original:
                new_list = candidate
                break

        if len(new_list) > 0:
            self.args = new_list
        else:
            self.args = []
        self._description = self.build_description()

        return original_description, self._description

    def check_following(self, generation):
        if not isinstance(generation, str):
            return False
        if not isinstance(self.args, list):
            return True
        kws: List[str] = self.args or []
        if not kws:
            return True
        text = generation
        # If any forbidden keyword appears (case-insensitive; word-boundary when possible)
        for kw in kws:
            if self._contains(text, kw):
                return False
        return True

    # -------------------- helpers --------------------
    def _contains(self, text: str, keyword: str) -> bool:
        return self._count(text, keyword) > 0

    def _count(self, text: str, keyword: str) -> int:
        if not isinstance(text, str) or not isinstance(keyword, str) or keyword == "":
            return 0
        flags = re.IGNORECASE
        use_word_mode = re.match(r"^\w+$", keyword, flags=0) is not None
        if use_word_mode:
            pattern = r"\b" + re.escape(keyword) + r"\b"
        else:
            pattern = re.escape(keyword)
        try:
            return len(re.findall(pattern, text, flags=flags))
        except re.error:
            haystack = text.lower()
            needle = keyword.lower()
            return haystack.count(needle)

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        """
        Compare keyword differences between prev_args and cur_args (treat additions as differences),
        and determine whether each differing keyword appears in the query (case-insensitive).
        Return True if there are no newly added keywords.
        """
        if not isinstance(query, str):
            return False

        added_keywords = []
        if prev_args is None:
            add_keywords = cur_args
        else:
            prev_set = {s.casefold() for s in prev_args}
            # Added keywords: present in cur but not in prev (case-insensitive)
            for k in cur_args:
                if k.casefold() not in prev_set:
                    added_keywords.append(k)

        # If there are no additions, consider it complete
        if len(added_keywords) == 0:
            return True
        q = query.casefold()
        for kw in added_keywords:
            if kw.casefold() not in q:
                return False
        return True


if __name__ == "__main__":
    query = "Could we add one more thing to the guidelines? Just make sure the text doesn't actually mention 'tripoli' or a 'principality of galilee'. I think that will help keep it on track."
    prev_args = None
    cur_args = ["tripoli", "principality of galilee"]
    print(ForbiddenInstruction.check_query_completeness(
        query, prev_args, cur_args))
