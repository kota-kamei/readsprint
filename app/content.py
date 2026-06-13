"""難易度・レベル・文章スタイルの定義。

画面表示(label)とプロンプト(prompt)を1か所で管理する。
ユーザーには LEVELS の3段階を提示し、生成時に各レベルへ割り当てられた
DIFFICULTIES(内部5段階)のいずれかをランダムに選んで使う。
"""

DIFFICULTIES = {
    1: {
        "label": "CEFR A1-A2",
        "prompt": """Elementary (CEFR: A1-A2)
- Use basic everyday expressions and simple phrases
- Focus on concrete, immediate needs
- Keep sentence structure simple""",
    },
    2: {
        "label": "CEFR A2-B1",
        "prompt": """Pre-Intermediate (CEFR: A2-B1)
- Use common expressions about familiar topics
- Include basic personal and situational information
- Maintain simple but connected text""",
    },
    3: {
        "label": "CEFR B1-B2",
        "prompt": """Intermediate (CEFR: B1-B2)
- Cover familiar topics and personal interests
- Include simple explanations and descriptions
- Use clear standard language""",
    },
    4: {
        "label": "CEFR B2-C1",
        "prompt": """Upper-Intermediate (CEFR: B2-C1)
- Include both concrete and abstract topics
- Use detailed explanations
- Express viewpoints with pros and cons""",
    },
    5: {
        "label": "CEFR C1-C2",
        "prompt": """Advanced (CEFR: C1-C2)
- Use complex language structures
- Include detailed discussions
- Express nuanced meanings""",
    },
}

# ユーザー向けの3段階レベル。difficulties に挙げた内部難易度から
# 生成のたびにランダムに1つ選ばれる。
LEVELS = {
    1: {
        "label": "初級",
        "cefr": "CEFR A1-B1",
        "description": "身近な話題のやさしい英文",
        "difficulties": (1, 2),
    },
    2: {
        "label": "中級",
        "cefr": "CEFR B1-B2",
        "description": "標準的な語彙と文構造の英文",
        "difficulties": (3,),
    },
    3: {
        "label": "上級",
        "cefr": "CEFR B2-C2",
        "description": "抽象的な話題を含む高度な英文",
        "difficulties": (4, 5),
    },
}

STYLES = {
    "ニュース記事": {
        "description": "時事を伝える報道スタイル",
        "prompt": """News article reporting on a current event
- Objective journalistic style with a lead paragraph and supporting details
- Possible topics: economy, science, culture, sports, environment, local events""",
    },
    "エッセイ": {
        "description": "個人の視点で語る文章",
        "prompt": """Essay expressing a personal viewpoint or reflection
- Clear thesis with supporting reasoning, engaging voice
- Possible topics: lifestyle, society, learning, technology and life, culture""",
    },
    "物語文": {
        "description": "短い物語・フィクション",
        "prompt": """Story (short narrative fiction)
- Characters, setting, and a small narrative arc within the length limit
- Possible genres: slice of life, mystery, adventure, fantasy, humor""",
    },
    "ビジネス": {
        "description": "メール・レポートなどの実務文",
        "prompt": """Business writing, such as an email, memo, report, or proposal
- Professional and purposeful tone
- Possible topics: negotiations, marketing, project updates, workplace policies, customer relations""",
    },
    "日常会話": {
        "description": "2人のやり取りの対話形式",
        "prompt": """Daily conversation between two people, written as a dialogue (A: / B:)
- Natural spoken expressions and turn-taking
- Possible situations: shopping, travel, friends catching up, asking for help, making plans""",
    },
}
