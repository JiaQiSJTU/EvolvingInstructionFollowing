# encoding = "utf-8"


INIT_QUERY_SYNTHESIS_WO_STYLE = """You are a rewriting assistant. Merge the user's proposed Topic and the other instructions into one fluent, conversational user query.

# Constraints
- The user_query must reference the instruction; do NOT answer or fulfill the instruction.
- The generated user query should startwith the topic followed by the instruction in a natural way.
- Use ONLY the information in the provided Input precisely; include all of it.
- Do NOT introduce other instructions.
- The generated user query should be natural, fluent, and from the perspective of the user.

# Input

## Topic
{topic_query}

## Instruction
{instructions}

# Output
```json
{{
    "user_query": "xxx"
}}
```
"""

TOPIC_CHANGE_QUERY_SYNTHESIS_WO_STYLE = """The user returns to a previously discussed topic and adds a new instruction in a conversation. Write a natural transitional query that reconnects to the topic and states the new instruction.

# Constraints
- Begin with a recalling/transition phrase (e.g., "Going back to the topic on ...", "Regarding the earlier topic on ...").
- The user_query must reference the instruction; do NOT answer or fulfill the instruction.
- Do NOT restate prior details of the topic. Focus on the new instruction precisely. It contains the following three categories:
    - add: introduce a new instruction.
    - remove: omit a prior instruction.
    - modify: change an old instruction.
- Do NOT introduce other instructions.
- The generated user query should be natural, fluent, and from the perspective of the user.

# Input

## Topic
{topic_query}

## Instruction
{instructions}

# Output
```json
{{
    "user_query": "xxx"
}}
```
"""

TOPIC_CONTINUE_QUERY_SYNTHESIS_WO_STYLE = """In a conversation, the user continues the current topic and provides a follow-up instruction that is expected to be followed by the response at turn {turn_idx}. Rewrite the instruction into a natural follow-up utterance.

# Constraints
- The user_query must reference the instruction; do NOT answer or fulfill the instruction.
- Clearly and previsely express the user's follow-up instruction. It contains the following three categories:
    - add: introduce a new instruction.
    - remove: omit a prior instruction.
    - modify: change an old instruction.
- Do NOT introduce new information.
- The generated user query should be natural, fluent, and from the perspective of the user.

# Input Format

## Instruction
{instructions}

# Output
```json
{{
    "turn_idx": {turn_idx},
    "user_query": "xxx"
}}
```
"""

INIT_QUERY_SYNTHESIS_W_STYLE = """You are a rewriting assistant. Merge the user's Topic and the content of the Instruction into a fluent, conversational user query.

First, you should write a tone-agnostic version that combines ONLY the Topic and the Instruction.
Then rephrase that neutral version to match the user's Language Style & Tone without adding, removing, or inferring any content.

# Constraints
- Do NOT answer and Do NOT fulfill the instruction.
- The user query must be composed ONLY from Topic and Instruction; include all and only their content.
- The user query should start with the Topic and naturally lead into the Instruction.
- The user query should sound natural, fluent, and from the user's perspective.
- Reflect style & tone implicitly (word choice, register, rhythm, punctuation, etc.); never mention style terms explicitly.

# Input

## Topic
{topic_query}

## Instruction
{instructions}

## Language Style & Tone
{style}

# Output
```json
{{
    "user_query_neutral": "the neutral user query",
    "user_query": "the styled user query"
}}
```
"""

TOPIC_CHANGE_QUERY_SYNTHESIS_W_STYLE = """You are a rewriting assistant. The user returns to a previously discussed topic and adds a new instruction. Write a transitional user query that reconnects to the topic and states the new instruction.

First, you should write a tone-agnostic version using ONLY the Topic and Instruction.
Then rephrase that neutral version to match the user's Language Style & Tone without changing content.

# Constraints
- Begin with a recalling/transition phrase (e.g., "Going back to the topic on ...", "Regarding the earlier topic on ...").
- Do NOT answer or fulfill the instruction.
- Do NOT restate prior details of the topic. Focus precisely on the new instruction. It contains three categories:
    - add: introduce a new instruction.
    - remove: omit a prior instruction.
    - modify: change an old instruction.
- The user query must use ONLY the Topic + Instruction; fully preserve the Instruction content; for the Topic, mention it only via ONLY one keyword.
- The user query should be natural, fluent, and from the user's perspective.
- Reflect style & tone implicitly (word choice, register, rhythm, punctuation, etc.); never mention style terms explicitly.


# Input

## Topic
{topic_query}

## Instruction
{instructions}

## Language Style & Tone
{style}

# Output
```json
{{
    "user_query_neutral": "the neutral user query",
    "user_query": "the styled user query"
}}
```
"""

TOPIC_CONTINUE_QUERY_SYNTHESIS_W_STYLE = """You are a rewriting assistant. The user continues the current topic and provides a follow-up instruction. Produce a natural follow-up user query.

First, you should write a tone-agnostic version from ONLY the Instruction.
Then rephrase that neutral version to match the user's Language Style & Tone without changing content.

# Constraints
- Do NOT answer and Do NOT fulfill the instruction.
- Clearly and precisely express the follow-up instruction. It contains three categories:
    - add: introduce a new instruction.
    - remove: omit a prior instruction.
    - modify: change an old instruction.
- The user query must use ONLY the provided Instruction. It should be natural, fluent, and from the user's perspective.
- Reflect style & tone implicitly (word choice, register, rhythm, punctuation, etc.); never mention style terms explicitly.


# Input Format

## Instruction
{instructions}

## Language Style & Tone
{style}

# Output
```json
{{
    "user_query_neutral": "the neutral user query",
    "user_query": "the styled user query"
}}
```
"""