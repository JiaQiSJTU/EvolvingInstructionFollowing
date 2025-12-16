# encoding = "utf-8"

import random
import re
from typing import Dict, List
import json

from .base import Instruction

STYLE_DEFINITIONS: Dict[str, str] = {
    "formal": "A formal style, which is usually characterized by detachment, precision, objectivity, rigidity, and higher cognitive load.",
    "informal": "An informal style, which is more subjective, less accurate, less informative, and with much lighter cognitive load.",
    "active voice": "Active voice when the subject performs the action",
    "passive voice": "Passive voice is when the subject receives the action. ",
}

STYLE_EVAL_PROMPT = """You are an impartial judge. Evaluate how well the text matches the target writing style.


# Input
## Target Style
{style}

## Text
{generation}

# Scoring Requirements
Use an integer score from 1 to 10 with these definitions:
1-2: Completely mismatched or mostly opposite to the target style.
3-4: Weak alignment; occasional features, mostly inconsistent.
5-6: Partial alignment; noticeable but frequent departures.
7-8: Strong alignment; only occasional minor slips.
9-10: Near-perfect alignment; pervasive and consistent with no contradictions.

# Output JSON Format
{{
  "rationale": "1 sentence",
  "score": integer 1-10
}}
"""


class StyleInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "style"
        self.args: Dict[str, str] = {}
        self._description: str = ""
        self._allowed: List[str] = [
            "formal",
            "informal",
            "active voice",
            "passive voice",
        ]

    def initialization(self, args=None):
        """Initialize style constraint.
        Args can include: {style: formal|informal|active voice|passive voice}
        """
        if isinstance(args, dict) and args.get("style") is not None:
            style = str(args.get("style")).lower()
            if style in self._allowed:
                self.args = {"style": style}
            else:
                self.args = {}
        else:
            style = random.choice(self._allowed)
            self.args = {"style": style}
        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("style") is not None:
            style = self.args.get("style")
            # More natural phrasing for different style categories
            if style == "formal":
                self._description = "The response should adopt a 'formal' writing style throughout."
            elif style == "informal":
                self._description = "The response should adopt an 'informal' writing style throughout."
            elif style == "active voice":
                self._description = "The response should be written in the 'active voice' throughout."
            elif style == "passive voice":
                self._description = "The response should be written in the 'passive voice' throughout."
            else:
                raise ValueError(f"Unknown style: {style}")
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
        """With GPT-4.1"""

        messages = [
            {"role": "user", "content": STYLE_EVAL_PROMPT.format(
                generation=generation, style=STYLE_DEFINITIONS[self.args.get("style")])}
        ]
        response, prompt_tokens, completion_tokens = llm_backend(
            api_key, messages, model_name)
        response = json.loads(response)

        assert response.get("score") is not None

        return int(response["score"]), response.get("rationale", "")

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        """Require the target style keyword (or synonyms) to appear in the synthesized query."""
        style = None
        if isinstance(cur_args, dict):
            style = cur_args.get("style")
        if not isinstance(style, str) or style.strip() == "":
            return True
        text = query.casefold()

        return style.casefold().split(" ")[0] in text
