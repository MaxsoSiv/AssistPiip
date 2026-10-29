import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.md_render import md_to_html
from core.updater import parse_version, is_newer, _validate_download_url
from core.reminders import parse_when
from core.notes_manager import Note, NotesManager
from core.command_manager import Command, CommandManager
from win.hotkey_manager import parse_combo
from ui.calculator import SafeEvaluator


def test_md_render():
    assert md_to_html("**жирный** и *курсив*") == "<b>жирный</b> и <i>курсив</i>"
    assert "<code>x</code>" in md_to_html("код `x` тут")
    assert '<a href="https://example.com">' in md_to_html("[сайт](https://example.com)")
    assert "<script>" not in md_to_html("<script>alert(1)</script>")
    assert "&lt;script&gt;" in md_to_html("<script>alert(1)</script>")
    block = md_to_html("```\nprint(1)\n```")
    assert "<pre>" in block and "print(1)" in block
    assert "<b>Заголовок</b>" in md_to_html("## Заголовок")
    assert "• " in md_to_html("- пункт")


def test_versions():
    assert parse_version("1.10.2") == (1, 10, 2)
    assert is_newer("1.2.0", "1.1.9")
    assert not is_newer("1.1.0", "1.1.0")


def test_download_url_allowlist():
    _validate_download_url("https://github.com/x/y.zip")
    for bad in ("http://github.com/x.zip", "https://evil.example.com/x.zip", "ftp://github.com/x"):
        try:
            _validate_download_url(bad)
            raise AssertionError(bad)
        except ValueError:
            pass


def test_parse_when():
    due, rest = parse_when("через 20 минут купить хлеб")
    assert rest == "купить хлеб"
    due2, rest2 = parse_when("в 19:30 позвонить")
    assert rest2 == "позвонить"
    assert parse_when("в 25:00 x") is None


def test_parse_combo():
    combo = parse_combo("Ctrl+Alt+P")
    assert combo is not None
    assert parse_combo("Ctrl+Язык") is None
    assert parse_combo("Ctrl+Ы") is not None


def test_evaluator():
    assert SafeEvaluator.evaluate("2+2*2") == 6
    assert SafeEvaluator.evaluate("2^3") == 8
    try:
        SafeEvaluator.evaluate("__import__('os')")
        raise AssertionError("must reject")
    except ValueError:
        pass


def test_note_history():
    manager = NotesManager(tempfile.mkdtemp())
    note = Note("v1", "первая")
    manager.add_note(note)
    updated = Note("v2", "вторая", note.pinned, note.created, note.id, note.history)
    manager.update_note(note, updated)
    stored = manager.all_notes()[0]
    assert stored.title == "v2"
    assert len(stored.history) == 1
    assert stored.history[0]["title"] == "v1"


def test_plugins_validation(tmp_create=True):
    data_dir = tempfile.mkdtemp()
    plugins = os.path.join(data_dir, "plugins")
    os.makedirs(plugins)
    good = {"name": "demo", "commands": [
        {"trigger": "плагин-тест", "actions": [{"type": "url", "value": "https://example.com"}]}
    ]}
    bad = {"commands": [{"trigger": "x", "actions": [{"type": "format", "value": "c"}]}]}
    json.dump(good, open(os.path.join(plugins, "good.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(bad, open(os.path.join(plugins, "bad.json"), "w", encoding="utf-8"), ensure_ascii=False)

    class _S:
        browser_path = ""

    manager = CommandManager(_S(), data_dir)
    triggers = [c.trigger for c in manager.all_commands()]
    assert "плагин-тест" in triggers
    assert "x" not in triggers
    assert manager.is_plugin("плагин-тест")
    found = manager.find_by_trigger("Плагин-Тест")
    assert found is not None and found.source == "plugin"
    assert manager._substitute("нет шаблонов") == "нет шаблонов"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {test.__name__}: {e}")
    if failed:
        raise SystemExit(1)
    print(f"ALL_TESTS_OK ({len(tests)})")


if __name__ == "__main__":
    main()
