# encoding = "utf-8"

import json
from argparse import ArgumentParser
import os
import numpy as np
import random


def main(args):

    input_dir = args.input_dir

    total_dialog_number = args.end_id + 1 - args.start_id

    # Number of turns survived (regardless of correctness)
    total_survival_turns = []
    total_success_turns = []  # Number of turns survived where overall_ok=True for each turn
    # Number of turns survived, tracking per-turn constraint satisfaction
    total_constraints_turns = []

    # Maximum length of consecutive successful turns
    maximum_consecutive_successful_length = []

    # total_failed_count = [0] * total_dialog_number # Total failures where overall_ok=False (excluding the final consecutive failures); can be derived from total_survival_turn and total_success_turns
    # Total number of recoveries in a dialog (excluding the final consecutive failures)
    total_recovery_count = []

    turn_number_survival_ratio = [0.0] * 100  # Survival ratio per turn index
    constraint_pass_rate = {}  # For each constraint: total occurrences and successes

    # (# satisfied constraints) / (total constraints) per turn
    micro_constraint_pass_rate = []
    micro_turn_pass_rate = 0.0  # (# successful turns) / (total turns)

    idx_list = []
    for idx in range(args.start_id, args.end_id + 1):
        input_path = os.path.join(input_dir, f"eval_{idx}.jsonl")

        if os.path.exists(input_path):
            idx_list.append(idx)

    if args.random_num:
        chosen_idx_list = random.sample(idx_list, args.random_num)
    else:
        chosen_idx_list = idx_list

    dialog_idx = -1
    for idx in chosen_idx_list:
        input_path = os.path.join(input_dir, f"eval_{idx}.jsonl")
        # if not os.path.exists(input_path):
        #     continue

        dialog_idx += 1
        # Number of turns survived (regardless of correctness)
        total_survival_turns.append(0.0)
        # Number of turns survived where overall_ok=True for each turn
        total_success_turns.append(0.0)
        # Per-turn constraint satisfaction while surviving
        total_constraints_turns.append(0.0)
        # Maximum length of consecutive successful turns
        maximum_consecutive_successful_length.append(0.0)
        # Total number of recoveries in a dialog
        total_recovery_count.append(0.0)

        prev_success_state = True
        current_streak = 0
        current_max_streak = 0

        with open(input_path, "r", encoding="utf-8") as f:
            turn_idx = -1
            for line in f:
                line = json.loads(line.strip())
                eval_result = line["eval"]

                turn_idx += 1

                total_survival_turns[dialog_idx] += 1
                if eval_result["overall_ok"] == True:
                    total_success_turns[dialog_idx] += 1
                    # Count consecutive successes
                    current_streak += 1
                    if current_streak > current_max_streak:
                        current_max_streak = current_streak
                else:
                    # Reset the consecutive-success counter on failure
                    current_streak = 0

                total_constraints_turns[dialog_idx] += sum(
                    eval_result["details"].values()) / len(eval_result["details"])

                micro_constraint_pass_rate.append(
                    sum(eval_result["details"].values()) / len(eval_result["details"]))

                turn_number_survival_ratio[turn_idx] += 1

                for key in eval_result["details"]:
                    if key not in constraint_pass_rate:
                        constraint_pass_rate[key] = [0, 0]  # pass, total
                    constraint_pass_rate[key][1] += 1
                    if eval_result["details"][key]:
                        constraint_pass_rate[key][0] += 1

                if prev_success_state == False and eval_result["overall_ok"] == True:
                    total_recovery_count[dialog_idx] += 1

                prev_success_state = eval_result["overall_ok"]

                if line["remaining_patience"] == (3 - args.patience):
                    break

        maximum_consecutive_successful_length[dialog_idx] = current_max_streak

    micro_turn_pass_rate = sum(total_success_turns) / sum(total_survival_turns)
    micro_constraint_pass_rate = np.mean(micro_constraint_pass_rate)

    constraint_pass_rate = {k: (v[0], v[1], v[0] / v[1])
                            for k, v in constraint_pass_rate.items()}

    total_failed_count = np.array(
        total_survival_turns) - np.array(total_success_turns) - 1

    robustness = np.array(total_success_turns) / np.array(total_survival_turns)

    recovery_rate = np.array(total_recovery_count) / \
        np.array(total_failed_count)

    print(f"{args.input_dir}")
    print(f"Total dialog number: {dialog_idx+1}")
    print(
        f"Endurance: {np.mean(total_survival_turns), np.mean(total_constraints_turns), np.mean(total_success_turns), }")
    print(
        f"Endurance_LSS: {np.mean(maximum_consecutive_successful_length)}")
    print(f"Constraint Satisfaction Rate (CSR): {micro_constraint_pass_rate}")
    print(f"Instruction Satisfaction Rate (ISR): {micro_turn_pass_rate}")
    print(f"Robustness: {np.mean(robustness)}")
    print(f"Recovery: {np.mean(recovery_rate)}")
    print(f"Turn number survival ratio: {turn_number_survival_ratio}")
    print(f"Constraint pass rate: {constraint_pass_rate}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input_dir", type=str,
                        default="./evaluation/mistral-large-2512", help="")
    parser.add_argument("--start_id", type=int, default=0, help="")
    parser.add_argument("--end_id", type=int, default=205, help="")
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--random_num", type=int, default=None, help="")
    parser.add_argument("--random_seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.random_seed)
    main(args)
