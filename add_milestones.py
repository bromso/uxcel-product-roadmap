#!/usr/bin/env python3
"""
Script to add milestones to a GitHub repository.
Usage: python3 add_milestones.py [owner] [repo] [github_token]
Example: python3 add_milestones.py bromso uxcel-product-roadmap YOUR_GITHUB_TOKEN
Or set GITHUB_TOKEN environment variable
"""

import sys
import os
import json
import urllib.parse

# Check if requests is available, otherwise use urllib
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    USE_REQUESTS = False

# Milestones to create
MILESTONES = [
    {
        "title": "Discovery",
        "description": "Problem validation, value prop, v1 scope, instrumentation plan",
        "due_on": "2025-11-14T23:59:59Z"
    },
    {
        "title": "MVP/Alpha",
        "description": "Core collaboration primitives; internal dogfood",
        "due_on": "2025-12-05T23:59:59Z"
    },
    {
        "title": "Private Beta",
        "description": "Invite-only; analytics + feedback live",
        "due_on": "2026-01-09T23:59:59Z"
    },
    {
        "title": "Public Beta",
        "description": "Self-serve signup, pricing experiment, scale validation",
        "due_on": "2026-02-07T23:59:59Z"
    },
    {
        "title": "GA",
        "description": "Hardening, billing, support ops, SLAs",
        "due_on": "2026-03-07T23:59:59Z"
    },
    {
        "title": "Post-GA Growth",
        "description": "Expansion features, retention levers, integrations",
        "due_on": "2026-04-18T23:59:59Z"
    }
]

def create_milestone_requests(owner, repo, milestone, token):
    """Create a milestone using the requests library."""
    url = f"https://api.github.com/repos/{owner}/{repo}/milestones"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=milestone)
    return response

def create_milestone_urllib(owner, repo, milestone, token):
    """Create a milestone using urllib."""
    url = f"https://api.github.com/repos/{owner}/{repo}/milestones"
    data = json.dumps(milestone).encode('utf-8')
    
    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as response:
            return type('Response', (), {
                'status_code': response.getcode(),
                'text': response.read().decode('utf-8'),
                'json': lambda: json.loads(response.read().decode('utf-8'))
            })()
    except urllib.error.HTTPError as e:
        return type('Response', (), {
            'status_code': e.code,
            'text': e.read().decode('utf-8') if hasattr(e, 'read') else str(e),
            'json': lambda: {}
        })()

def create_or_update_milestone(owner, repo, milestone, token):
    """Create or update a milestone in the repository."""
    title = milestone["title"]
    
    if USE_REQUESTS:
        response = create_milestone_requests(owner, repo, milestone, token)
    else:
        response = create_milestone_urllib(owner, repo, milestone, token)
    
    if response.status_code == 201:
        print(f"✓ Created milestone: {title}")
        return True
    elif response.status_code == 422:
        # Milestone might already exist, try to update it
        # First, get existing milestones to find the number
        if USE_REQUESTS:
            list_url = f"https://api.github.com/repos/{owner}/{repo}/milestones"
            list_headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
            list_response = requests.get(list_url, headers=list_headers)
            if list_response.status_code == 200:
                existing = [m for m in list_response.json() if m["title"] == title]
                if existing:
                    milestone_num = existing[0]["number"]
                    update_url = f"https://api.github.com/repos/{owner}/{repo}/milestones/{milestone_num}"
                    update_response = requests.patch(update_url, headers=list_headers, json=milestone)
                    if update_response.status_code == 200:
                        print(f"✓ Updated milestone: {title}")
                        return True
        
        print(f"✗ Failed to create milestone: {title} (already exists or invalid)")
        return False
    else:
        print(f"✗ Failed to create milestone: {title} (HTTP {response.status_code})")
        try:
            error_text = response.text if hasattr(response, 'text') else str(response)
            print(f"  Response: {error_text}")
        except:
            pass
        return False

def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else "bromso"
    repo = sys.argv[2] if len(sys.argv) > 2 else "uxcel-product-roadmap"
    token = sys.argv[3] if len(sys.argv) > 3 else os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("Error: GitHub token is required.")
        print(f"Usage: {sys.argv[0]} [owner] [repo] [github_token]")
        print("Or set GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    print(f"Adding milestones to {owner}/{repo}...")
    print()
    
    success_count = 0
    for milestone in MILESTONES:
        if create_or_update_milestone(owner, repo, milestone, token):
            success_count += 1
    
    print()
    print(f"Done! Successfully processed {success_count}/{len(MILESTONES)} milestones.")

if __name__ == "__main__":
    main()

