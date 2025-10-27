<div align= "center">
    <h1> Probing LLMs' Limits of Multi-Turn Instruction Following with an Evolving Benchmark </h1>
</div>



# Introduction

Understanding how well large language models can follow users' instructions throughout a dialogue spanning multiple topics is of great importance for data-intensive conversational applications. Existing benchmarks are often limited to a fixed number of turns, making them susceptible to saturation and failing to account for the user's interactive experience. In this work, we propose an extensible framework for assessing multi-turn instruction-following ability. At its core, our framework decouples linguistic surface forms from user intent simulation through a three-layer mechanism that tracks constraints, instructions, and topics. This framework mimics User-LLM interaction by enabling the dynamic construction of benchmarks with state changes and tracebacks, terminating a conversation only when the model exhausts a simulated user's patience. We define a suite of metrics capturing the quality of the interaction process. Using this framework, we construct EvolIF, an evolving instruction-following benchmark incorporating nine distinct constraint types. Our results indicate that GPT-5 exhibits superior instruction-following performance. It sustains an average of 18.54 conversational turns and demonstrates 70.31% robustness, outperforming Gemini-2.5-Pro by a significant margin of 11.41%, while other models lag far behind. The data and code will be made publicly available.


# Usage

## Installation

Clone this repo into your working directory and setup the environment:

```python
git clone xxx
cd EvolvingInstructionFollowing
conda create -n evolif python=3.10
conda activate evolif
pip install -r requirements.txt
```

Major requirements are listed in `requirements.txt`. 

## Benchmark Construction

```python

# Generate user intentions from scratch
python3 src/main.py --steps 50 --output_dir ./state --start_id 0 --end_id 10

# Synthesize user queries
python3 src/query_synthesis.py --input_dir ./state --output_dir ./dialog --start_id 0 --end_id 10 --api_key xxx --base_url xxx
```

## LLM Evaluation

```python
# Evaluate model
python3 src/eval.py --dialog_dir ./dialog --output_dir ./evaluation --start_id 0 --end_id 10 --model_name xxx --api_key xxx --base_url xxx

# Calculate and print results
python3 src/score.py --input_dir ./evaluation/xxx
```

# Leaderboards

| Models | CSR (%) | ISR (%) | ACT_len | ACT_acc | ACT_succ | LSS | ROB (%) | REC (%) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5 | **88.56** | **74.76** | **18.54** | **16.42** | **13.86** | **9.46** | **70.31** | <u>28.93</u> |
| Gemini-2.5-Pro | <u>83.62</u> | <u>67.79</u> | <u>14.78</u> | <u>12.36</u> | <u>10.02</u> | <u>5.96</u> | <u>59.90</u> | **28.99** |
| DeepSeek-V3.2 | 77.35 | 60.77 | 10.40 | 8.04 | 6.32 | 4.60 | 52.23 | 20.02 |
| Kimi-K2 | 76.50 | 58.86 | 10.50 | 8.03 | 6.18 | 4.44 | 51.97 | 20.63 |
| GPT-4.1 | 75.66 | 58.91 | 10.32 | 7.81 | 6.08 | 3.90 | 49.55 | 20.89 |
| Qwen3-235B | 73.10 | 57.31 | 10.26 | 7.50 | 5.88 | 4.12 | 49.67 | 19.17 |
| Grok-4-Fast | 75.12 | 56.28 | 9.88 | 7.42 | 5.56 | 3.94 | 47.76 | 19.37 |
| Llama-4-Maverick | 73.87 | 56.85 | 9.64 | 7.12 | 5.48 | 4.04 | 47.84 | 20.10 |
| Seed-1.6 | 70.10 | 54.70 | 9.14 | 6.41 | 5.00 | 3.64 | 43.99 | 19.09 |
| Mistral-Medium | 66.26 | 50.36 | 8.22 | 5.45 | 4.14 | 2.90 | 36.75 | 15.35 |





