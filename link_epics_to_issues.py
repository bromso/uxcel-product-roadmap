#!/usr/bin/env python3
"""
Link child issues in project #17 to parent Epic issues in project #18.
Matches based on Epic Link field values.
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
    """Get all items from a project with their field values."""
    all_items = []
    cursor = None
    
    while True:
        query = f'''{{
          node(id: "{project_id}") {{
            ... on ProjectV2 {{
              items(first: 100{f', after: "{cursor}"' if cursor else ''}) {{
                nodes {{
                  id
                  content {{
                    ... on Issue {{
                      id
                      number
                      title
                    }}
                    ... on DraftIssue {{
                      id
                      title
                    }}
                  }}
                  fieldValues(first: 100) {{
                    nodes {{
                      ... on ProjectV2ItemFieldTextValue {{
                        field {{
                          ... on ProjectV2Field {{
                            id
                            name
                          }}
                        }}
                        text
                      }}
                      ... on ProjectV2ItemFieldSingleSelectValue {{
                        field {{
                          ... on ProjectV2SingleSelectField {{
                            id
                            name
                          }}
                        }}
                        name
                      }}
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
        items = data.get('data', {}).get('node', {}).get('items', {}).get('nodes', [])
        all_items.extend(items)
        
        page_info = data.get('data', {}).get('node', {}).get('items', {}).get('pageInfo', {})
        if not page_info.get('hasNextPage'):
            break
        
        cursor = page_info.get('endCursor')
    
    return all_items

def get_field_id(project_id, field_name):
    """Get field ID by name."""
    query = f'''{{
      node(id: "{project_id}") {{
        ... on ProjectV2 {{
          fields(first: 100) {{
            nodes {{
              ... on ProjectV2Field {{
                id
                name
              }}
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
        return None
    
    data = json.loads(result.stdout)
    fields = data.get('data', {}).get('node', {}).get('fields', {}).get('nodes', [])
    
    for field in fields:
        if field.get('name') == field_name:
            return field.get('id')
    return None

def extract_epic_link(item):
    """Extract Epic Link value from item field values."""
    field_values = item.get('fieldValues', {}).get('nodes', [])
    for fv in field_values:
        field = fv.get('field', {})
        if field.get('name') == 'Epic Link':
            return fv.get('text', '')
    return None

def normalize_epic_title(title):
    """Normalize epic title for matching."""
    # Remove "EPIC: " prefix if present
    title = re.sub(r'^EPIC:\s*', '', title, flags=re.IGNORECASE)
    return title.strip()

def update_parent_issue_direct(project_id, item_id, parent_item_id, parent_field_id):
    """Update the Parent issue field using parent's project item ID directly."""
    # Try different formats - GitHub API might accept the item ID string directly
    # First try: using issueId field (parent issue node ID might be needed)
    # Actually, for PARENT_ISSUE, we need the parent's project item ID
    # But the value might just be the item ID string wrapped differently
    
    # Based on GitHub's API, PARENT_ISSUE field accepts an issueId (the issue node ID, not project item ID)
    # So we need to get the issue ID from the parent item first
    
    # Get parent item's issue ID
    query = f'''{{
      node(id: "{parent_item_id}") {{
        ... on ProjectV2Item {{
          content {{
            ... on Issue {{
              id
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
        return False
    
    data = json.loads(result.stdout)
    parent_issue_id = data.get('data', {}).get('node', {}).get('content', {}).get('id')
    
    if not parent_issue_id:
        return False
    
    # Now update with the parent issue ID
    mutation = f'''mutation {{
      updateProjectV2ItemFieldValue(input: {{
        projectId: "{project_id}"
        itemId: "{item_id}"
        fieldId: "{parent_field_id}"
        value: {{
          issueId: "{parent_issue_id}"
        }}
      }}) {{
        projectV2Item {{
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
        if data.get('errors'):
            print(f"    Error: {json.dumps(data.get('errors'))}")
            return False
        return True
    
    # Print error for debugging
    try:
        data = json.loads(result.stdout)
        if data.get('errors'):
            error_msg = data.get('errors')[0].get('message', 'Unknown error')
            print(f"    Error: {error_msg}")
    except:
        print(f"    Error: {result.stderr[:200]}")
    
    return False

def update_parent_issue(project_id, item_id, parent_issue_id, parent_field_id):
    """Update the Parent issue field to link to parent epic."""
    # For PARENT_ISSUE field, we need to find the parent's project item ID in the same project
    # First, get the parent issue's project item ID in this project
    query = f'''{{
      node(id: "{project_id}") {{
        ... on ProjectV2 {{
          items(first: 100) {{
            nodes {{
              id
              content {{
                ... on Issue {{
                  id
                }}
              }}
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
        return False
    
    data = json.loads(result.stdout)
    items = data.get('data', {}).get('node', {}).get('items', {}).get('nodes', [])
    
    # Find parent's project item ID
    parent_item_id = None
    for item in items:
        if item.get('content', {}).get('id') == parent_issue_id:
            parent_item_id = item.get('id')
            break
    
    if not parent_item_id:
        # Parent not found in this project - can't link
        return False
    
    mutation = f'''mutation {{
      updateProjectV2ItemFieldValue(input: {{
        projectId: "{project_id}"
        itemId: "{item_id}"
        fieldId: "{parent_field_id}"
        value: {{
          parentId: "{parent_item_id}"
        }}
      }}) {{
        projectV2Item {{
          id
        }}
      }}
    }}'''
    
    result = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={mutation}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        # Try alternative format
        mutation = f'''mutation {{
          updateProjectV2ItemFieldValue(input: {{
            projectId: "{project_id}"
            itemId: "{item_id}"
            fieldId: "{parent_field_id}"
            value: {{
              itemId: "{parent_item_id}"
            }}
          }}) {{
            projectV2Item {{
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
        # Check for errors in response
        data = json.loads(result.stdout)
        if data.get('errors'):
            return False
        return True
    
    return False

def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else 'bromso'
    epics_project_num = sys.argv[2] if len(sys.argv) > 2 else '18'
    issues_project_num = sys.argv[3] if len(sys.argv) > 3 else '17'
    
    print(f"Linking child issues from project #{issues_project_num} to Epics in project #{epics_project_num}...")
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
    
    # Get Parent issue field ID
    parent_field_id = get_field_id(issues_project_id, 'Parent issue')
    if not parent_field_id:
        print("Could not find 'Parent issue' field in issues project")
        return
    
    print(f"Found 'Parent issue' field (ID: {parent_field_id})")
    print()
    
    # Get all Epics
    print("Fetching Epics from project #18...")
    epics = get_project_items(epics_project_id)
    print(f"Found {len(epics)} Epics")
    
    # Build Epic lookup: normalized title -> (item_id, issue_id)
    epic_lookup = {}
    epic_issues_to_add = []
    
    for epic in epics:
        content = epic.get('content', {})
        if not content:
            continue
        
        title = content.get('title', '')
        normalized = normalize_epic_title(title)
        epic_item_id = epic.get('id')
        epic_issue_id = content.get('id')  # This is the issue node ID
        
        if normalized:
            epic_lookup[normalized] = {
                'item_id': epic_item_id,
                'issue_id': epic_issue_id,
                'title': title
            }
            epic_issues_to_add.append(epic_issue_id)
    
    print(f"Built lookup for {len(epic_lookup)} Epics")
    
    # Add Epic issues to project #17 so they can be linked as parents
    print("Adding Epic issues to project #17...")
    epics_in_project17 = {}
    
    for epic_issue_id in epic_issues_to_add:
        # Check if already in project #17
        query = f'''{{
          node(id: "{issues_project_id}") {{
            ... on ProjectV2 {{
              items(first: 100) {{
                nodes {{
                  id
                  content {{
                    ... on Issue {{
                      id
                    }}
                  }}
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
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            items = data.get('data', {}).get('node', {}).get('items', {}).get('nodes', [])
            found = False
            for item in items:
                if item.get('content', {}).get('id') == epic_issue_id:
                    epics_in_project17[epic_issue_id] = item.get('id')
                    found = True
                    break
            
            if not found:
                # Add to project #17
                mutation = f'''mutation {{
                  addProjectV2ItemById(input: {{
                    projectId: "{issues_project_id}"
                    contentId: "{epic_issue_id}"
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
                    item_id = data.get('data', {}).get('addProjectV2ItemById', {}).get('item', {}).get('id')
                    if item_id:
                        epics_in_project17[epic_issue_id] = item_id
                        time.sleep(0.2)
    
    # Update epic lookup with project #17 item IDs
    for normalized, epic_info in epic_lookup.items():
        epic_issue_id = epic_info['issue_id']
        if epic_issue_id in epics_in_project17:
            epic_lookup[normalized]['project17_item_id'] = epics_in_project17[epic_issue_id]
    
    print(f"Epics ready in project #17: {len(epics_in_project17)}/{len(epic_lookup)}")
    print()
    
    # Get all child issues
    print("Fetching child issues from project #17...")
    issues = get_project_items(issues_project_id)
    print(f"Found {len(issues)} items")
    print()
    
    # Match and link
    linked_count = 0
    failed_count = 0
    
    for issue in issues:
        content = issue.get('content', {})
        if not content:
            continue
        
        issue_title = content.get('title', '')
        issue_item_id = issue.get('id')
        epic_link = extract_epic_link(issue)
        
        if not epic_link:
            continue
        
        # Normalize epic link for matching
        normalized_link = normalize_epic_title(epic_link)
        
        # Find matching epic
        if normalized_link in epic_lookup:
            epic_info = epic_lookup[normalized_link]
            parent_item_id = epic_info.get('project17_item_id')
            
            if not parent_item_id:
                print(f"⚠ Epic not in project #17: {issue_title}")
                print(f"  Epic: {epic_info['title']}")
                continue
            
            print(f"Linking: {issue_title}")
            print(f"  → Epic: {epic_info['title']}")
            
            if update_parent_issue_direct(issues_project_id, issue_item_id, parent_item_id, parent_field_id):
                print(f"  ✓ Linked successfully")
                linked_count += 1
            else:
                print(f"  ✗ Failed to link")
                failed_count += 1
        else:
            print(f"⚠ No matching Epic found for: {issue_title}")
            print(f"  Epic Link value: '{epic_link}' (normalized: '{normalized_link}')")
        
        time.sleep(0.2)  # Rate limiting
        print()
    
    print(f"Done! Linked {linked_count} issues, {failed_count} failed.")

if __name__ == '__main__':
    main()

