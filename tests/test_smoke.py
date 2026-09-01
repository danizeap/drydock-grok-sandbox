"""Tests for drydock_sandbox.smoke.seaworthy_greeting."""

import pytest

from drydock_sandbox.smoke import seaworthy_greeting


def test_greets_a_plain_name():
    assert seaworthy_greeting("Grok") == "Ahoy, Grok! The deck is seaworthy."


def test_strips_surrounding_whitespace():
    assert seaworthy_greeting("  Grok  ") == "Ahoy, Grok! The deck is seaworthy."


def test_is_pure_and_repeatable():
    assert seaworthy_greeting("Grok") == seaworthy_greeting("Grok")


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_rejects_empty_names(name):
    with pytest.raises(ValueError):
        seaworthy_greeting(name)
