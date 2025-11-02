#!/usr/bin/env python3
"""
Script to add labels to a GitHub repository.
Usage: python3 add_labels.py [owner] [repo] [github_token]
Example: python3 add_labels.py bromso connect-the-dots YOUR_GITHUB_TOKEN
Or set GITHUB_TOKEN environment variable
"""

import sys
import os
import json
import requests
import urllib.parse

# Labels to create
LABELS = [
    {"name": "priority:high", "color": "b60205", "description": "High impact/urgent"},
    {"name": "priority:medium", "color": "d93f0b"},
    {"name": "priority:low", "color": "fbca04"},
    {"name": "type:feature", "color": "0e8a16"},
    {"name": "type:tech-debt", "color": "5319e7"},
    {"name": "type:research", "color": "c2e0c6"},
    {"name": "type:bug", "color": "d73a4a"},
    {"name": "area:platform", "color": "0052cc"},
    {"name": "area:collaboration", "color": "1d76db"},
    {"name": "stage:discovery", "color": "bfdadc"},
    {"name": "stage:alpha", "color": "c5def5"},
    {"name": "stage:beta", "color": "c7def8"},
    {"name": "stage:ga", "color": "bfe5bf"},
    {"name": "risk:high", "color": "8b0000"},
    {"name": "risk:medium", "color": "ff8c00"},
    {"name": "risk:low", "color": "ffd700"}
]

def create_or_update_label(owner, repo, label, token):
    """Create or update a label in the repository."""
    name = label["name"]
    color = label["color"].lstrip("#")  # Remove # if present
    description = label.get("description", "")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/labels"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "color": color
    }
    if description:
        payload["description"] = description
    
    # Try to create the label
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        print(f"✓ Created label: {name}")
        return True
    elif response.status_code == 422:
        # Label already exists, try to update it
        encoded_name = urllib.parse.quote(name, safe="")
        update_url = f"https://api.github.com/repos/{owner}/{repo}/labels/{encoded_name}"
        update_response = requests.patch(update_url, headers=headers, json=payload)
        
        if update_response.status_code == 200:
            print(f"✓ Updated label: {name}")
            return True
        else:
            print(f"✗ Failed to update label: {name} (HTTP {update_response.status_code})")
            print(f"  Response: {update_response.text}")
            return False
    else:
        print(f"✗ Failed to create label: {name} (HTTP {response.status_code})")
        print(f"  Response: {response.text}")
        return False

def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else "bromso"
    repo = sys.argv[2] if len(sys.argv) > 2 else "connect-the-dots"
    token = sys.argv[3] if len(sys.argv) > 3 else os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("Error: GitHub token is required.")
        print(f"Usage: {sys.argv[0]} [owner] [repo] [github_token]")
        print("Or set GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    print(f"Adding labels to {owner}/{repo}...")
    print()
    
    success_count = 0
    for label in LABELS:
        if create_or_update_label(owner, repo, label, token):
            success_count += 1
    
    print()
    print(f"Done! Successfully processed {success_count}/{len(LABELS)} labels.")

if __name__ == "__main__":
    main()

