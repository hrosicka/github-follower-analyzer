import argparse
import requests
import os
import csv
import time

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

# Základní URL pro GitHub API.
BASE_URL = 'https://api.github.com'

# --- Funkce pro získání uživatelů ---
def get_following_users(token):
    """
    Získá seznam uživatelů, které sledujete, z GitHub API.
    """
    users = []
    page = 1
    per_page = 100
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    print(f"Načítám seznam uživatelů, které sleduje uživatel '{GITHUB_USERNAME}'...")

    while True:
        url = f'{BASE_URL}/users/{GITHUB_USERNAME}/following'
        params = {'page': page, 'per_page': per_page}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            page_users = response.json()
            if not page_users:
                break
            
            for user_data in page_users:
                users.append(user_data['login'])
            
            if 'link' in response.headers and 'rel="next"' in response.headers['link']:
                page += 1
            else:
                break
        else:
            print(f"Chyba při načítání seznamu. Status kód: {response.status_code}")
            return None
    
    return users

def get_user_details(username, token):
    """
    Získá detailní informace o uživateli, včetně počtu veřejných repozitářů.
    """
    url = f'{BASE_URL}/users/{username}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Chyba při načítání detailů pro uživatele '{username}'. Status kód: {response.status_code}")
        return None

def find_users_with_low_repos(output_file=None, output_format="txt"):
    """
    Najde uživatele, které sledujete a kteří mají 1 nebo méně repozitářů.
    """
    following_users = get_following_users(GITHUB_TOKEN)
    if following_users is None:
        return

    low_repo_users = []
    
    total_users = len(following_users)
    print(f"\nZahajuji kontrolu {total_users} uživatelů...")

    for i, user in enumerate(following_users, 1):
        try:
            user_details = get_user_details(user, GITHUB_TOKEN)
            if user_details and 'public_repos' in user_details:
                public_repos = user_details['public_repos']
                print(f"Kontrola {i}/{total_users}: Uživatel '{user}' má {public_repos} repozitářů.")
                if public_repos <= 1:
                    low_repo_users.append({'username': user, 'repos': public_repos})
            else:
                print(f"Přeskakuji uživatele '{user}' kvůli chybějícím datům.")
        except Exception as e:
            print(f"Chyba při zpracování uživatele '{user}': {e}")
        
        # Zpoždění, aby se zabránilo překročení limitu požadavků (rate limit).
        time.sleep(0.5) 

    print("\n--- Výsledky ---")
    if low_repo_users:
        print(f"Nalezeno {len(low_repo_users)} uživatelů, které sledujete a kteří mají 1 nebo méně repozitářů:")
        for user in sorted(low_repo_users, key=lambda x: x['username']):
            print(f"- {user['username']} ({user['repos']} repozitářů)")
    else:
        print("Všichni uživatelé, které sledujete, mají více než 1 repozitář.")
    
    # Export do souboru, pokud je zadáno
    if output_file:
        if output_format == "csv":
            write_low_repo_users_csv(low_repo_users, output_file)
        else:
            write_low_repo_users_txt(low_repo_users, output_file)
        print(f"\nVýsledky exportovány do '{output_file}' ve formátu {output_format.upper()}.")

def write_low_repo_users_txt(users, file_path):
    """Zapíše výsledky do textového souboru."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("--- Uživatelé s 1 nebo méně repozitáři ---\n\n")
        for user in sorted(users, key=lambda x: x['username']):
            f.write(f"- {user['username']} ({user['repos']} repozitářů)\n")
        f.write("\n--- Hotovo ---\n")

def write_low_repo_users_csv(users, file_path):
    """Zapíše výsledky do CSV souboru."""
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Public Repositories"])
        for user in sorted(users, key=lambda x: x['username']):
            writer.writerow([user['username'], user['repos']])

# --- Hlavní spouštěcí blok ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Najde uživatele, které sledujete a kteří mají málo repozitářů.")
    parser.add_argument("--output", type=str, help="Výstupní soubor pro uložení výsledků (např. results.txt nebo results.csv)")
    parser.add_argument("--format", type=str, choices=["txt", "csv"], default="txt", help="Formát výstupního souboru (txt nebo csv, výchozí: txt)")
    args = parser.parse_args()

    find_users_with_low_repos(output_file=args.output, output_format=args.format)