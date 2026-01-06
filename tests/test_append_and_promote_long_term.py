import os
import json
import tempfile
import shutil
import pytest

from core.functions.append_long_term_entry import append_long_term_entry
from core.functions.promote_to_long_term import promote_to_long_term

def test_append_long_term_entry_creates_file_and_appends():
    from core.functions.append_long_term_entry import append_long_term_entry
    def dummy_token_estimator(x): return 1
    def dummy_refresh(): pass
    messages = [
        {"role": "user", "content": "hi", "metadata": {"id": 1}},
        {"role": "assistant", "content": "hello", "metadata": {"id": 2}}
    ]
    long_term_context = []
    append_long_term_entry(messages, long_term_context, 100, dummy_token_estimator, dummy_refresh)
    assert isinstance(long_term_context[-1], dict)
    assert "summary" in long_term_context[-1]

def test_append_long_term_entry_handles_invalid_file():
    from core.functions.append_long_term_entry import append_long_term_entry
    def dummy_token_estimator(x): return 1
    def dummy_refresh(): pass
    # Should not raise, just append
    messages = [
        {"role": "user", "content": "hi", "metadata": {"id": 1}}
    ]
    long_term_context = []
    append_long_term_entry(messages, long_term_context, 100, dummy_token_estimator, dummy_refresh)
    assert isinstance(long_term_context[-1], dict)
    assert "summary" in long_term_context[-1]

def test_promote_to_long_term_moves_entry(tmp_path):
    from core.functions.promote_to_long_term import promote_to_long_term
    from core.functions.append_long_term_entry import append_long_term_entry
    def dummy_token_estimator(x): return 1
    def dummy_refresh(): pass
    short_entries = [
        {"role": "user", "content": "hi", "metadata": {"id": 1}},
        {"role": "assistant", "content": "hello", "metadata": {"id": 2}}
    ]
    long_entries = []
    def append_entry(messages):
        long_entries.append(messages[0])
    promote_to_long_term(short_entries[0], long_entries, 1, append_entry)
    assert long_entries[-1] == short_entries[0]

def test_promote_to_long_term_handles_missing_files(tmp_path):
    from core.functions.promote_to_long_term import promote_to_long_term
    from core.functions.append_long_term_entry import append_long_term_entry
    def dummy_token_estimator(x): return 1
    def dummy_refresh(): pass
    # Should not raise if lists are empty
    short_entries = []
    long_entries = []
    def append_entry(messages):
        long_entries.extend(messages)
    # Should not raise if message is empty
    promote_to_long_term({}, long_entries, 1, append_entry)
    assert long_entries == [{}]
    assert short_entries == []