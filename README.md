# GitHub Follower Analyzer

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)
[![GitHub API](https://img.shields.io/badge/GitHub%20API-v3-blueviolet)](https://docs.github.com/en/rest)
[![Last Commit](https://img.shields.io/github/last-commit/hrosicka/github-follower-analyzer)](https://github.com/hrosicka/github-follower-analyzer/commits/main)
[![Issues](https://img.shields.io/github/issues/hrosicka/github-follower-analyzer)](https://github.com/hrosicka/github-follower-analyzer/issues)
[![Stars](https://img.shields.io/github/stars/hrosicka/github-follower-analyzer?style=social)](https://github.com/hrosicka/github-follower-analyzer/stargazers)

A simple script to analyze your GitHub social graph: find out who you follow that doesn't follow you back, and who follows you that you don't follow back.

---

## Features

- **Analyzes your GitHub "followers" and "following" relationships**
- **Identifies:**
  - People you follow who do **not** follow you back ("non-followers")
  - People who follow you but you do **not** follow back ("fans")
- **Handles large accounts** (uses proper API pagination)
- **Clear command-line output**
- **Graceful error handling** for authentication and API rate limits
- **Optionally exports results to a file (TXT or CSV)**

---

## How It Works

This script fetches your followers and users you are following via the GitHub API, compares the two sets, and prints out:

- A list of users you follow who don't follow you back
- A list of users who follow you, but you don't follow back

You can also choose to export the results to a TXT or CSV file.

## Requirements

- Python 3.x
- `requests` module (`pip install requests`)
- GitHub Personal Access Token (with `read:user` permissions)

---

## Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/hrosicka/github-follower-analyzer.git
   cd github-follower-analyzer
   ```

2. **Install dependencies:**
   ```bash
   pip install requests
   ```

3. **Set up your credentials:**
   - Open `main.py`
   - Set your GitHub username:  
     ```python
     GITHUB_USERNAME = 'your-github-username'
     ```
   - Set your GitHub Personal Access Token:  
     ```python
     GITHUB_TOKEN = 'your-personal-access-token'
     ```
   - **Tip:** For better security, use an environment variable instead of hardcoding your token.
     Uncomment and use:
     ```python
     # GITHUB_TOKEN = os.environ.get('GITHUB_PAT')
     ```
     Then set `GITHUB_PAT` in your environment.

4. **(Optional) Configure environment variable:**
   - On Linux/macOS:
     ```bash
     export GITHUB_PAT='your-personal-access-token'
     ```
   - On Windows (Command Prompt):
     ```cmd
     set GITHUB_PAT=your-personal-access-token
     ```
   - On Windows (PowerShell):
     ```powershell
     $env:GITHUB_PAT='your-personal-access-token'
     ```

---

## Usage

Run the script:
```bash
python main.py
```

You will see output like:
```
--- Comparison Results ---

Total Followers: 42
Total Following: 30

Users you follow who DO NOT follow you back (3):
- user123
- user456
- user789

Users who FOLLOW YOU but you DO NOT follow back (1):
- fanuser

--- Done ---
```

---

### Exporting Results

You can now export the results to a TXT or CSV file:

- Export to TXT:  
  ```bash
  python main.py --output results.txt
  ```

- Export to CSV:  
  ```bash
  python main.py --output results.csv --format csv
  ```

Results will always be printed to the console by default. Providing arguments for exporting is optional; if omitted, the script behaves as before.

---

## Notes

- The script handles pagination to support accounts with many followers/followings.
- Authentication and rate limit errors are clearly reported.
- **Never commit your Personal Access Token to a public repository!**

---

## 👩‍💻 Author

Lovingly crafted by [Hanka Robovska](https://github.com/hrosicka) 👩‍🔬

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details. Free to use, modify, and distribute as needed.
