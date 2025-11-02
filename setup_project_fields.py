#!/usr/bin/env python3
"""
Configure GitHub project fields using GraphQL API
Uses MCP or environment authentication
"""

import json
import os
import sys
import subprocess

def get_auth_token():
    """Get GitHub token from MCP or environment."""
    # Try to get token from gh CLI
    try:
        result = subprocess.run(['gh', 'auth', 'token'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        pass
    
    # Try environment variable
    return os.getenv('GITHUB_TOKEN')

def make_graphql_request(query, token):
    """Make GraphQL request using gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'api', 'graphql', '-f', f'query={query}'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {'errors': [{'message': e.stderr}]}
    except json.JSONDecodeError:
        return {'errors': [{'message': 'Invalid JSON response'}]}

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
    
    result = make_graphql_request(query, None)
    
    if result.get('errors'):
        print(f"Error getting project: {result['errors']}")
        return None
    
    project = result.get('data', {}).get('user', {}).get('projectV2')
    if project:
        print(f"Found project: {project['title']} (ID: {project['id']})")
        return project['id']
    return None

def create_field(project_id, field_config):
    """Create a field in the project."""
    field_name = field_config['name']
    field_type = field_config['type']
    
    print(f"Creating field: {field_name} ({field_type})")
    
    if field_type == 'single-select':
        options = field_config.get('options', [])
        options_json = json.dumps([{'name': opt} for opt in options])
        
        query = f'''mutation {{
          createProjectV2Field(input: {{
            projectId: "{project_id}"
            dataType: SINGLE_SELECT
            name: "{field_name}"
            singleSelectOptions: {options_json}
          }}) {{
            projectV2Field {{
              ... on ProjectV2SingleSelectField {{
                id
                name
              }}
            }}
          }}
        }}'''
        
    elif field_type == 'iteration':
        config = field_config.get('config', {})
        duration = config.get('duration_weeks', 2)
        start_day = config.get('start_day_of_week', 'Mon').upper()
        
        day_map = {
            'MON': 'MONDAY', 'TUE': 'TUESDAY', 'WED': 'WEDNESDAY',
            'THU': 'THURSDAY', 'FRI': 'FRIDAY', 'SAT': 'SATURDAY', 'SUN': 'SUNDAY'
        }
        start_day_enum = day_map.get(start_day[:3], 'MONDAY')
        
        query = f'''mutation {{
          createProjectV2Field(input: {{
            projectId: "{project_id}"
            dataType: ITERATION
            name: "{field_name}"
            iterationConfig: {{
              duration: {duration}
              startDay: {start_day_enum}
            }}
          }}) {{
            projectV2Field {{
              ... on ProjectV2IterationField {{
                id
                name
              }}
            }}
          }}
        }}'''
        
    elif field_type == 'number':
        query = f'''mutation {{
          createProjectV2Field(input: {{
            projectId: "{project_id}"
            dataType: NUMBER
            name: "{field_name}"
          }}) {{
            projectV2Field {{
              ... on ProjectV2Field {{
                id
                name
              }}
            }}
          }}
        }}'''
        
    elif field_type == 'text':
        query = f'''mutation {{
          createProjectV2Field(input: {{
            projectId: "{project_id}"
            dataType: TEXT
            name: "{field_name}"
          }}) {{
            projectV2Field {{
              ... on ProjectV2Field {{
                id
                name
              }}
            }}
          }}
        }}'''
        
    elif field_type == 'date':
        query = f'''mutation {{
          createProjectV2Field(input: {{
            projectId: "{project_id}"
            dataType: DATE
            name: "{field_name}"
          }}) {{
            projectV2Field {{
              ... on ProjectV2Field {{
                id
                name
              }}
            }}
          }}
        }}'''
        
    else:
        print(f"  ⚠ Unknown field type: {field_type}")
        return False
    
    result = make_graphql_request(query, None)
    
    if result.get('errors'):
        error_msg = result['errors'][0].get('message', str(result['errors']))
        if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
            print(f"  ⚠ Field '{field_name}' may already exist")
            return True
        print(f"  ✗ Error: {error_msg}")
        return False
    
    field_data = result.get('data', {}).get('createProjectV2Field', {}).get('projectV2Field')
    if field_data:
        print(f"  ✓ Created field: {field_name}")
        return True
    return False

def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else 'bromso'
    project_number = sys.argv[2] if len(sys.argv) > 2 else '17'
    
    # Load config
    config_file = 'project_config.json'
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    project_config = config_data.get('project', {})
    
    print(f"Configuring project #{project_number} for {owner}...")
    print()
    
    # Get project ID
    project_id = get_project_id(owner, project_number)
    if not project_id:
        print("Failed to get project ID")
        sys.exit(1)
    
    print()
    print("Adding custom fields...")
    print()
    
    # Create fields
    fields = project_config.get('fields', [])
    success_count = 0
    
    for field in fields:
        if create_field(project_id, field):
            success_count += 1
        print()
    
    print(f"Done! Successfully created {success_count}/{len(fields)} fields.")
    print()
    print("Note: Views need to be created manually in the GitHub UI.")
    print("All custom fields are now available in your project!")

if __name__ == '__main__':
    main()

