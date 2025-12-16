# encoding = "utf-8"

import random
import re
from typing import Dict, List
import json

from .base import Instruction

EMOTION_EVAL_PROMPT = """You are an impartial judge. Evaluate how well the text expresses the target emotion.

# Input
## Target Emotion
{emotion}

## Text
{generation}

# Scoring Requirements
Use an integer score from 1 to 10 with these definitions:
1-2: No alignment or opposite to the target emotion.
3-4: Weak alignment to the target emotion; sporadic cues, mostly inconsistent.
5-6: Partial alignment to the target emotion; noticeable but frequent departures.
7-8: Strong alignment to the target emotion; occasional minor slips.
9-10: Near-perfect alignment to the target emotion; consistent throughout.

# Output JSON Format
{{
  "rationale": "1 sentence",
  "score": integer 1-10
}}
"""


class EmotionInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "emotion"
        self.args: Dict[str, str] = {}
        self._description: str = ""
        self._allowed: List[str] = ["happy", "sad",
                                    "neutral", "angry", "excited", "frustrated"]

    def initialization(self, args=None):
        """Initialize emotion constraint.
        Args can include: {emotion: happy|sad|neutral|angry|excited|frustrated}
        """
        if isinstance(args, dict) and args.get("emotion") is not None:
            emo = str(args.get("emotion")).lower()
            if emo in self._allowed:
                self.args = {"emotion": emo}
            else:
                self.args = {}
        else:
            emo = random.choice(self._allowed)
            self.args = {"emotion": emo}
        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("emotion") is not None:
            emo = self.args.get("emotion")
            self._description = f"The response should adopt a '{emo}' emotional tone throughout."
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
        """With reward model
        """
        messages = [
            {"role": "user", "content": EMOTION_EVAL_PROMPT.format(
                generation=generation, emotion=self.args.get("emotion"))}
        ]
        response, prompt_tokens, completion_tokens = llm_backend(
            api_key, messages, model_name, base_url)
        response = json.loads(response)

        assert response.get("score") is not None

        return int(response["score"]), response.get("rationale", "")

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        """Require the target emotion keyword to appear in the synthesized query."""

        emo = None
        if isinstance(cur_args, dict):
            emo = cur_args.get("emotion")
        if not isinstance(emo, str) or emo.strip() == "":
            return True
        return emo.casefold() in query.casefold()
