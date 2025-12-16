# encoding = "utf-8"

'''
Evaluate dialog model generations against instruction-following constraints.

Workflow:
1) Load dialog_*.jsonl and initialize the target model.
2) For each turn, generate a response for 'user_query_verified'.
3) Evaluate the response against the active instructions.
4) Save generated responses and evaluation results to eval_*.jsonl.
5) Early stopping: with patience = N, stop evaluating a dialog after N consecutive
   turns fail to satisfy the instructions.
'''

import argparse
import json
import os
from typing import Dict, Any, List, Tuple

from openai import OpenAI
from tqdm import tqdm

from data_utils.utils import LLM_backend
from data_utils.system_prompt import SYSTEM_PROMPT

# -------------------- Instruction helpers --------------------

from instruction import *

_ID_TO_CLASS = {
    "startwith": StartWithInstruction,
    "endwith": EndWithInstruction,
    # "language": LanguageInstruction,
    "format": FormatInstruction,
    "countableItems": CountableItemsInstruction,
    "length": LengthInstruction,
    "existence": ExistenceInstruction,
    "forbidden": ForbiddenInstruction,
    "case": ChangeCaseInstruction,
    "punctuation": PunctuationInstruction,
    "emotion": EmotionInstruction,
    "reader_age": ReaderAgeInstruction,
    "style": StyleInstruction,
}


def build_instruction_instance(inst_id: str, args: Any):
    cls = _ID_TO_CLASS.get(inst_id)
    if cls is None:
        return None
    inst = cls()
    # Directly assign args for evaluation; ignore descriptions entirely
    setattr(inst, "args", args)
    return inst


def check_all_instructions(instructions: List[Dict[str, Any]], generation: str, api_key: str, base_url: str) -> Tuple[bool, Dict[str, bool]]:
    details: Dict[str, bool] = {}
    sub_details: Dict[str, Tuple[float, str]] = {}
    all_ok = True
    for it in instructions or []:
        inst_id = it.get("id")
        inst_args = it.get("args")
        inst = build_instruction_instance(inst_id, inst_args)
        if inst is None:
            ok = False  # unknown instruction, skip
        else:
            if inst_id in ["emotion", "reader_age", "style"]:
                try:
                    ok, rationale = inst.check_following(
                        generation, LLM_backend, api_key, base_url)
                except Exception:
                    ok = 0
                    rationale = ""
            else:
                try:
                    ok = inst.check_following(generation)
                except Exception:
                    ok = False

        if inst_id not in ["emotion", "reader_age", "style"]:
            details[inst_id] = bool(ok)
            if bool(ok) == False:
                all_ok = False
        else:
            bool_ok = float(ok) > 6.0
            details[inst_id] = bool_ok
            sub_details[inst_id] = (float(ok), rationale)
            if not bool_ok:
                all_ok = False

    return all_ok, details, sub_details


def load_jsonl(path: str) -> List[Dict[str, Any]]:

    contents: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                contents.append(json.loads(line))
            except Exception:
                continue
    return contents


def write_jsonl(path: str, records: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def run(args):
    dialogs_dir = args.dialogs_dir
    out_dir = os.path.join(args.output_dir, args.model_name.split("/")[-1])
    os.makedirs(out_dir, exist_ok=True)

    for file_id in tqdm(range(args.start_id, args.end_id + 1)):

        dialog_path = os.path.join(dialogs_dir, f"dialog_{file_id}.jsonl")
        if not os.path.exists(dialog_path):
            continue

        turns = load_jsonl(dialog_path)
        # Track remaining patience across turns and resumes
        current_remaining = int(args.patience) if (
            args.patience is not None and args.patience > 0) else None

        out_file = os.path.join(out_dir, f"eval_{file_id}.jsonl")
        # Determine resume point from existing eval output if present
        start_from_turn = 0
        history_msgs: List[Dict[str, str]] = []
        if os.path.exists(out_file):
            finished_turns = load_jsonl(out_file)
            if len(finished_turns) > 0:
                last_turn = finished_turns[-1]
                start_from_turn = last_turn.get("turn")
                current_remaining = last_turn.get("remaining_patience")
                # Build prior history: user -> assistant pairs from finished turns
                for r in finished_turns:
                    try:
                        uq = r.get("user_query_verified")
                        rp = r.get("response")
                        history_msgs.append({"role": "user", "content": uq})
                        history_msgs.append(
                            {"role": "assistant", "content": rp})
                    except Exception:
                        continue

        # Open for append; write each turn immediately
        output_file = open(out_file, "a+", encoding="utf-8")
        for turn in tqdm(turns[start_from_turn:]):

            # If patience is configured and exhausted, stop immediately
            if current_remaining is not None and current_remaining == 0:
                break

            turn_idx = turn.get("turn")
            active_topic = turn.get("active_topic")
            user_query_verified = turn.get("user_query_verified")
            instructions = turn.get("instructions")

            if args.system_prompt == 1:
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *history_msgs,
                    {"role": "user", "content": user_query_verified},
                ]
            else:
                # print("here")
                # exit(0)
                messages = [
                    *history_msgs,
                    {"role": "user", "content": user_query_verified},
                ]

            try:
                generation, ptok, ctok = LLM_backend(
                    args.api_key, messages, args.model_name, args.base_url, use_json_mode=False)
            except Exception as e:
                print(e)
                break
                # generation, ptok, ctok = f"[GENERATION_ERROR] {e}", 0, 0

            overall_ok, details, sub_details = check_all_instructions(
                instructions, generation, args.api_key, args.base_url)
            # Update remaining patience based on result
            if current_remaining is not None:
                if overall_ok:
                    current_remaining = int(args.patience)
                else:
                    current_remaining = max(0, current_remaining - 1)

            record = {
                "turn": turn_idx,
                "active_topic": active_topic,
                "user_query_verified": user_query_verified,
                "instructions": instructions,
                "response": generation,
                "eval": {
                    "overall_ok": overall_ok,
                    "details": details,
                    "sub_details": sub_details,
                },
                "remaining_patience": current_remaining,
            }
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            output_file.flush()
            # Extend in-memory history with this turn

            history_msgs.append(
                {"role": "user", "content": user_query_verified})
            history_msgs.append({"role": "assistant", "content": generation})


def build_parser():
    parser = argparse.ArgumentParser(
        description="Evaluate dialog generations against instructions.")
    parser.add_argument("--dialogs_dir", type=str, default="./dialog",
                        help="Directory containing dialog_*.jsonl files")
    parser.add_argument("--output_dir", type=str, default="./evaluation_wo_system",
                        help="Output directory for eval_*.jsonl")
    parser.add_argument("--start_id", type=int,
                        default=0, help="Start dialog ID")
    parser.add_argument("--end_id", type=int, default=205,
                        help="End dialog ID (inclusive)")
    parser.add_argument("--api_key", type=str, default="",
                        help="API key for model access")
    parser.add_argument("--base_url", type=str, default="", help="Base URL")
    parser.add_argument("--model_name", type=str,
                        default="llama-4-maverick", help="Model name")
    parser.add_argument("--patience", type=int, default=3,
                        help="Stop after this many consecutive failures")
    parser.add_argument("--system_prompt", type=int, default=0, help="")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    run(args)

    # messages = [
    #     {"role": "system", "content": "You are ChatGPT."},
    #     {"role": "user", "content": "Hello, how are you?"},
    # ]
    # response, ptok, ctok = LLM_backend(args.api_key, messages, args.model_name)
    # print(response)
    # print(ptok, ctok)
