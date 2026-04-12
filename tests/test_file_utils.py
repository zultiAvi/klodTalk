"""Tests for file_utils module."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from utils.file_utils import read_file, write_file


class TestReadFile:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        assert read_file(str(f)) == "hello world"

    def test_read_nonexistent_file(self, tmp_path):
        assert read_file(str(tmp_path / "nope.txt")) == ""

    def test_read_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert read_file(str(f)) == ""

    def test_read_multiline_file(self, tmp_path):
        f = tmp_path / "multi.txt"
        content = "line1\nline2\nline3"
        f.write_text(content)
        assert read_file(str(f)) == content

    def test_read_unicode(self, tmp_path):
        f = tmp_path / "unicode.txt"
        content = "\u05e9\u05dc\u05d5\u05dd"
        f.write_text(content)
        assert read_file(str(f)) == content

    def test_read_large_file(self, tmp_path):
        f = tmp_path / "large.txt"
        content = "x" * 100_000
        f.write_text(content)
        assert len(read_file(str(f))) == 100_000


class TestWriteFile:
    def test_write_creates_file(self, tmp_path):
        path = str(tmp_path / "new.txt")
        write_file(path, "content")
        assert os.path.isfile(path)
        with open(path) as f:
            assert f.read() == "content"

    def test_write_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "a" / "b" / "c" / "deep.txt")
        write_file(path, "deep")
        with open(path) as f:
            assert f.read() == "deep"

    def test_write_overwrites(self, tmp_path):
        path = str(tmp_path / "over.txt")
        write_file(path, "first")
        write_file(path, "second")
        with open(path) as f:
            assert f.read() == "second"

    def test_write_empty_content(self, tmp_path):
        path = str(tmp_path / "empty.txt")
        write_file(path, "")
        with open(path) as f:
            assert f.read() == ""

    def test_write_multiline(self, tmp_path):
        path = str(tmp_path / "multi.txt")
        content = "line1\nline2\nline3"
        write_file(path, content)
        with open(path) as f:
            assert f.read() == content
