# encoding = "utf-8"

from .base import Instruction
from .start_with import StartWithInstruction
from .end_with import EndWithInstruction
from .format_instruction import FormatInstruction
from .countable_items import CountableItemsInstruction
from .length import LengthInstruction
from .existence import ExistenceInstruction
from .forbidden import ForbiddenInstruction
from .change_case import ChangeCaseInstruction
from .punctuation import PunctuationInstruction
# from .language import LanguageInstruction
from .emotion import EmotionInstruction
from .reader_age import ReaderAgeInstruction
from .style import StyleInstruction

__all__ = [
    "Instruction",
    "StartWithInstruction",
    "EndWithInstruction",
    "FormatInstruction",
    "CountableItemsInstruction",
    "LengthInstruction",
    "ExistenceInstruction",
    "ForbiddenInstruction",
    "ChangeCaseInstruction",
    "PunctuationInstruction",
    "EmotionInstruction",
    # "LanguageInstruction",
    "ReaderAgeInstruction",
    "StyleInstruction",
]
