# tests/test_main.py
# Tests for main.py (get_github_users, write_results_txt/csv, compare_github_relationships)
import io
import os
import csv
import tempfile
from unittest.mock import patch, MagicMock
import pytest
import sys

# Setting the path to the module to be tested
sys.path.append('../github-follower-analyzer')
import main


def make_response(status=200, json_data=None, headers=None, text=""):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data if json_data is not None else []
    resp.headers = headers or {}
    resp.text = text
    # raise_for_status exists but only used in some places; keep as no-op when status is 200
    def raise_for_status():
        if status >= 400:
            raise Exception(f"HTTP {status}")
    resp.raise_for_status = MagicMock(side_effect=raise_for_status if status >= 400 else lambda: None)
    return resp

def test_get_github_users_single_page(monkeypatch):
    sample = [{"login": "Alice"}, {"login": "Bob"}]
    resp = make_response(status=200, json_data=sample, headers={})
    with patch("main.requests.get", return_value=resp) as mock_get:
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        assert isinstance(result, set)
        assert result == {"alice", "bob"}
        mock_get.assert_called()

def test_get_github_users_pagination(monkeypatch):
    # First page returns data and link with rel="next"; second returns empty list ending pagination
    resp1 = make_response(status=200, json_data=[{"login": "User1"}], headers={"link": '<https://api?page=2>; rel="next"'})
    resp2 = make_response(status=200, json_data=[])
    with patch("main.requests.get", side_effect=[resp1, resp2]) as mock_get:
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        assert result == {"user1"}
        assert mock_get.call_count == 2

def test_get_github_users_auth_error_returns_none():
    resp = make_response(status=401, json_data={"message": "bad credentials"})
    with patch("main.requests.get", return_value=resp):
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        assert result is None

def test_get_github_users_forbidden_returns_none():
    resp = make_response(status=403, json_data={"message": "forbidden"}, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "12345"})
    with patch("main.requests.get", return_value=resp):
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        assert result is None

def test_write_results_txt_and_csv(tmp_path):
    non_followers = {"alice", "charlie"}
    fans = {"bob"}
    txt_file = tmp_path / "out.txt"
    csv_file = tmp_path / "out.csv"

    main.write_results_txt(non_followers, fans, str(txt_file))
    assert txt_file.exists()
    content = txt_file.read_text(encoding="utf-8")
    assert "alice" in content and "bob" in content and "charlie" in content

    main.write_results_csv(non_followers, fans, str(csv_file))
    assert csv_file.exists()
    # Quick CSV structure check
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        # Expect header row and at least one username row
        assert any("Users you follow who DO NOT follow you back" in row[0] for row in reader if row), "CSV header missing"

def test_compare_github_relationships_outputs_and_writes(tmp_path, capsys):
    # Patch get_github_users to return followers and following sets
    followers = {"a", "b"}
    following = {"b", "c"}
    def fake_get(url, token, label):
        return followers if "followers" in url else following

    with patch.object(main, "get_github_users", side_effect=fake_get):
        out_file = tmp_path / "results.txt"
        main.compare_github_relationships(output_file=str(out_file), output_format="txt")
        captured = capsys.readouterr()
        # Basic assertions on printed totals and expected usernames
        assert "Total Followers: 2" in captured.out
        assert "Total Following: 2" in captured.out
        # Ensure results file was written
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "c" in content and "a" in content