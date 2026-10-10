"""Contract tests for the informational landing page and independent chat wizard.

These are deliberately offline: no CDC calls, private DEV/TEST questions, or
neural indexes are required for rendering the public site.
"""
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'static' / 'index.html'


def site():
    html = INDEX.read_text(encoding='utf-8')
    return BeautifulSoup(html, 'html.parser'), html


def test_homepage_explains_carebridge_instead_of_being_a_full_page_chat():
    doc, html = site()
    assert doc.select_one('main h1')
    assert doc.select_one('main #about')
    assert doc.select_one('main #how-it-works')
    assert doc.select_one('main #safety')
    assert doc.select_one('main #faq')
    assert 'academic vaccine-education chatbot prototype' in html
    assert 'public CDC' in html
    assert doc.select_one('main #widget-form') is None


def test_widget_is_separate_hidden_and_accessible_on_initial_load():
    doc, html = site()
    launcher = doc.select_one('button#bot-launcher')
    widget = doc.select_one('#chat-widget')
    assert launcher['aria-controls'] == 'chat-widget'
    assert launcher['aria-expanded'] == 'false'
    assert widget.has_attr('hidden')
    assert widget['role'] == 'dialog'
    assert doc.select_one('#widget-close')['aria-label'] == 'Close chatbot'
    assert doc.select_one('#dialogue')['aria-live'] == 'polite'
    assert doc.select_one('#widget-form input#question')['maxlength'] == '1000'
    assert doc.select_one('#widget-send')['type'] == 'submit'
    assert 'Escape' in html


def test_guided_wizard_and_optional_free_text_are_supported():
    doc, html = site()
    assert doc.select_one('#wizard-title')
    assert doc.select_one('#wizard-options')
    assert doc.select_one('#wizard-back').has_attr('hidden')
    assert 'showTopics' in html and 'showQuestions' in html
    assert 'STEP 1 OF 2' in html and 'STEP 2 OF 2' in html
    assert 'MMR & other vaccines' in html
    assert 'Vaccine Information Statement' in html
    assert len(doc.select('[data-open-assistant]')) >= 2


def test_widget_uses_existing_chat_api_and_sanitizes_source_links():
    doc, html = site()
    assert "fetch('/api/chat'" in html
    assert 'question:q,mode:mode.value,history:history.slice(-3)' in html
    assert "u.protocol==='https:'" in html
    assert "u.hostname==='cdc.gov'" in html
    assert "u.hostname==='www.cdc.gov'" in html
    assert "link.rel='noopener noreferrer'" in html
    assert "reply.body.textContent=out.answer" in html
    assert '<script src=' not in html.lower()  # No third-party widget tracking script.


def test_public_demo_does_not_misrepresent_research_neural_backend():
    doc, html = site()
    assert 'This public demo uses a small curated set' in html
    assert '163 CDC pages' in html
    assert 'The demo is not that full research system' in html
    assert doc.select_one('select#mode')
    modes = {option['value'] for option in doc.select('select#mode option')}
    assert modes == {'hybrid','bm25','dense'}
    assert 'educate, not diagnose' in html.lower()


def test_website_has_small_screen_and_keyboard_accessibility():
    doc, html = site()
    assert 'width=device-width' in doc.select_one('meta[name="viewport"]')['content']
    assert '@media(max-width:720px)' in html
    assert '@media(prefers-reduced-motion:reduce)' in html
    assert ':focus-visible' in html
    assert doc.select_one('nav[aria-label="Main navigation"]')
    assert doc.select_one('nav[aria-label="Helpful links"]')
