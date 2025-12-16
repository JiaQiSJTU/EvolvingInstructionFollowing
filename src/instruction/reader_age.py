# encoding = "utf-8"

import random
import re
from typing import Dict, List
import json

from .base import Instruction

AGE_DEFINITIONS: Dict[str, str] = {
    "child": "children aged under 14",
    "youth": "youth aged from 15 to 24",
    "adult": "adults aged from 25 to 64",
    "senior": "seniors aged 65 or older",
}

READER_EVAL_PROMPT = """You are an impartial judge. Evaluate how well the text aligns with the target reader age.

# Input
## Target Reader Age
{reader_age}

## Text
{generation}

# Scoring Requirements
Use an integer score from 1 to 10 with these definitions:
1-2: No alignment or opposite to the target reader age.
3-4: Weak alignment to the target reader age; sporadic cues, mostly inconsistent.
5-6: Partial alignment to the target reader age; noticeable but frequent departures.
7-8: Strong alignment to the target reader age; occasional minor slips.
9-10: Near-perfect alignment to the target reader age; consistent throughout.

# Output JSON Format
{{
  "rationale": "1 sentence",
  "score": integer 1-10
}}
"""


class ReaderAgeInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "reader_age"
        self.args: Dict[str, str] = {}
        self._description: str = ""
        self._allowed: List[str] = ["child", "youth", "adult", "senior"]

    def initialization(self, args=None):
        """Initialize reader age constraint.
        Args can include: {reader_age: child|youth|adult|senior}
        """
        if isinstance(args, dict) and args.get("reader_age") is not None:
            age = str(args.get("reader_age")).lower()
            if age in self._allowed:
                self.args = {"reader_age": age}
            else:
                self.args = {}
        else:
            age = random.choice(self._allowed)
            self.args = {"reader_age": age}
        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("reader_age") is not None:
            age = self.args.get("reader_age")
            self._description = f"The response should be tailored for '{age}' readers."
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

    def check_following(self, generation, llm_backend, api_key, base_url, model_name="gpt-4.1"):
        """With reward model (stub)"""

        messages = [
            {"role": "user", "content": READER_EVAL_PROMPT.format(
                generation=generation, reader_age=AGE_DEFINITIONS[self.args.get("reader_age")])}
        ]
        response, prompt_tokens, completion_tokens = llm_backend(
            api_key, messages, model_name, base_url)
        response = json.loads(response)

        assert response.get("score") is not None

        return int(response["score"]), response.get("rationale", "")

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        """Require the target reader age keyword to appear in the synthesized query."""
        age = None
        if isinstance(cur_args, dict):
            age = cur_args.get("reader_age")
        if not isinstance(age, str) or age.strip() == "":
            return True
        text = query.casefold()

        synonyms = {
            "child": {
                "child", "kid",
            },
            "youth": {
                "youth", "teen",
                "adolescent", "young"
            },
            "adult": {
                "adult", "grown-up",
                "mature"
            },
            "senior": {
                "senior", "elder", "older",
                "retire"
            },
        }

        return age in text or any(synonym in text for synonym in synonyms.get(age, set()))
