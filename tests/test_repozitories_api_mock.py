"""
Unit tests for the 'repozitories.py' script.

This test file focuses on verifying the core functions that interact with the GitHub API:
1. get_following_users: Checks pagination and error handling.
2. get_user_details: Checks successful detail retrieval and error handling.

All tests utilize mocking (unittest.mock.patch) to simulate HTTP responses
and avoid making actual network calls.
"""
import pytest
import json
import sys
from unittest.mock import patch, MagicMock, ANY 
import requests # Import requests to mock its exceptions

# Add the parent directory to the path to import the module under test
sys.path.append('../github-follower-analyzer')
# Import the actual module (repozitories.py)
import repozitories

def make_mock_response(json_data, status=200, headers=None):
    """
    Helper function to create a MagicMock object that simulates a requests.Response.

    Configures the mock to return specific JSON data, status code, and headers
    upon calling its methods.
    
    :param json_data: The dictionary/list the .json() method should return.
    :param status: The HTTP status code to simulate.
    :param headers: Dictionary of HTTP response headers (e.g., for 'Link' header).
    :return: A configured MagicMock instance.
    """
    m = MagicMock()
    m.status_code = status
    m.json.return_value = json_data
    m.headers = headers or {}
    m.text = json.dumps(json_data)
    
    def raise_for_status_mock():
        """Simulates response.raise_for_status() behavior."""
        if status >= 400:
            http_error = requests.exceptions.HTTPError(f"Simulated HTTP {status} error")
            http_error.response = m
            raise http_error

    m.raise_for_status = MagicMock(side_effect=raise_for_status_mock)

    return m


# --- Tests for get_following_users ---

@patch.object(repozitories, "requests", autospec=True)
def test_get_following_users_single_page_success(mock_requests):
    """
    Tests successful retrieval of users when all data fits on a single API page.
    """
    # Arrange: Define sample user data
    sample_users = [{"login": "alice"}, {"login": "bob"}]
    # Create mock response without a 'Link' header
    mock_resp = make_mock_response(sample_users, status=200)
    mock_requests.get.return_value = mock_resp
    
    # Act
    result = repozitories.get_following_users("testuser", "fake-token")
    
    # Assert
    assert result == ["alice", "bob"]
    # Check that the API was called exactly once
    mock_requests.get.assert_called_once()
    

@patch.object(repozitories, "requests", autospec=True)
def test_get_following_users_pagination_success(mock_requests):
    """
    Tests correct handling of multi-page results using the 'Link' header for pagination.
    """
    # Arrange: Setup two responses for pagination
    
    # Response 1: Data for page 1, with a 'rel="next"' link header
    resp1_data = [{"login": "user1"}]
    resp1_headers = {"link": '<https://api.github.com/next?page=2>; rel="next"'}
    mock_resp1 = make_mock_response(resp1_data, headers=resp1_headers)
    
    # Response 2: Data for page 2, with no 'Link' header (end of data)
    resp2_data = [{"login": "user2"}]
    mock_resp2 = make_mock_response(resp2_data)
    
    # Configure the mock to return responses sequentially
    mock_requests.get.side_effect = [mock_resp1, mock_resp2]
    
    # Act
    result = repozitories.get_following_users("testuser", "fake-token")
    
    # Assert
    assert result == ["user1", "user2"]
    # Check that the API was called twice
    assert mock_requests.get.call_count == 2
    # Check the second call used page=2
    expected_url = f'{repozitories.BASE_URL}/users/testuser/following'
    # --- ZDE OPRAVENO: pytest.anything() nahrazeno za ANY ---
    mock_requests.get.assert_called_with(expected_url, headers=ANY, params={'page': 2, 'per_page': 100})


@patch.object(repozitories, "requests", autospec=True)
def test_get_following_users_api_error(mock_requests):
    """
    Tests error handling when the API returns an error status (e.g., 404 or 403).
    """
    # Arrange: Simulate an HTTP 404 Not Found error
    mock_resp_error = make_mock_response({"message": "Not Found"}, status=404)
    # Configure the mock to raise the exception when raise_for_status() is called
    mock_requests.get.return_value = mock_resp_error
    
    # Act
    result = repozitories.get_following_users("nonexistentuser", "fake-token")
    
    # Assert
    # The function should return None on failure
    assert result is None
    # Ensure the API call was attempted
    mock_requests.get.assert_called_once()


# --- Tests for get_user_details ---

@patch.object(repozitories, "requests", autospec=True)
def test_get_user_details_success(mock_requests):
    """
    Tests successful retrieval of detailed user information.
    """
    # Arrange: Sample details including the key 'public_repos'
    sample_details = {"login": "devuser", "public_repos": 5}
    mock_resp = make_mock_response(sample_details, status=200)
    mock_requests.get.return_value = mock_resp
    
    # Act
    result = repozitories.get_user_details("devuser", "fake-token")
    
    # Assert
    assert result == sample_details
    mock_requests.get.assert_called_once()


@patch.object(repozitories, "requests", autospec=True)
def test_get_user_details_api_error(mock_requests, capsys):
    """
    Tests error handling when fetching details fails. The function should 
    return None and print an error message.
    """
    # Arrange: Simulate a 500 Server Error
    mock_resp_error = make_mock_response({"message": "Server error"}, status=500)
    mock_requests.get.return_value = mock_resp_error
    
    # Act
    result = repozitories.get_user_details("problemuser", "fake-token")
    
    # Assert
    assert result is None
    # Check that an error message was printed to the console
    captured = capsys.readouterr()
    assert "Error fetching details for user 'problemuser'" in captured.out
