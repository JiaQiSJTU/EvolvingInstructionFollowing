# encoding = "utf-8"

import random
import re
from typing import Dict

from .base import Instruction


class CountableItemsInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "countableItems"
        self.args: Dict[str, int] = {}
        self._description: str = ""

    def initialization(self, args=None):
        """Initialize with the exact number of bullet points required.
        Args can include: {num: int}
        """
        if isinstance(args, dict) and args.get("num") is not None:
            n = args.get("num")
            if isinstance(n, int) and n >= 0:
                self.args = {"num": n}
            else:
                self.args = {}
        else:
            n = random.randint(3, 15)
            self.args = {"num": n}

        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("num") is not None:
            n = self.args.get("num")
            self._description = f"The answer must contain exactly {n} bullet points, which should be separated by bullet points such as: * point or - point."

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
        num_required = self.args.get("num") if isinstance(
            self.args, dict) else None
        if num_required is None:
            return True
        # Count markdown bullet lists beginning with '*' or '-'
        bullets_star = re.findall(
            r"^\s*\*[^\*].*$", generation, flags=re.MULTILINE)
        bullets_dash = re.findall(r"^\s*-.*$", generation, flags=re.MULTILINE)
        num_actual = len(bullets_star) + len(bullets_dash)
        return num_actual == num_required

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        if not isinstance(query, str) or not query.strip():
            return False
        q = query.lower()
        bullets_syn = r"(\*|-)"
        return re.search(bullets_syn, q, flags=re.IGNORECASE) is not None
