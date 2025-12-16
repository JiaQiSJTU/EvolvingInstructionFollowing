# encoding = "utf-8"

import random
import json
import csv
import re
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Dict, List

from .base import Instruction


class FormatInstruction(Instruction):
    def __init__(self):
        super().__init__()
        self.id = "format"
        self.args: Dict[str, str] = {}
        self._description: str = ""

    def initialization(self, args=None):
        """Initialize format constraint.
        Modes: json | html | xml | csv | markdown
        """
        # Use ordered list to avoid set-order nondeterminism
        allowed = ["json", "html", "xml", "csv", "markdown"]
        if isinstance(args, dict) and args.get("mode") is not None:
            mode = args.get("mode")
            if isinstance(mode, str) and mode in allowed:
                self.args = {"mode": mode}
            else:
                self.args = {}
        else:
            mode = random.choice(allowed)
            self.args = {"mode": mode}

        return self

    def build_description(self):
        if isinstance(self.args, dict) and self.args.get("mode") is not None:
            mode = self.args.get("mode")
            if mode == "json":
                self._description = "The response must be valid JSON, parseable by a standard JSON parser."
            if mode == "html":
                self._description = "The response must be syntactically valid HTML with properly nested tags."
            if mode == "xml":
                self._description = "The response must be well-formed XML which is parseable and properly nested."
            if mode == "csv":
                self._description = "The response must be valid CSV that is consistent columns and properly quoted."
            if mode == "markdown":
                self._description = "The response must be valid Markdown without broken fences or obvious syntax errors)."
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
        mode = self.args.get("mode") if isinstance(self.args, dict) else None
        # Unwrap common code fences like ```json ... ``` or ```xml ... ```
        text = generation.strip()
        try:
            m = re.match(r"^```[\w.+-]*\s*\n(.*?)\n```\s*$", text, re.DOTALL)
            if m:
                text = m.group(1).strip()
        except Exception:
            pass
        # Use unwrapped text onward
        generation = text
        if not mode:
            return True
        text = generation.strip()
        try:
            if mode == "json":
                return self._is_valid_json(text)
            if mode == "xml":
                return self._is_valid_xml(text)
            if mode == "html":
                return self._is_valid_html(text)
            if mode == "csv":
                return self._is_valid_csv(text)
            if mode == "markdown":
                return self._is_valid_markdown(text)
        except Exception:
            return False
        return False

    # -------------------- validators --------------------
    def _is_valid_json(self, text: str) -> bool:
        try:
            json.loads(text)
            return True
        except Exception:
            return False

    def _is_valid_xml(self, text: str) -> bool:
        try:
            ET.fromstring(text)
            return True
        except Exception:
            return False

    def _is_valid_csv(self, text: str) -> bool:
        try:
            f = StringIO(text)
            reader = csv.reader(f)
            row_lengths: List[int] = []
            for idx, row in enumerate(reader):
                # allow empty last line
                if idx == 0 and len(row) == 0:
                    return False
                row_lengths.append(len(row))
            if len(row_lengths) == 0:
                return False
            # All rows should have the same number of columns (allow last empty row)
            base = row_lengths[0]
            for n in row_lengths[1:]:
                if n != base:
                    return False
            return True
        except Exception:
            return False

    def _is_valid_markdown(self, text: str) -> bool:
        # Best-effort checks: closed fenced code blocks, no obvious broken fences
        fence_count = text.count("```")
        if fence_count % 2 != 0:
            return False
        # If there are fenced regions, ensure each opens and closes
        if fence_count > 0:
            # simple scan
            opened = False
            for line in text.splitlines():
                if line.strip().startswith("```"):
                    opened = not opened
            if opened:
                return False

        return True

    def _is_valid_html(self, text: str) -> bool:
        # Minimal tag stack validation ignoring void elements
        # Accept if there are no tags (then not HTML); require at least one tag
        tag_regex = re.compile(r"<\/?([A-Za-z][A-Za-z0-9:-]*)\b[^>]*?>")
        tags = list(tag_regex.finditer(text))
        if not tags:
            return False
        void_tags = {
            "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
            "param", "source", "track", "wbr",
        }
        stack: List[str] = []
        for m in tags:
            tag = m.group(0)
            name = m.group(1).lower()
            is_closing = tag.startswith("</")
            self_closing = tag.endswith("/>") or name in void_tags
            if is_closing:
                # pop until we find matching name
                if not stack:
                    return False
                top = stack.pop()
                if top != name:
                    return False
            elif not self_closing:
                stack.append(name)
        return len(stack) == 0

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        mode = cur_args.get("mode") if isinstance(cur_args, dict) else None
        if not isinstance(query, str) or not query.strip():
            return False
        q = query.casefold()
        return str(mode).casefold() in q
