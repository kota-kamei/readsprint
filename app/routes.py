import random

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask import current_app

from app.content import LEVELS, STYLES
from app.generator import generate_reading, GenerationError

bp = Blueprint('main', __name__)

DEFAULT_LEVEL = 2


def _generate_and_show(settings):
    """設定をもとに生成し、結果をセッションへ保存して読解ページへ。

    レベルに割り当てられた内部難易度から1つをランダムに選んで生成する。
    """
    difficulty = random.choice(LEVELS[settings['level']]['difficulties'])
    try:
        material = generate_reading(
            difficulty, settings['style'], settings['target_words']
        )
    except GenerationError:
        flash('文章の生成中にエラーが発生しました。しばらく時間をおいてから再度お試しください。', 'error')
        return redirect(url_for('main.customize'))

    material['level_label'] = LEVELS[settings['level']]['label']
    session['settings'] = settings
    session['reading'] = material
    return redirect(url_for('main.reading'))


@bp.route('/')
def index():
    """トップページの表示"""
    return render_template('index.html')


@bp.route('/customize', methods=['GET'])
def customize():
    """カスタマイズページの表示(前回の設定を初期選択にする)"""
    settings = session.get('settings', {})
    selected_level = settings.get('level')
    selected_style = settings.get('style')
    return render_template(
        'customize.html',
        levels=LEVELS,
        styles=STYLES,
        selected_level=selected_level if selected_level in LEVELS else DEFAULT_LEVEL,
        selected_style=selected_style if selected_style in STYLES else None,
    )


@bp.route('/generate', methods=['POST'])
def generate():
    """文章生成のハンドリング"""
    try:
        level = int(request.form.get('level', DEFAULT_LEVEL))
        if level not in LEVELS:
            raise ValueError
    except ValueError:
        flash('レベルの選択が正しくありません。適切なレベルを選択してください。', 'error')
        return redirect(url_for('main.customize'))

    style = request.form.get('style')
    if not style or style not in STYLES:
        flash('文章スタイルの選択が正しくありません。適切なスタイルを選択してください。', 'error')
        return redirect(url_for('main.customize'))

    target_words = request.form.getlist('target_words[]')
    target_words = [word.strip() for word in target_words
                    if word.strip() and word.replace(' ', '').isalpha()]
    if len(target_words) > 3:
        flash('指定できる単語は3つまでです。', 'error')
        return redirect(url_for('main.customize'))

    return _generate_and_show({
        'level': level,
        'style': style,
        'target_words': target_words,
    })


@bp.route('/regenerate', methods=['POST'])
def regenerate():
    """前回と同じ設定でもう一度生成する"""
    settings = session.get('settings')
    if (not settings or settings.get('level') not in LEVELS
            or settings.get('style') not in STYLES):
        return redirect(url_for('main.customize'))
    return _generate_and_show(settings)


@bp.route('/reading')
def reading():
    """読解ページの表示"""
    material = session.get('reading')
    if not material:
        return redirect(url_for('main.customize'))
    return render_template('reading.html', **material)


@bp.route('/terms')
def terms():
    """利用規約ページの表示"""
    return render_template('terms.html')


@bp.route('/privacy')
def privacy():
    """プライバシーポリシーページの表示"""
    return render_template('privacy.html')
