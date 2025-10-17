# tests/test_main.py
# pytest -q
"""
Unit tests for the main module of the GitHub Follower Analyzer.

This file contains tests for the core logic of 'main.py', specifically
functions for fetching GitHub user lists (get_github_users),
writing results to files (write_results_txt/csv), and the main
comparison logic (compare_github_relationships).
"""

import csv
from unittest.mock import patch, MagicMock
import sys

# Setting the path to the module to be tested
# This ensures that 'main.py' can be imported correctly from the parent directory.
sys.path.append('../github-follower-analyzer')
import main


def make_response(status=200, json_data=None, headers=None, text=""):
    """
    Helper function to create a mock response object for 'requests.get'.
    
    This simulates the HTTP response received from the GitHub API, allowing
    for controlled testing of success, pagination, and error scenarios.
    
    :param status: HTTP status code (e.g., 200, 404).
    :param json_data: Data returned by the .json() method.
    :param headers: Dictionary of HTTP response headers.
    :param text: Raw text content of the response.
    :return: A configured MagicMock instance simulating a requests.Response.
    """
    resp = MagicMock()
    resp.status_code = status
    # Set the return value for the .json() method
    resp.json.return_value = json_data if json_data is not None else []
    resp.headers = headers or {}
    resp.text = text
    
    # Simulate the .raise_for_status() method behavior
    def raise_for_status():
        if status >= 400:
            # Raise an exception for HTTP error status codes
            raise Exception(f"HTTP {status}")
            
    # Attach the simulated behavior to the mock object
    resp.raise_for_status = MagicMock(side_effect=raise_for_status if status >= 400 else lambda: None)
    return resp

def test_get_github_users_single_page(monkeypatch):
    """
    Tests successful fetching of users when data fits on a single page.
    
    Verifies that the function correctly parses user logins and converts them to 
    lowercase in a set.
    """
    # Sample data mimicking a GitHub API response for a list of users
    sample = [{"login": "Alice"}, {"login": "Bob"}]
    # Create a mock 200 OK response with the sample data and no link header (no pagination)
    resp = make_response(status=200, json_data=sample, headers={})
    
    # Patch the 'requests.get' method to return our mock response
    with patch("main.requests.get", return_value=resp) as mock_get:
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        
        # Assertions
        assert isinstance(result, set)
        # Check that the result set contains the lowercased usernames
        assert result == {"alice", "bob"}
        # Ensure the API was called exactly once
        mock_get.assert_called()

def test_get_github_users_pagination(monkeypatch):
    """
    Tests handling of multi-page API results using the 'Link' header.
    
    Verifies that the function follows the 'rel="next"' link until no more
    pages are indicated.
    """
    # Response for the first page: one user and a 'next' link header
    resp1 = make_response(
        status=200, 
        json_data=[{"login": "User1"}], 
        headers={"link": '<https://api?page=2>; rel="next"'}
    )
    # Response for the second page: empty list, signaling the end of results
    resp2 = make_response(status=200, json_data=[])
    
    # Patch 'requests.get' to return the responses sequentially
    with patch("main.requests.get", side_effect=[resp1, resp2]) as mock_get:
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        
        # Assertions
        assert result == {"user1"}
        # Check that the API was called twice (once for each page)
        assert mock_get.call_count == 2

def test_get_github_users_auth_error_returns_none():
    """
    Tests error handling when authentication fails (HTTP 401).
    
    The function should catch the error and return None to signal failure.
    """
    # Mock a 401 Unauthorized response
    resp = make_response(status=401, json_data={"message": "bad credentials"})
    with patch("main.requests.get", return_value=resp):
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        # Assert failure: function returns None
        assert result is None

def test_get_github_users_forbidden_returns_none():
    """
    Tests error handling when a rate limit or forbidden access (HTTP 403) occurs.
    
    This is critical for handling GitHub's rate limiting policies.
    """
    # Mock a 403 Forbidden response, including rate limit headers
    resp = make_response(
        status=403, 
        json_data={"message": "forbidden"}, 
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "12345"}
    )
    with patch("main.requests.get", return_value=resp):
        result = main.get_github_users("https://api.github.com/some/url", "fake-token", "followers")
        # Assert failure: function returns None
        assert result is None

def test_write_results_txt_and_csv(tmp_path):
    """
    Tests the functions responsible for writing output files.
    
    Verifies that both text and CSV files are created correctly with the expected content.
    'tmp_path' is a pytest fixture for creating temporary directories and files.
    """
    non_followers = {"alice", "charlie"} # Users followed by the target who don't follow back
    fans = {"bob"}                       # Users who follow the target but are not followed back
    txt_file = tmp_path / "out.txt"
    csv_file = tmp_path / "out.csv"

    # --- Test TXT writing ---
    main.write_results_txt(non_followers, fans, str(txt_file))
    assert txt_file.exists()
    content = txt_file.read_text(encoding="utf-8")
    # Check if all expected usernames are present in the text file content
    assert "alice" in content and "bob" in content and "charlie" in content

    # --- Test CSV writing ---
    main.write_results_csv(non_followers, fans, str(csv_file))
    assert csv_file.exists()
    
    # Quick check for CSV structure and content
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        # Ensure a header row indicating the purpose of the data exists
        assert any("Users you follow who DO NOT follow you back" in row[0] for row in reader if row), "CSV header missing"

def test_compare_github_relationships_outputs_and_writes(tmp_path, capsys):
    """
    Tests the main comparison and output writing function.
    
    Verifies that the correct comparison logic is executed, results are printed 
    to stdout, and the output file is written as expected.
    'capsys' is a pytest fixture to capture stdout and stderr.
    """
    # Define the mock data for followers and following lists
    followers = {"a", "b"} # Users who follow the target
    following = {"b", "c"} # Users the target follows
    
    # Define the mock implementation for get_github_users
    def fake_get(url, token, label):
        # Return the appropriate set based on the URL/label being requested
        return followers if "followers" in url else following

    # Patch 'get_github_users' to return our predefined sets instead of making API calls
    with patch.object(main, "get_github_users", side_effect=fake_get):
        out_file = tmp_path / "results.txt"
        # Run the main comparison function
        main.compare_github_relationships(output_file=str(out_file), output_format="txt")
        
        # Capture stdout to check printed messages
        captured = capsys.readouterr()
        
        # Assertions on printed output
        assert "Total Followers: 2" in captured.out
        assert "Total Following: 2" in captured.out
        
        # Assertions on file output
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        # 'c' is in 'following' but not 'followers' (Non-follower)
        # 'a' is in 'followers' but not 'following' (Fan)
        assert "c" in content and "a" in content