#!/usr/bin/env python3
"""
Link child issues from project #17 as sub-issues to their parent Epics in project #18.
Updates Epic issue descriptions with task lists to create the parent-child relationship.
"""

import json
import sys
import subprocess
import time
import re

def get_project_id(owner, project_number):
    """Get project ID."""
    query = f'''{{
      user(login: "{owner}") {{
        projectV2(number: {project_number}) {{
          id
          title
        }}
      }}
    }}'''
    
    result = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={query}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None, None
    
    data = json.loads(result.stdout)
    project = data.get('data', {}).get('user', {}).get('projectV2', {})
    return project.get('id'), project.get('title')

def get_project_items(project_id):
    """Get all items from a project."""
    all_items = []
    cursor = None
    has_next_page = True
    
    while has_next_page:
        after_clause = f', after: "{cursor}"' if cursor else ''
        query = f'''{{
          node(id: "{project_id}") {{
            ... on ProjectV2 {{
              items(first: 100{after_clause}) {{
                nodes {{
                  id
                  content {{
                    ... on Issue {{
                      id
                      number
                      title
                    }}
                  }}
                }}
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
              }}
            }}
          }}
        }}'''
        
        result = subprocess.run(
            ['gh', 'api', 'graphql', '-f', f'query={query}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            break
        
        data = json.loads(result.stdout)
        node = data.get('data', {}).get('node', {})
        items_data = node.get('items', {})
        items = items_data.get('nodes', [])
        all_items.extend(items)
        
        page_info = items_data.get('pageInfo', {})
        has_next_page = page_info.get('hasNextPage', False)
        cursor = page_info.get('endCursor')
    
    return all_items

def normalize_epic_title(title):
    """Normalize epic title for matching."""
    return re.sub(r'^EPIC:\s*', '', title, flags=re.IGNORECASE).strip()

def add_item_to_project(project_id, issue_node_id):
    """Add an issue to a project."""
    mutation = f'''mutation {{
      addProjectV2ItemById(input: {{
        projectId: "{project_id}"
        contentId: "{issue_node_id}"
      }}) {{
        item {{
          id
        }}
      }}
    }}'''
    
    result = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={mutation}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return data.get('data', {}).get('addProjectV2ItemById', {}).get('item', {}).get('id')
    return None

def get_issue_body(owner, repo, issue_number):
    """Get issue body."""
    query = f'''{{
      repository(owner: "{owner}", name: "{repo}") {{
        issue(number: {issue_number}) {{
          id
          body
        }}
      }}
    }}'''
    
    result = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={query}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        issue = data.get('data', {}).get('repository', {}).get('issue', {})
        return issue.get('body', '') or ''
    return None

def update_issue_body(owner, repo, issue_number, new_body):
    """Update issue body."""
    # Use REST API to update issue
    result = subprocess.run(
        ['gh', 'api', f'repos/{owner}/{repo}/issues/{issue_number}', '-X', 'PATCH', '-f', f'body={new_body}'],
        capture_output=True,
        text=True
    )
    
    return result.returncode == 0

def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else 'bromso'
    repo = sys.argv[2] if len(sys.argv) > 2 else 'uxcel-product-roadmap'
    epics_project_num = sys.argv[3] if len(sys.argv) > 3 else '18'
    issues_project_num = sys.argv[4] if len(sys.argv) > 4 else '17'
    
    print(f"Linking sub-issues from project #{issues_project_num} to Epics in project #{epics_project_num}...")
    print()
    
    # Get project IDs
    epics_project_id, epics_project_title = get_project_id(owner, epics_project_num)
    issues_project_id, issues_project_title = get_project_id(owner, issues_project_num)
    
    if not epics_project_id or not issues_project_id:
        print("Failed to get project IDs")
        return
    
    print(f"Epics project: {epics_project_title} (ID: {epics_project_id})")
    print(f"Issues project: {issues_project_title} (ID: {issues_project_id})")
    print()
    
    # Load issues data
    issues_file = 'issues.jsonl'
    issues_data = {}
    
    with open(issues_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                issue = json.loads(line)
                title = issue.get('title', '')
                # Only process non-Epic issues
                if 'EPIC:' not in title.upper():
                    issues_data[title] = issue
    
    print(f"Loaded {len(issues_data)} child issues from {issues_file}")
    print()
    
    # Get all Epics from project #18
    print("Fetching Epics from project #18...")
    epics = get_project_items(epics_project_id)
    epic_lookup = {}
    
    for epic in epics:
        content = epic.get('content', {})
        if not content:
            continue
        
        title = content.get('title', '')
        if 'EPIC:' in title.upper():
            normalized = normalize_epic_title(title)
            epic_lookup[normalized] = {
                'item_id': epic.get('id'),
                'issue_id': content.get('id'),
                'issue_number': content.get('number'),
                'title': title
            }
    
    print(f"Found {len(epic_lookup)} Epics")
    print()
    
    # Get all items from project #17 (child issues)
    print("Fetching child issues from project #17...")
    child_items = get_project_items(issues_project_id)
    child_issues = {}
    
    for item in child_items:
        content = item.get('content', {})
        if not content:
            continue
        
        title = content.get('title', '')
        # Skip Epics
        if 'EPIC:' in title.upper():
            continue
        
        child_issues[title] = {
            'item_id': item.get('id'),
            'issue_id': content.get('id'),
            'issue_number': content.get('number'),
            'title': title
        }
    
    print(f"Found {len(child_issues)} child issues in project #17")
    print()
    
    # Build mapping: Epic -> list of child issues
    epic_to_children = {}
    
    for child_title, child_info in child_issues.items():
        if child_title in issues_data:
            issue_data = issues_data[child_title]
            epic_link = issue_data.get('epic_link') or issue_data.get('Epic Link')
            
            if epic_link:
                normalized_link = normalize_epic_title(epic_link)
                if normalized_link in epic_lookup:
                    if normalized_link not in epic_to_children:
                        epic_to_children[normalized_link] = []
                    epic_to_children[normalized_link].append({
                        'title': child_title,
                        'issue_id': child_info['issue_id'],
                        'issue_number': child_info['issue_number']
                    })
    
    print(f"Built mapping for {len(epic_to_children)} Epics with sub-issues")
    print()
    
    # Get existing items in project #18
    existing_items = get_project_items(epics_project_id)
    existing_issue_ids = {item.get('content', {}).get('id') for item in existing_items if item.get('content', {}).get('id')}
    
    # For each Epic, add child issues to project #18 and update Epic description with task list
    print("Processing Epics and their sub-issues...")
    print()
    
    total_added = 0
    total_updated = 0
    
    for epic_title, epic_info in epic_lookup.items():
        if epic_title not in epic_to_children:
            continue
        
        children = epic_to_children[epic_title]
        print(f"Epic: {epic_info['title']}")
        print(f"  {len(children)} sub-issues")
        
        epic_issue_number = epic_info['issue_number']
        
        # Add children to project #18 if not already there
        task_list_items = []
        for child in children:
            child_issue_id = child['issue_id']
            child_issue_number = child['issue_number']
            
            # Check if child is already in project #18
            if child_issue_id not in existing_issue_ids:
                child_project_item_id = add_item_to_project(epics_project_id, child_issue_id)
                if child_project_item_id:
                    print(f"  ✓ Added issue #{child_issue_number} to project #18")
                    total_added += 1
                    time.sleep(0.3)
                    # Update existing_issue_ids for next iteration
                    existing_issue_ids.add(child_issue_id)
            
            # Add to task list
            task_list_items.append(f"- [ ] #{child_issue_number}")
        
        # Get current Epic body
        epic_body = get_issue_body(owner, repo, epic_issue_number)
        if epic_body is None:
            print(f"  ⚠ Could not get Epic body, skipping update")
            continue
        
        # Check if task list already exists
        if "## Sub-issues" in epic_body or "## Sub-Issues" in epic_body:
            print(f"  ℹ Epic already has sub-issues section, skipping update")
            print()
            continue
        
        # Append task list to Epic body
        task_list_section = "\n\n## Sub-issues\n\n" + "\n".join(task_list_items)
        new_body = epic_body + task_list_section
        
        # Update Epic issue body
        if update_issue_body(owner, repo, epic_issue_number, new_body):
            print(f"  ✓ Updated Epic description with {len(task_list_items)} sub-issues")
            total_updated += 1
        else:
            print(f"  ✗ Failed to update Epic description")
        
        print()
        time.sleep(0.3)
    
    print(f"Done!")
    print(f"Added {total_added} child issues to project #18")
    print(f"Updated {total_updated} Epic descriptions with task lists")
    print()
    print("Sub-issues are now linked via task lists in Epic descriptions!")

if __name__ == '__main__':
    main()

