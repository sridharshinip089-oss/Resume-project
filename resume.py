#!/usr/bin/env python3
"""
Upload a local project folder to GitHub.

Requirements:
1. Install Git: https://git-scm.com/downloads
2. Install GitHub CLI: https://cli.github.com/
3. Run `gh auth login` once before using this script.
4. Save this script in your project root and run: python upload_to_github.py
"""

import shutil
import subprocess
import sys
from pathlib import Path


GITIGNORE_CONTENT = """# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
.venv/
venv/
env/

# Secrets and local configuration
.env
.env.*
!.env.example

# Uploaded user files and generated data
uploads/
*.pdf
*.doc
*.docx

# Editors / operating system
.vscode/
.idea/
.DS_Store
Thumbs.db
"""


def run(command, cwd, check=True):
    """Run a command and show its output."""
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}"
        )
    return result


def main():
    project_dir = Path(__file__).resolve().parent

    # Check required command-line tools.
    for tool in ("git", "gh"):
        if shutil.which(tool) is None:
            print(f"ERROR: '{tool}' is not installed or not in PATH.")
            if tool == "gh":
                print("Install GitHub CLI from https://cli.github.com/")
            else:
                print("Install Git from https://git-scm.com/downloads")
            sys.exit(1)

    # Confirm GitHub CLI login.
    auth = run(["gh", "auth", "status"], project_dir, check=False)
    if auth.returncode != 0:
        print("\nPlease sign in first by running: gh auth login")
        sys.exit(1)

    # Create a safe default .gitignore only if one does not exist.
    gitignore = project_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(GITIGNORE_CONTENT, encoding="utf-8")
        print("Created .gitignore to exclude virtual environments,")
        print("uploaded resumes, and local secret files.")

    # Initialize Git if this folder is not already a repository.
    if not (project_dir / ".git").exists():
        run(["git", "init"], project_dir)

    # Use main as the branch name.
    run(["git", "branch", "-M", "main"], project_dir)

    # Stage project files and create a commit if there are changes.
    run(["git", "add", "-A"], project_dir)
    status = run(
        ["git", "status", "--porcelain"],
        project_dir,
        check=False
    )

    if status.stdout.strip():
        run(
            ["git", "commit", "-m", "Initial project upload"],
            project_dir
        )
    else:
        print("No new changes to commit.")

    # If a remote already exists, push to it.
    remote = run(
        ["git", "remote", "get-url", "origin"],
        project_dir,
        check=False
    )

    if remote.returncode == 0:
        print(f"\nExisting GitHub remote: {remote.stdout.strip()}")
        run(["git", "push", "-u", "origin", "main"], project_dir)
    else:
        repo_name = input(
            "\nEnter the GitHub repository name "
            "(example: ResumeAI): "
        ).strip()

        if not repo_name:
            print("Repository name cannot be empty.")
            sys.exit(1)

        visibility = input("Make repository public or private? [private]: ")
        visibility = visibility.strip().lower() or "private"
        if visibility not in ("public", "private"):
            print("Choose either 'public' or 'private'.")
            sys.exit(1)

        # gh creates the GitHub repository, adds origin, and pushes the code.
        command = [
            "gh", "repo", "create", repo_name,
            f"--{visibility}",
            "--source=.",
            "--remote=origin",
            "--push"
        ]
        run(command, project_dir)

    print("\nSUCCESS! Your project has been uploaded to GitHub.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"\nERROR: {error}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nUpload cancelled.")
        sys.exit(1)
