# encoding = "utf-8"

from typing import List, Tuple, Dict
import string
import re
import nltk
import functools
import json


# Predefined pools
LETTERS: List[str] = list(string.ascii_letters)

EMOJIS: List[str] = [
    # faces - positive
    "😀", "😁", "😂", "🤣", "😃", "😄", "😅", "😆", "😉", "😊", "🙂", "🙃",
    "😍", "🥰", "😘", "😗", "😙", "😚", "🤗", "🤩",
    # faces - neutral / thinking
    "🤔", "🤨", "😐", "😑", "😶", "😏", "🙄",
    # faces - negative / tired / sick
    "😣", "😖", "😫", "😩", "😮", "😯", "😪", "😴", "😓", "😥", "😢", "😭",
    "😰", "😱", "😳", "😵", "🤒", "🤕", "🤢", "🤮", "🤧", "😷",
    # fun / party
    "😎", "🤓", "🤠", "🥳",
]


@functools.lru_cache(maxsize=None)
def _get_sentence_tokenizer():
    return nltk.data.load("nltk:tokenizers/punkt/english.pickle")


def count_sentences(text: str) -> int:
    """Count the number of sentences in text using NLTK Punkt tokenizer."""
    tokenizer = _get_sentence_tokenizer()
    tokenized_sentences = tokenizer.tokenize(text)
    return len(tokenized_sentences)


def normalize_list_of_strings(value) -> List[str]:
    """Normalize a list of strings by removing non-strings and empty/whitespace-only entries.
    Returns an empty list if input is not a list.
    """
    if isinstance(value, list):
        return [s.lower() for s in value if isinstance(s, str) and s.strip() != ""]
    return []


# Each data item processed by IFEval is treated as a topic with corresponding keywords
def load_topic_keywords(file_path="./data/input_data_modified_keywords_v2.jsonl"):

    keywords_dict = {}
    query_dict = {}
    with open(file_path, "r") as f:
        for line in f:
            data = json.loads(line.strip())
            topic = data["key"]
            keywords = data["keywords"]
            keywords_dict[topic] = normalize_list_of_strings(keywords)
            query_dict[topic] = data["prompt"]
    return keywords_dict, query_dict


TOPIC_KEYWORDS_DICT, TOPIC_QUERY_DICT = load_topic_keywords()
TOPIC_LIST = list(TOPIC_KEYWORDS_DICT.keys())
# print(TOPIC_KEYWORDS_DICT)
# print(TOPIC_QUERY_DICT)
# print(TOPIC_LIST)
# exit(0)


def get_topic_list() -> List[str]:
    return TOPIC_LIST.copy()


def get_keywords(topic: str = None) -> List[str]:
    """Return the list of keywords for the specified topic; if topic is empty, return the deduplicated union of all topics' keywords."""
    try:
        assert topic in TOPIC_KEYWORDS_DICT
        return TOPIC_KEYWORDS_DICT[topic].copy()
    except Exception as e:
        print("Warning: Topic does not exist.")
        print(topic)
        exit(0)


# Supported quotation/bracket pairs (left, right)
QUOTATION_PAIRS: List[Tuple[str, str]] = [
    ("(", ")"), ("[", "]"), ("{", "}"),  # (), [], {}
    ("<", ">"),  # angle brackets
    ("\u300a", "\u300b"),  # 《 》 double angle brackets
    ("\u3008", "\u3009"),  # 〈 〉 single angle brackets
    ("\u300c", "\u300d"),  # 「 」 corner brackets
    ("\u300e", "\u300f"),  # 『 』 white corner brackets
    ("\uff08", "\uff09"),  # （ ） fullwidth parentheses
    ("\u00ab", "\u00bb"),  # « » guillemets
    ("\u3010", "\u3011"),  # 【 】 lenticular brackets
    ("\u201c", "\u201d"),  # “ ” double curly quotes
    ("\u2018", "\u2019"),  # ‘ ’ single curly quotes
    ("'", "'"), ('"', '"'),  # ASCII quotes
]

# Punctuation candidates (EN + CN), excluding any chars used in QUOTATION_PAIRS
_RAW_PUNCTUATIONS: List[str] = list(string.punctuation) + [
    "。", "，", "、", "？", "！", "：", "；", "（", "）", "【", "】",
    "「", "」", "『", "』", "《", "》", "〈", "〉", "——", "……",
    "·", "～", "—", "￥", "?", "!", ";", "(", ")", "~"
]
_QUOTE_CHARS = {c for pair in QUOTATION_PAIRS for c in pair}
PUNCTUATIONS: List[str] = [
    p for p in _RAW_PUNCTUATIONS if p not in _QUOTE_CHARS]

# Common vs Uncommon punctuation buckets
COMMON_PUNCTUATIONS: List[str] = [
    ".", ",", ':'
]

# Uncommon is defined as the remainder of PUNCTUATIONS not in COMMON_PUNCTUATIONS
UNCOMMON_PUNCTUATIONS: List[str] = [
    p for p in PUNCTUATIONS if p not in COMMON_PUNCTUATIONS]


def get_letters() -> List[str]:
    """Return a copy of the candidate letter list (ASCII letters)."""
    return LETTERS.copy()


def get_emojis() -> List[str]:
    """Return a copy of the candidate emoji list."""
    return EMOJIS.copy()


def get_quotation_pairs() -> List[Tuple[str, str]]:
    """Return supported quotation/bracket pairs as (left, right)."""
    return QUOTATION_PAIRS.copy()


def get_punctuations() -> List[str]:
    """Return a copy of the punctuation candidates list (EN + CN)."""
    # Preserve order while deduplicating for determinism
    return list(dict.fromkeys(PUNCTUATIONS))


def get_all_punctuations() -> List[str]:
    """Return a copy of the raw punctuation list including brackets/quotes."""
    # Preserve order while deduplicating for determinism
    return list(dict.fromkeys(_RAW_PUNCTUATIONS))


def get_common_punctuations() -> List[str]:
    """Return commonly used punctuation candidates."""
    # keep only those that truly exist in the global list
    base = set(PUNCTUATIONS)
    return [p for p in COMMON_PUNCTUATIONS if p in base]


def get_uncommon_punctuations() -> List[str]:
    """Return less commonly used punctuation candidates."""
    base = set(PUNCTUATIONS)
    return [p for p in UNCOMMON_PUNCTUATIONS if p in base]


# -------------------- Text normalization helpers --------------------
def strip_structured_wrappers(text: str) -> str:
    """Remove common structural wrappers (markdown fences, html/xml tags, tables, simple json/csv shells) from the start of text.

    The goal is to expose the human-readable leading content for prefix checks.
    This is a conservative best-effort cleaning, not a full parser.
    """
    if not isinstance(text, str):
        return text

    s = text.lstrip("\ufeff\n\r\t ")

    # 1) Remove YAML front matter or markdown fences
    # --- front matter ---
    fm = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
    s = fm.sub("", s, count=1)
    # ```lang\n ... \n```
    fence = re.compile(r"^```[\w.+-]*\s*\n(.*?)\n```\s*", re.DOTALL)
    m = fence.match(s)
    if m:
        s = m.group(1).lstrip()

    # 2) Remove leading markdown table/header/blockquote markers
    # Skip sequences of lines that are typical table formatting
    lines = s.splitlines()
    i = 0

    def _is_wrapper_line(raw: str) -> bool:
        line = raw.lstrip()
        # Markdown table rule rows or pure punctuation rows
        if line.startswith("|"):
            return True
        if re.fullmatch(r"[:\-\s\|]+", line):
            return True
        # For headers/blockquote/bullets: only treat as wrapper if NO alnum content

        def no_alnum(text: str) -> bool:
            return re.search(r"[A-Za-z0-9]", text) is None
        for p in (">", "> ", "#", "##", "###", "####"):
            if line.startswith(p):
                return no_alnum(line[len(p):].strip())
        for p in ("- ", "* ", "+ "):
            if line.startswith(p):
                return no_alnum(line[len(p):].strip())
        return False

    while i < len(lines) and _is_wrapper_line(lines[i]):
        i += 1
    if i > 0 and i < len(lines):
        s = "\n".join(lines[i:]).lstrip()

    # 3) Remove leading HTML/XML tags iteratively
    tag_lead = re.compile(r"^\s*<[^>]+>\s*")
    for _ in range(10):
        s2 = tag_lead.sub("", s, count=1)
        if s2 == s:
            break
        s = s2

    # 4) Simplistic JSON unwrap: find first quoted value after a colon
    if s.startswith("{") or s.startswith("["):
        m = re.search(r":\s*\"([^\"]+)\"", s)
        if m:
            s = m.group(1).lstrip()

   # 5）Final cleanup of residual HTML tags at the very start
    s = re.sub(r"^<[^>]+>\s*", "", s)
    s = re.sub(r'\s*(</[^>]+>\s*)+$', '', s)
    return s
