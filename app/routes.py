from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask import current_app
from openai import OpenAI

bp = Blueprint('main', __name__)

DIFFICULTY_LEVELS = {
    1: "入門 (CEFR: A1-A2)",
    2: "初級 (CEFR: A2-B1)",
    3: "中級 (CEFR: B1-B2)",
    4: "上級 (CEFR: B2-C1)",
    5: "最上級 (CEFR: C1-C2)"
}

TEXT_STYLES = [
    "アカデミック",
    "ビジネス",
    "公式文書",
    "法的文書",
    "プレスリリース",
    "ニュース記事",
    "エッセイ",
    "物語文",
    "ユーザーマニュアル",
    "日常会話"
]

def get_openai_client():
    return OpenAI(api_key=current_app.config['OPENAI_API_KEY'])

def generate_text(difficulty, style, target_words=None):
    client = get_openai_client()
    
    difficulty_mapping = {
            1: """Elementary (CEFR: A1-A2)
            - Use basic everyday expressions and simple phrases
            - Focus on concrete, immediate needs
            - Keep sentence structure simple""",
            
            2: """Pre-Intermediate (CEFR: A2-B1)
            - Use common expressions about familiar topics
            - Include basic personal and situational information
            - Maintain simple but connected text""",
            
            3: """Intermediate (CEFR: B1-B2)
            - Cover familiar topics and personal interests
            - Include simple explanations and descriptions
            - Use clear standard language""",
            
            4: """Upper-Intermediate (CEFR: B2-C1)
            - Include both concrete and abstract topics
            - Use detailed explanations
            - Express viewpoints with pros and cons""",
            
            5: """Advanced (CEFR: C1-C2)
            - Use complex language structures
            - Include detailed discussions
            - Express nuanced meanings"""
        }
    
    style_mapping = {
        "アカデミック": """Academic""",
        "ビジネス": """Business""",
        "公式文書": """Official Document""",
        "法的文書": """Legal Document""",
        "プレスリリース": """Press Release""",
        "ニュース記事": """News Article""",
        "エッセイ": """Essay""",
        "物語文": """Story""",
        "ユーザーマニュアル": """User Manual""",
        "日常会話": """Daily Conversation"""
    }
    
    user_prompt = f"""Create an English text strictly following these guidelines:

1. Style-Specific Requirements:
Style: {style_mapping[style]}
- First, identify and maintain the core characteristics of this style (tone, structure, formatting)
- Then envision the wide range of potential topics that can be expressed within these style constraints
- Each generation should cover a different topic within this style
- Be creative while maintaining style authenticity

2. Difficulty Level Requirements:
Difficulty: {difficulty_mapping[difficulty]}

3. Content Requirements:
- Length: About 130-150 words
"""

    if target_words:
        user_prompt += f"\n- Naturally incorporate these words into the text: {', '.join(target_words)}"
        
    user_prompt += """\n\n4. Respond in this format:
[ENGLISH]
(English text, only the plain text content with no markdown formatting, no asterisks, no hashtags, or any other markup symbols. Do not include any title.)

[JAPANESE]
(Japanese translation)
"""
    
    system_prompt = """You are an expert in creating diverse and engaging English reading texts. For each generation, select a unique and interesting topic within the specified style while maintaining authenticity and appropriate difficulty level."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=1.0,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        current_app.logger.error(f"OpenAI API error: {str(e)}")
        raise

@bp.route('/')
def index():
    """トップページの表示"""
    return render_template('index.html')

@bp.route('/customize', methods=['GET'])
def customize():
    """カスタマイズページの表示"""
    return render_template(
        'customize.html',
        difficulties=DIFFICULTY_LEVELS,
        styles=TEXT_STYLES
    )

@bp.route('/generate', methods=['POST'])
def generate():
    """文章生成のハンドリング"""
    try:
        try:
            difficulty = int(request.form.get('difficulty', 3))
            if difficulty not in DIFFICULTY_LEVELS:
                flash('難易度の選択が正しくありません。適切な難易度を選択してください。', 'error')
                return redirect(url_for('main.customize'))
        except ValueError:
            flash('難易度の値が不正です。', 'error')
            return redirect(url_for('main.customize'))

        style = request.form.get('style')
        if not style or style not in TEXT_STYLES:
            flash('文章スタイルの選択が正しくありません。適切なスタイルを選択してください。', 'error')
            return redirect(url_for('main.customize'))

        target_words = request.form.getlist('target_words[]')
        target_words = [word.strip() for word in target_words if word.strip() and word.replace(' ', '').isalpha()]
        if len(target_words) > 5:
            flash('指定できる単語は5つまでです。', 'error')
            return redirect(url_for('main.customize'))

        try:
            generated_content = generate_text(difficulty, style, target_words)
            session['generated_content'] = generated_content
            return redirect(url_for('main.reading'))
        except Exception as api_error:
            current_app.logger.error(f"OpenAI API error: {str(api_error)}")
            flash('文章の生成中にエラーが発生しました。しばらく時間をおいてから再度お試しください。', 'error')
            return redirect(url_for('main.customize'))

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        flash('申し訳ございません。システムエラーが発生しました。しばらく時間をおいてから再度お試しください。', 'error')
        return redirect(url_for('main.customize'))

@bp.route('/reading')
def reading():
    """読解ページの表示"""
    generated_content = session.get('generated_content')
    if not generated_content:
        return redirect(url_for('main.customize'))
    
    english_text = ""
    japanese_text = ""
    
    parts = generated_content.split('[JAPANESE]')
    if len(parts) == 2:
        english_part = parts[0].split('[ENGLISH]')
        if len(english_part) == 2:
            english_text = english_part[1].strip()
            japanese_text = parts[1].strip()
    
    return render_template('reading.html', 
                          english_text=english_text,
                          japanese_text=japanese_text)

@bp.route('/terms')
def terms():
    """利用規約ページの表示"""
    return render_template('terms.html')

@bp.route('/privacy')
def privacy():
    """プライバシーポリシーページの表示"""
    return render_template('privacy.html')