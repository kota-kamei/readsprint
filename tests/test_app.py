import pytest

from app import create_app
from app.generator import parse_response, build_user_prompt, GenerationError
from app.content import DIFFICULTIES, LEVELS, STYLES

SAMPLE_RESPONSE = """[ENGLISH]
The quick brown fox jumps over the lazy dog.

It was a sunny day in the village.

[JAPANESE]
素早い茶色のキツネは怠け者の犬を飛び越えます。

村は晴れた日でした。

[VOCAB]
lazy: 怠け者の
village: 村

[QUIZ]
It was raining in the village. | FALSE | 本文では村は晴れた日だったと述べられています。
"""

SAMPLE_MATERIAL = {
    'english_paragraphs': ['Hello world.'],
    'japanese_paragraphs': ['こんにちは世界。'],
    'vocab': [],
    'quiz': [],
    'word_count': 2,
    'difficulty_label': DIFFICULTIES[3]['label'],
    'style': 'エッセイ',
}


@pytest.fixture
def app():
    return create_app('testing')


@pytest.fixture
def client(app):
    return app.test_client()


class TestParseResponse:
    def test_full_response(self):
        material = parse_response(SAMPLE_RESPONSE)
        assert len(material['english_paragraphs']) == 2
        assert len(material['japanese_paragraphs']) == 2
        assert material['word_count'] == 17
        assert material['vocab'] == [
            {'word': 'lazy', 'meaning': '怠け者の'},
            {'word': 'village', 'meaning': '村'},
        ]
        assert material['quiz'] == [
            {'statement': 'It was raining in the village.', 'answer': False,
             'explanation': '本文では村は晴れた日だったと述べられています。'},
        ]

    def test_missing_japanese_raises(self):
        with pytest.raises(GenerationError):
            parse_response("[ENGLISH]\nSome text only.")

    def test_missing_vocab_and_quiz_is_tolerated(self):
        material = parse_response("[ENGLISH]\nText.\n\n[JAPANESE]\n訳。")
        assert material['vocab'] == []
        assert material['quiz'] == []

    def test_malformed_quiz_lines_are_skipped(self):
        response = SAMPLE_RESPONSE + "\nbroken line without separator\nstatement | MAYBE\n"
        material = parse_response(response)
        assert len(material['quiz']) == 1

    def test_true_statement_without_explanation(self):
        response = "[ENGLISH]\nText.\n\n[JAPANESE]\n訳。\n\n[QUIZ]\nA statement. | TRUE"
        material = parse_response(response)
        assert material['quiz'] == [
            {'statement': 'A statement.', 'answer': True, 'explanation': ''},
        ]


class TestBuildPrompt:
    def test_contains_difficulty_and_style(self):
        prompt = build_user_prompt(3, 'エッセイ', ['apple'])
        assert DIFFICULTIES[3]['prompt'] in prompt
        assert STYLES['エッセイ']['prompt'] in prompt
        assert 'apple' in prompt

    def test_all_definitions_are_usable(self):
        for difficulty in DIFFICULTIES:
            for style in STYLES:
                assert build_user_prompt(difficulty, style)

    def test_levels_cover_all_difficulties(self):
        covered = {d for info in LEVELS.values() for d in info['difficulties']}
        assert covered == set(DIFFICULTIES)


class TestRoutes:
    @pytest.mark.parametrize('path', ['/', '/customize', '/terms', '/privacy'])
    def test_static_pages(self, client, path):
        assert client.get(path).status_code == 200

    def test_reading_without_session_redirects(self, client):
        response = client.get('/reading')
        assert response.status_code == 302
        assert '/customize' in response.headers['Location']

    def test_reading_with_material(self, client):
        with client.session_transaction() as sess:
            sess['reading'] = dict(SAMPLE_MATERIAL)
        response = client.get('/reading')
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        assert 'Hello world.' in html
        assert '2 words' in html

    def test_generate_success(self, client, monkeypatch):
        monkeypatch.setattr('app.routes.generate_reading',
                            lambda *args, **kwargs: dict(SAMPLE_MATERIAL))
        response = client.post('/generate', data={'level': '2', 'style': 'エッセイ'})
        assert response.status_code == 302
        assert '/reading' in response.headers['Location']

    def test_generate_remembers_settings(self, client, monkeypatch):
        monkeypatch.setattr('app.routes.generate_reading',
                            lambda *args, **kwargs: dict(SAMPLE_MATERIAL))
        client.post('/generate', data={'level': '3', 'style': '物語文'})
        html = client.get('/customize').get_data(as_text=True)
        assert 'value="3" checked' in html
        assert 'value="物語文" checked' in html

    def test_generate_invalid_level(self, client):
        response = client.post('/generate', data={'level': '9', 'style': 'エッセイ'})
        assert response.status_code == 302
        assert '/customize' in response.headers['Location']

    def test_generate_too_many_words(self, client):
        response = client.post('/generate', data={
            'level': '2', 'style': 'エッセイ',
            'target_words[]': ['one', 'two', 'three', 'four'],
        })
        assert response.status_code == 302
        assert '/customize' in response.headers['Location']

    def test_generate_accepts_three_words(self, client, monkeypatch):
        monkeypatch.setattr('app.routes.generate_reading',
                            lambda *args, **kwargs: dict(SAMPLE_MATERIAL))
        response = client.post('/generate', data={
            'level': '2', 'style': 'エッセイ',
            'target_words[]': ['one', 'two', 'three'],
        })
        assert response.status_code == 302
        assert '/reading' in response.headers['Location']

    def test_generate_invalid_style(self, client):
        response = client.post('/generate', data={'level': '2', 'style': '存在しない'})
        assert response.status_code == 302
        assert '/customize' in response.headers['Location']

    def test_generate_failure_shows_error(self, client, monkeypatch):
        def fail(*args, **kwargs):
            raise GenerationError('boom')
        monkeypatch.setattr('app.routes.generate_reading', fail)
        response = client.post('/generate', data={'level': '2', 'style': 'エッセイ'},
                               follow_redirects=True)
        assert 'エラーが発生しました' in response.get_data(as_text=True)

    def test_regenerate_without_settings_redirects(self, client):
        response = client.post('/regenerate')
        assert response.status_code == 302
        assert '/customize' in response.headers['Location']

    def test_regenerate_with_legacy_settings_redirects(self, client):
        with client.session_transaction() as sess:
            sess['settings'] = {'difficulty': 2, 'style': 'エッセイ', 'target_words': []}
        response = client.post('/regenerate')
        assert response.status_code == 302
        assert '/customize' in response.headers['Location']

    def test_regenerate_uses_saved_settings(self, client, monkeypatch):
        captured = {}

        def fake_generate(difficulty, style, target_words):
            captured.update(difficulty=difficulty, style=style)
            return dict(SAMPLE_MATERIAL)
        monkeypatch.setattr('app.routes.generate_reading', fake_generate)

        with client.session_transaction() as sess:
            sess['settings'] = {'level': 1, 'style': 'ビジネス', 'target_words': []}
        response = client.post('/regenerate')
        assert response.status_code == 302
        assert '/reading' in response.headers['Location']
        assert captured['style'] == 'ビジネス'
        assert captured['difficulty'] in LEVELS[1]['difficulties']
