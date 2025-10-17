import argparse
import requests
import os
import csv
import time

# --- Configuration ---
# Retrieve the username from arguments or use a default (recommended: use arguments)
# For simplicity, a placeholder is still used here, but it should be replaced with the actual username.
# Ideally, you should load GITHUB_USERNAME from a command-line argument.
GITHUB_USERNAME = 'YOUR_GITHUB_USERNAME'

# !!! IMPORTANT SECURITY WARNING !!!
# The token is now hardcoded directly into the script. 
# Ensure this file is NEVER committed to a public repository!
# Replace 'YOUR_GITHUB_TOKEN' with your actual Personal Access Token.
GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN' 

# Base URL for the GitHub API.
BASE_URL = 'https://api.github.com'

# --- Functions for fetching users ---
def get_following_users(username, token):
    """
    Fetches the list of users that the authenticated user is following from the GitHub API.
    """
    if not token:
        print("ERROR: GitHub Personal Access Token is not available. Please set the GITHUB_TOKEN variable in the script.")
        return None
        
    users = []
    page = 1
    per_page = 100
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    print(f"Fetching the list of users followed by '{username}'...")

    while True:
        url = f'{BASE_URL}/users/{username}/following'
        params = {'page': page, 'per_page': per_page}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status() # Raises an exception for 4xx/5xx errors
        except Exception as e:
            print(f"Error communicating with API: {e}")
            return None
        
        page_users = response.json()
        if not page_users:
            break
        
        for user_data in page_users:
            users.append(user_data['login'])
        
        if 'link' in response.headers and 'rel="next"' in response.headers['link']:
            page += 1
        else:
            break
    
    return users

def get_user_details(username_to_check, token):
    """
    Fetches detailed user information, including the count of public repositories.
    """
    url = f'{BASE_URL}/users/{username_to_check}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Print error but do not stop the entire script run
        print(f"Error fetching details for user '{username_to_check}'. Error: {e}")
        return None

def find_users_with_low_repos(username, token, output_file=None, output_format="txt"):
    """
    Finds users that the authenticated user follows who have 2 or fewer repositories.
    """
    following_users = get_following_users(username, token)
    if following_users is None:
        return

    low_repo_users = []
    
    total_users = len(following_users)
    print(f"\nStarting check for {total_users} users...")

    for i, user in enumerate(following_users, 1):
        # Basic implementation to prevent hitting the Rate Limit
        time.sleep(0.5) 
        
        user_details = get_user_details(user, token)
        
        if user_details and 'public_repos' in user_details:
            public_repos = user_details['public_repos']
            print(f"Checking {i}/{total_users}: User '{user}' has {public_repos} repositories.")
            if public_repos <= 2:
                low_repo_users.append({'username': user, 'repos': public_repos})
        else:
            print(f"Skipping user '{user}' due to missing data or API error.")
        
    print("\n--- Results ---")
    if low_repo_users:
        print(f"Found {len(low_repo_users)} users you follow who have 2 or fewer repositories:")
        for user in sorted(low_repo_users, key=lambda x: x['username']):
            print(f"- {user['username']} ({user['repos']} repositories)")
    else:
        print("All users you follow have more than 2 repositories.")
    
    # Export to file if specified
    if output_file:
        if output_format == "csv":
            write_low_repo_users_csv(low_repo_users, output_file)
        else:
            write_low_repo_users_txt(low_repo_users, output_file)
        print(f"\nResults exported to '{output_file}' in {output_format.upper()} format.")

def write_low_repo_users_txt(users, file_path):
    """Writes the results to a text file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("--- Users with 2 or Fewer Repositories ---\n\n")
        for user in sorted(users, key=lambda x: x['username']):
            f.write(f"- {user['username']} ({user['repos']} repositories)\n")
        f.write("\n--- Done ---\n")

def write_low_repo_users_csv(users, file_path):
    """Writes the results to a CSV file."""
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Public Repositories"])
        for user in sorted(users, key=lambda x: x['username']):
            writer.writerow([user['username'], user['repos']])

# --- Main execution block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finds users you follow who have few repositories.")
    parser.add_argument("--username", type=str, default=GITHUB_USERNAME, help=f"Your GitHub username (default: {GITHUB_USERNAME})")
    parser.add_argument("--output", type=str, help="Output file to save the results (e.g., results.txt or results.csv)")
    parser.add_argument("--format", type=str, choices=["txt", "csv"], default="txt", help="Output file format (txt or csv, default: txt)")
    args = parser.parse_args()

    find_users_with_low_repos(
        username=args.username,
        token=GITHUB_TOKEN,
        output_file=args.output, 
        output_format=args.format
    )
