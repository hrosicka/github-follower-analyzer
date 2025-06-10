import requests
import os

# --- Configuration ---
# Replace 'YOUR_GITHUB_USERNAME' with your actual GitHub username.
GITHUB_USERNAME = 'YOUR_GITHUB_USERNAME' 

# Replace 'YOUR_GITHUB_TOKEN' with your Personal Access Token.
# !!! IMPORTANT: NEVER UPLOAD THIS TOKEN TO A PUBLIC REPOSITORY! !!!
# For better security, consider loading the token from an environment variable
# or a separate configuration file that is not committed to version control.
# GITHUB_TOKEN = os.environ.get('GITHUB_PAT') # Example: If you use environment variable
# To set an environment variable:
# On Linux/macOS: export GITHUB_PAT='ghp_...'
# On Windows (Cmd): set GITHUB_PAT=ghp_...
# On Windows (PowerShell): $env:GITHUB_PAT='ghp_...'
GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN' 

# Base URL for the GitHub API.
BASE_URL = 'https://api.github.com'

# --- Function to Fetch GitHub Users ---
def get_github_users(url, token, user_type_label):
    """
    Fetches a list of GitHub users (either followers or following) from the API.
    Handles pagination to retrieve all users if there are more than 'per_page'.

    Args:
        url (str): The API endpoint URL (e.g., '.../followers' or '.../following').
        token (str): The GitHub Personal Access Token for authentication.
        user_type_label (str): A descriptive label for the type of users being fetched
                                (e.g., "followers" or "following") for print messages.

    Returns:
        set: A set of unique usernames (lowercase) if successful, None otherwise.
    """
    users = set()
    page = 1
    per_page = 100  # Max users per page allowed by GitHub API is 100.
    
    # Headers for API request, including Authorization for token and API version.
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json' # Recommended for GitHub API v3.
    }

    print(f"Fetching {user_type_label} list for user '{GITHUB_USERNAME}'...")

    while True:
        # Parameters for pagination.
        params = {'page': page, 'per_page': per_page}
        response = requests.get(url, headers=headers, params=params)
        
        # Check HTTP status code for response.
        if response.status_code == 200:
            page_users = response.json()
            if not page_users:
                break # No more users on this page, pagination complete.

            # Add usernames to the set, converting to lowercase for case-insensitive comparison.
            for user_data in page_users:
                users.add(user_data['login'].lower())
            
            # Check the 'Link' header to determine if there are more pages.
            # This is the standard way to handle pagination in GitHub API.
            if 'link' in response.headers:
                links = response.headers['link']
                if 'rel="next"' not in links:
                    break # 'next' link not found, indicating last page.
            else:
                break # No 'Link' header, assuming single page or implicit end.
            
            page += 1 # Move to the next page.

        elif response.status_code == 401:
            print(f"Authentication Error (401): Please check if your GitHub token is valid and has the correct 'read:user' permissions.")
            return None
        elif response.status_code == 403:
            print(f"Error (403 Forbidden) or Rate Limit Exceeded. Please try again later. "
                  f"Rate limit resets at: {response.headers.get('X-RateLimit-Reset')} (epoch time). "
                  f"Remaining requests: {response.headers.get('X-RateLimit-Remaining')}")
            return None
        else:
            print(f"An error occurred while fetching {user_type_label}. Status code: {response.status_code}, Response: {response.text}")
            return None
    
    return users

def compare_github_relationships():
    """
    Fetches the lists of followers and following from GitHub using the API
    and then compares them to identify non-followers and fans.
    """
    # Construct API URLs for fetching followers and following.
    followers_url = f'{BASE_URL}/users/{GITHUB_USERNAME}/followers'
    following_url = f'{BASE_URL}/users/{GITHUB_USERNAME}/following'

    # Fetch the list of followers.
    followers = get_github_users(followers_url, GITHUB_TOKEN, "followers")
    if followers is None:
        print("Failed to retrieve followers list. Script terminating.")
        return

    # Fetch the list of users being followed.
    following = get_github_users(following_url, GITHUB_TOKEN, "following")
    if following is None:
        print("Failed to retrieve following list. Script terminating.")
        return

    # --- Compare the Lists ---
    # Identify 'non-followers': Users you follow but who don't follow you back.
    # This is a set difference: elements in 'following' that are NOT in 'followers'.
    non_followers = following - followers

    # Identify 'fans': Users who follow you but you don't follow them back.
    # This is a set difference: elements in 'followers' that are NOT in 'following'.
    fans = followers - following

    print("\n--- Comparison Results ---")

    print(f"\nTotal Followers: {len(followers)}")
    print(f"Total Following: {len(following)}")

    if non_followers:
        print(f"\nUsers you follow who DO NOT follow you back ({len(non_followers)}):")
        for user in sorted(list(non_followers)):
            print(f"- {user}")
    else:
        print("\nGreat news! Everyone you follow on GitHub also follows you back.")

    if fans:
        print(f"\nUsers who FOLLOW YOU but you DO NOT follow back ({len(fans)}):")
        for user in sorted(list(fans)):
            print(f"- {user}")
    else:
        print("\nGreat news! You follow back all of your GitHub fans.")

    print("\n--- Done ---")

# --- Main Execution Block