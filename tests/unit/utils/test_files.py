"""Report writes either replace a complete file or leave the previous file intact."""

import pytest

from smart_data_inspector.utils.files import write_text_atomic


def test_atomic_write_creates_parents_and_replaces_complete_report(tmp_path):
    path = tmp_path / "new" / "report.md"
    write_text_atomic(path, "café\n")
    assert path.read_bytes() == "café\n".encode()
    write_text_atomic(path, "replacement\n")
    assert path.read_text() == "replacement\n"
    assert list(path.parent.iterdir()) == [path]


def test_encoding_failure_does_not_truncate_existing_file(tmp_path):
    path = tmp_path / "report.md"
    path.write_text("keep")
    with pytest.raises(UnicodeError):
        write_text_atomic(path, "\ud800")
    assert path.read_text() == "keep"
    assert list(tmp_path.iterdir()) == [path]


def test_replace_failure_keeps_existing_report_and_removes_temporary_file(tmp_path, monkeypatch):
    path = tmp_path / "report.md"
    path.write_text("keep")

    def fail_replace(*args):
        raise PermissionError("simulated failure")

    monkeypatch.setattr("smart_data_inspector.utils.files.os.replace", fail_replace)
    with pytest.raises(PermissionError, match="simulated"):
        write_text_atomic(path, "replacement")
    assert path.read_text() == "keep"
    assert list(tmp_path.iterdir()) == [path]
