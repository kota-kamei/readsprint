"""英文生成: プロンプト構築・OpenAI呼び出し・レスポンスのパース。"""

import re

from flask import current_app
from openai import OpenAI

from app.content import DIFFICULTIES, STYLES

SYSTEM_PROMPT = """You are an expert in creating diverse and engaging English reading texts. For each generation, select a unique and interesting topic within the specified style while maintaining authenticity and appropriate difficulty level."""

RESPONSE_FORMAT = """Respond in this format:
[ENGLISH]
(English text, only the plain text content with no markdown formatting, no asterisks, no hashtags, or any other markup symbols. Do not include any title.)

[JAPANESE]
(Japanese translation of the English text)

[VOCAB]
(3 to 5 words or phrases from the text that readers at this level may find difficult, one per line, in the format "word: 日本語の意味")

[QUIZ]
(1 true/false comprehension statement about the content of the text. Randomly decide whether to write a true statement or a false one. Format: "English statement | TRUE" if the statement matches the text, or "English statement | FALSE | 解説" if it does not. The 解説 must be a concise Japanese explanation of how the statement differs from what the text actually says.)"""


class GenerationError(Exception):
    """生成またはパースに失敗したことを示す。"""


def build_user_prompt(difficulty, style, target_words=None):
    prompt = f"""Create an English text strictly following these guidelines:

1. Style-Specific Requirements:
Style: {STYLES[style]['prompt']}
- First, identify and maintain the core characteristics of this style (tone, structure, formatting)
- Each generation should cover a different topic within this style
- Be creative while maintaining style authenticity

2. Difficulty Level Requirements:
Difficulty: {DIFFICULTIES[difficulty]['prompt']}

3. Content Requirements:
- Length: About 130 words
"""

    if target_words:
        prompt += f"\n- Naturally incorporate these words into the text: {', '.join(target_words)}"

    prompt += f"\n\n4. {RESPONSE_FORMAT}\n"
    return prompt


def _extract_section(text, name):
    match = re.search(rf'\[{name}\]\s*(.*?)(?=\n\s*\[[A-Z]+\]|\Z)', text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_vocab(section):
    vocab = []
    for line in section.splitlines():
        line = line.strip().lstrip('-•0123456789. ')
        for sep in (':', ':', ' - '):
            if sep in line:
                word, meaning = line.split(sep, 1)
                if word.strip() and meaning.strip():
                    vocab.append({'word': word.strip(), 'meaning': meaning.strip()})
                break
    return vocab[:5]


def _parse_quiz(section):
    quiz = []
    for line in section.splitlines():
        line = line.strip().lstrip('-•0123456789. ')
        parts = [part.strip() for part in line.split('|')]
        if len(parts) < 2:
            continue
        statement, answer = parts[0], parts[1].upper()
        explanation = parts[2] if len(parts) > 2 else ''
        if statement and answer in ('TRUE', 'FALSE'):
            quiz.append({
                'statement': statement,
                'answer': answer == 'TRUE',
                'explanation': explanation,
            })
    return quiz[:1]


def parse_response(content):
    """LLMの出力を構造化する。英文と日本語訳が取れなければ GenerationError。

    語彙・クイズは取れなくても致命的ではないため、空のまま許容する。
    """
    english = _extract_section(content, 'ENGLISH')
    japanese = _extract_section(content, 'JAPANESE')

    if not english or not japanese:
        raise GenerationError("Failed to parse ENGLISH/JAPANESE sections")

    return {
        'english_paragraphs': [p.strip() for p in english.splitlines() if p.strip()],
        'japanese_paragraphs': [p.strip() for p in japanese.splitlines() if p.strip()],
        'vocab': _parse_vocab(_extract_section(content, 'VOCAB')),
        'quiz': _parse_quiz(_extract_section(content, 'QUIZ')),
        'word_count': len(english.split()),
    }


def _call_api(user_prompt):
    client = OpenAI(
        api_key=current_app.config['OPENAI_API_KEY'],
        timeout=30.0,
        max_retries=1,
    )
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=1.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def generate_reading(difficulty, style, target_words=None):
    """英文教材を生成して構造化データで返す。パース失敗時は1回だけ再生成する。"""
    user_prompt = build_user_prompt(difficulty, style, target_words)

    last_error = None
    for attempt in range(2):
        try:
            content = _call_api(user_prompt)
            material = parse_response(content)
            material['difficulty_label'] = DIFFICULTIES[difficulty]['label']
            material['style'] = style
            return material
        except GenerationError as e:
            current_app.logger.warning(f"Parse failed (attempt {attempt + 1}): {e}")
            last_error = e
        except Exception as e:
            current_app.logger.error(f"OpenAI API error: {e}")
            raise GenerationError(str(e)) from e

    raise last_error
