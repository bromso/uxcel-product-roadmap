#!/usr/bin/env python3
"""
Update issue fields in GitHub project from issues.jsonl data.
Updates: OKR, Story Points, Start Date, Due Date, and attempts Parent issue linking.
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

def get_project_items_with_fields(project_id):
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
                      ... on ProjectV2ItemFieldNumberValue {{
                        field {{
                          ... on ProjectV2Field {{
                            id
                            name
                          }}
                        }}
                        number
                      }}
                      ... on ProjectV2ItemFieldDateValue {{
                        field {{
                          ... on ProjectV2Field {{
                            id
                            name
                          }}
                        }}
                        date
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

def get_field_ids(project_id):
    """Get all field IDs from project."""
    query = f'''{{
      node(id: "{project_id}") {{
        ... on ProjectV2 {{
          fields(first: 100) {{
            nodes {{
              ... on ProjectV2Field {{
                id
                name
                dataType
              }}
              ... on ProjectV2SingleSelectField {{
                id
                name
                dataType
              }}
              ... on ProjectV2IterationField {{
                id
                name
                dataType
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
        return {}
    
    data = json.loads(result.stdout)
    fields = data.get('data', {}).get('node', {}).get('fields', {}).get('nodes', [])
    
    field_ids = {}
    for field in fields:
        field_ids[field.get('name')] = {
            'id': field.get('id'),
            'dataType': field.get('dataType')
        }
    
    return field_ids

def update_field_value(project_id, item_id, field_id, field_type, value):
    """Update a field value."""
    if value is None or value == "":
        return True  # Skip empty values
    
    # Build mutation based on field type
    if field_type == 'TEXT':
        mutation = f'''mutation {{
          updateProjectV2ItemFieldValue(input: {{
            projectId: "{project_id}"
            itemId: "{item_id}"
            fieldId: "{field_id}"
            value: {{
              text: "{value}"
            }}
          }}) {{
            projectV2Item {{
              id
            }}
          }}
        }}'''
    elif field_type == 'NUMBER':
        mutation = f'''mutation {{
          updateProjectV2ItemFieldValue(input: {{
            projectId: "{project_id}"
            itemId: "{item_id}"
            fieldId: "{field_id}"
            value: {{
              number: {value}
            }}
          }}) {{
            projectV2Item {{
              id
            }}
          }}
        }}'''
    elif field_type == 'DATE':
        mutation = f'''mutation {{
          updateProjectV2ItemFieldValue(input: {{
            projectId: "{project_id}"
            itemId: "{item_id}"
            fieldId: "{field_id}"
            value: {{
              date: "{value}"
            }}
          }}) {{
            projectV2Item {{
              id
            }}
          }}
        }}'''
    else:
        return False
    
    result = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={mutation}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if data.get('errors'):
            return False
        return True
    
    return False

def find_epic_item_id(project_id, epic_title):
    """Find epic's project item ID by title."""
    items = get_project_items_with_fields(project_id)
    
    for item in items:
        content = item.get('content', {})
        if not content:
            continue
        
        title = content.get('title', '')
        # Normalize comparison - remove "EPIC: " prefix if present
        normalized_title = re.sub(r'^EPIC:\s*', '', title, flags=re.IGNORECASE).strip()
        normalized_epic = re.sub(r'^EPIC:\s*', '', epic_title, flags=re.IGNORECASE).strip()
        
        if normalized_title == normalized_epic:
            return item.get('id'), content.get('id')  # project item ID, issue node ID
    
    return None, None

def update_parent_issue_field(project_id, item_id, parent_field_id, epic_issue_node_id):
    """Attempt to update Parent issue field. This may not work via API."""
    # Try with issue node ID directly in a text format (some APIs accept this)
    # First, try getting parent's project item ID
    parent_item_id, _ = find_epic_item_id(project_id, epic_issue_node_id)
    
    if not parent_item_id:
        return False
    
    # Try various formats - GitHub API limitations may prevent this
    # Attempt 1: As text with issue ID
    mutation = f'''mutation {{
      updateProjectV2ItemFieldValue(input: {{
        projectId: "{project_id}"
        itemId: "{item_id}"
        fieldId: "{parent_field_id}"
        value: {{
          text: "{epic_issue_node_id}"
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
    
    # This will likely fail, but we'll note it for manual linking
    return False  # API doesn't support this yet

def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else 'bromso'
    project_number = sys.argv[2] if len(sys.argv) > 2 else '17'
    
    print(f"Updating issue fields in project #{project_number} for {owner}...")
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
                issues_data[title] = issue
    
    print(f"Loaded {len(issues_data)} issues from {issues_file}")
    print()
    
    # Get project ID
    project_id, project_title = get_project_id(owner, project_number)
    if not project_id:
        print("Failed to get project ID")
        return
    
    print(f"Project: {project_title} (ID: {project_id})")
    print()
    
    # Get field IDs
    print("Getting field IDs...")
    field_ids = get_field_ids(project_id)
    
    required_fields = ['OKR', 'Story Points', 'Start Date', 'Due Date', 'Parent issue']
    missing_fields = [f for f in required_fields if f not in field_ids]
    if missing_fields:
        print(f"⚠ Warning: Missing fields: {', '.join(missing_fields)}")
        print("Available fields:", ', '.join(field_ids.keys()))
    
    print()
    
    # Note: Epics are in project #18, not #17. Parent issue field will need manual linking.
    
    # Get all project items
    print("Fetching project items...")
    items = get_project_items_with_fields(project_id)
    print(f"Found {len(items)} items in project")
    print()
    
    # Update fields for each matching issue
    updated_count = 0
    parent_manual_count = 0
    seen_titles = set()
    
    for item in items:
        content = item.get('content', {})
        if not content:
            continue
        
        title = content.get('title', '')
        item_id = item.get('id')
        
        # Skip EPIC items - they should not be in project #17
        if 'EPIC:' in title.upper():
            continue
        
        if title not in issues_data:
            continue
        
        # Skip duplicates
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        issue_data = issues_data[title]
        print(f"Updating: {title}")
        
        updates_made = False
        
        # Update OKR (if present in data)
        okr = issue_data.get('okr') or issue_data.get('OKR')
        if okr and okr != "" and 'OKR' in field_ids:
            field_id = field_ids['OKR']['id']
            field_type = field_ids['OKR']['dataType']
            if update_field_value(project_id, item_id, field_id, field_type, str(okr)):
                print(f"  ✓ OKR: {okr}")
                updates_made = True
            else:
                print(f"  ✗ Failed to update OKR")
        
        # Update Story Points (if present in data, or use estimate as fallback)
        story_points = issue_data.get('story_points') or issue_data.get('Story Points')
        if story_points is None:
            # Try estimate as fallback
            story_points = issue_data.get('estimate')
        if story_points is not None and 'Story Points' in field_ids:
            field_id = field_ids['Story Points']['id']
            field_type = field_ids['Story Points']['dataType']
            if update_field_value(project_id, item_id, field_id, field_type, int(story_points)):
                print(f"  ✓ Story Points: {story_points}")
                updates_made = True
            else:
                print(f"  ✗ Failed to update Story Points")
        
        # Update Start Date
        start_date = issue_data.get('start_date') or issue_data.get('Start Date')
        if start_date and 'Start Date' in field_ids:
            field_id = field_ids['Start Date']['id']
            field_type = field_ids['Start Date']['dataType']
            if update_field_value(project_id, item_id, field_id, field_type, start_date):
                print(f"  ✓ Start Date: {start_date}")
                updates_made = True
            else:
                print(f"  ✗ Failed to update Start Date")
        
        # Update Due Date (if present in data)
        due_date = issue_data.get('due_date') or issue_data.get('Due Date')
        if due_date and due_date != "" and 'Due Date' in field_ids:
            field_id = field_ids['Due Date']['id']
            field_type = field_ids['Due Date']['dataType']
            if update_field_value(project_id, item_id, field_id, field_type, due_date):
                print(f"  ✓ Due Date: {due_date}")
                updates_made = True
            else:
                print(f"  ✗ Failed to update Due Date")
        
        # Note about Parent issue: Epics are in project #18, Parent issue linking must be done manually
        epic_link = issue_data.get('epic_link') or issue_data.get('Epic Link')
        if epic_link and 'Parent issue' in field_ids:
            print(f"  ℹ Parent Epic: {epic_link}")
            print(f"    Note: Parent issue field must be set manually in GitHub UI")
            print(f"    Epic is in project #18 and needs to be linked manually")
            parent_manual_count += 1
        
        if updates_made:
            updated_count += 1
        
        time.sleep(0.2)  # Rate limiting
        print()
    
    print(f"Done! Updated {updated_count} issues.")
    if parent_manual_count > 0:
        print(f"{parent_manual_count} issues need Parent issue field set manually in GitHub UI.")

if __name__ == '__main__':
    main()
