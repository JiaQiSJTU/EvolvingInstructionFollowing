# encoding = "utf-8"

import random
import re
from typing import Dict, List, Tuple

from .base import Instruction
from .instruction_utils import (
    get_keywords,
    normalize_list_of_strings,
)


class ExistenceInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "existence"
        self.args: Dict[str, object] = {}
        self._description: str = ""

    def initialization(self, topic_name, forbidden_keywords=None, args=None):
        """Initialize existence constraint.
        Args:
        - forbidden_keywords: List[str] | None; a mask list used ONLY to exclude these from being selected as required keywords. Not stored.
        - args: Optional dict where keys are keywords and values are their minimum counts (default 1)
          Example: {"keyword1": 2, "keyword2": 1}
        Note: matching ignores case; keywords are matched by word boundary when possible, otherwise by substring.
        """
        forbidden_mask = set(normalize_list_of_strings(
            forbidden_keywords) if forbidden_keywords is not None else [])
        if isinstance(args, dict) and len(args) > 0:
            # filter out forbidden-masked keywords
            if len(forbidden_mask) > 0:
                args = {k: v for k, v in args.items() if k not in forbidden_mask}
            if len(args) > 0:
                self.args = args
            else:
                self.args = {}
        else:
            # Random initialization for required keywords only (excluding forbidden)
            candidates = list(get_keywords(topic_name))
            if len(forbidden_mask) > 0:
                candidates = [c for c in candidates if c not in forbidden_mask]
            random.shuffle(candidates)
            if len(candidates) == 0:
                self.args = {}
            else:
                num_required = random.randint(1, 3)
                chosen = candidates[:num_required]
                keywords = {kw: random.randint(1, 10) for kw in chosen}
                self.args = keywords

        return self

    def build_description(self):
        if isinstance(self.args, dict) and len(self.args) > 0:
            keywords: Dict[str, int] = self.args
            parts = []
            for k, n in keywords.items():
                if n == 1:
                    parts.append(f"'{k}' (exactly once)")
                else:
                    parts.append(f"'{k}' (exactly {n} times)")
            req = ", ".join(parts)
            self._description = f"The response must include the following keywords: {req}."

        return self._description

    def get_instruction_args(self):
        return dict(self.args)

    def modification(self, topic_name, forbidden_keywords=None):
        """Randomly modify required keywords by adding/removing/updating.
        - forbidden_keywords: Optional[List[str]]; mask to exclude from selection. Not stored.
        Random strategy with guarantee:
        - Prefer a random op among {add, remove, update}; retry up to 10 times to get an actual change.
        - Fallback deterministically to add -> remove -> update if all retries failed.
        """
        forbidden_mask = set(normalize_list_of_strings(
            forbidden_keywords) if forbidden_keywords is not None else [])
        original_keywords: Dict[str, int] = dict(
            self.args) if isinstance(self.args, dict) else {}
        original_description = self.build_description()

        total_keywords_count = len(get_keywords(
            topic_name)) - len(forbidden_mask)

        def add_op(base: Dict[str, int]) -> Dict[str, int]:
            current = dict(base)
            candidates_all = [k for k in get_keywords(
                topic_name) if k not in forbidden_mask]
            add_candidates = [k for k in candidates_all if k not in current]
            random.shuffle(add_candidates)
            if len(add_candidates) == 0:
                return current
            k_num = random.randint(1, 3)
            for k in add_candidates[:k_num]:
                current[k] = random.randint(1, 3)
            return current

        def remove_op(base: Dict[str, int]) -> Dict[str, int]:
            current = dict(base)
            if len(current) == 0:
                return current
            keys = list(current.keys())
            random.shuffle(keys)
            k_num = random.randint(1, max(1, len(keys) // 2))
            for k in keys[:k_num]:
                current.pop(k, None)
            return current

        def update_op(base: Dict[str, int]) -> Dict[str, int]:
            current = dict(base)
            if len(current) == 0:
                return current
            keys = list(current.keys())
            random.shuffle(keys)
            k_num = random.randint(1, len(keys))
            changed = False
            for k in keys[:k_num]:
                old = current[k]
                choices = [1, 2, 3]
                if old in choices and len(choices) > 1:
                    choices = [c for c in choices if c != old]
                new_val = random.choice(choices)
                if new_val != old:
                    changed = True
                current[k] = new_val
            # If nothing changed due to edge cases, force-change one key
            if not changed:
                k = random.choice(keys)
                current[k] = 1 if current[k] != 1 else 2
            return current

        def mutate_once(base: Dict[str, int]) -> Dict[str, int]:
            if len(base) == 0:
                op = "add"
            elif len(base) == 1:  # <fix>
                op = random.choice(["add", "update"])
            elif len(base) == total_keywords_count:  # <fix>
                op = random.choice(["remove", "update"])
            else:
                op = random.choice(["add", "remove", "update"])
            if op == "add":
                return add_op(base)
            if op == "remove":
                return remove_op(base)
            return update_op(base)

        # Try up to 10 random attempts to get a change
        new_keywords = dict(original_keywords)
        for _ in range(10):
            candidate = mutate_once(original_keywords)
            # Enforce mask post-mutation (defensive)
            if len(forbidden_mask) > 0:
                candidate = {k: v for k, v in candidate.items()
                             if k not in forbidden_mask}
            if candidate != original_keywords:
                new_keywords = candidate
                break

        if len(new_keywords) > 0:
            self.args = new_keywords
        else:
            self.args = {}
        self._description = self.build_description()

        return original_description, self._description

    def check_following(self, generation):
        if not isinstance(generation, str):
            return False
        if not isinstance(self.args, dict):
            return True
        keywords: Dict[str, int] = self.args or {}
        if not keywords:
            return True
        text = generation
        # Ensure required counts (ignore case)
        for kw, min_count in keywords.items():
            if not isinstance(min_count, int) or min_count < 1:
                continue
            count = self._count(text, kw)
            if count != min_count:
                return False
        return True

    # -------------------- helpers --------------------
    def _count(self, text: str, keyword: str) -> int:
        if not isinstance(text, str) or not isinstance(keyword, str) or keyword == "":
            return 0
        flags = re.IGNORECASE
        # Use word boundary when keyword is purely word-chars; otherwise fallback to substring
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
        """Compare prev_args and cur_args to find changed keywords (added or count changed),
        then check these keywords appear in query (case-insensitive).
        If there is no effective change, return True.
        """
        # Defensive defaults
        if not isinstance(query, str):
            return False
        if not isinstance(prev_args, dict):
            prev_args = {}
        if not isinstance(cur_args, dict):
            cur_args = {}
        # Identify changed keywords: added or value changed
        changed_keywords: List[str] = []
        for k, v in cur_args.items():
            if (k not in prev_args) or (prev_args.get(k) != v):
                changed_keywords.append(k)

        # If no changes, consider complete
        if len(changed_keywords) == 0:
            return True

        q = query.casefold()
        # Require all changed keywords to be mentioned (case-insensitive substring)
        for kw in changed_keywords:
            if kw.casefold() not in q:
                return False
        return True
