#!/usr/bin/env python3
"""
Script to configure a GitHub project with custom fields and views.
Uses GraphQL API to add fields and create views.
"""

import sys
import os
import json
import urllib.request
import urllib.error
import urllib.parse

def make_graphql_request(query, token):
    """Make a GraphQL request to GitHub API."""
    url = "https://api.github.com/graphql"
    data = json.dumps({"query": query}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {"errors": [{"message": error_body}], "data": None}

def get_project_id(owner_login, project_number, token):
    """Get the project ID from owner login and project number."""
    query = f"""
    {{
      user(login: "{owner_login}") {{
        projectV2(number: {project_number}) {{
          id
          title
        }}
      }}
    }}
    """
    result = make_graphql_request(query, token)
    
    if result.get("errors"):
        print(f"Error getting project: {result['errors']}")
        return None
    
    project = result.get("data", {}).get("user", {}).get("projectV2")
    if project:
        print(f"Found project: {project['title']} (ID: {project['id']})")
        return project['id']
    return None

def add_field_to_project(project_id, field_name, field_type, token, options=None, description=None, config=None):
    """Add a field to a project."""
    if field_type == "single-select":
        # Create single-select field
        options_str = json.dumps(options) if options else "[]"
        query = f"""
        mutation {{
          addProjectV2FieldById(input: {{
            projectId: "{project_id}"
            fieldId: "PVTF_lADOABrq9s4AAzU0zgCvGgk"
          }}) {{
            projectV2Field {{
              ... on ProjectV2SingleSelectField {{
                id
                name
              }}
            }}
          }}
        }}
        """
        # Actually, we need to create the field first
        query = f"""
        mutation {{
          createProjectV2Field(input: {{
            projectId: "{project_id}"
            dataType: SINGLE_SELECT
            name: "{field_name}"
            singleSelectOptions: {options_str}
          }}) {{
            projectV2Field {{
              ... on ProjectV2SingleSelectField {{
                id
                name
              }}
            }}
          }}
        }}
        """
    elif field_type == "iteration":
        # Create iteration field
        duration = config.get("duration_weeks", 2) if config else 2
        start_day = config.get("start_day_of_week", "MONDAY") if config else "MONDAY"
        query = f"""
        mutation {{
          createProjectV2Field(input: {{
            projectId: "{project_id}"
            dataType: ITERATION
            name: "{field_name}"
            iterationConfig: {{
              duration: {duration}
              startDay: {start_day}
            }}
          }}) {{
            projectV2Field {{
              ... on ProjectV2IterationField {{
                id
                name
              }}
            }}
          }}
        }}
        """
    elif field_type == "number":
        query = f"""
        mutation {{
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
        }}
        """
    elif field_type == "text":
        query = f"""
        mutation {{
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
        }}
        """
    elif field_type == "date":
        query = f"""
        mutation {{
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
        }}
        """
    else:
        print(f"Unknown field type: {field_type}")
        return None
    
    result = make_graphql_request(query, token)
    
    if result.get("errors"):
        error_msg = result['errors'][0].get('message', str(result['errors']))
        if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
            print(f"  Field '{field_name}' may already exist")
            return "exists"
        print(f"  Error creating field '{field_name}': {error_msg}")
        return None
    
    field_data = None
    if field_type == "single-select":
        field_data = result.get("data", {}).get("createProjectV2Field", {}).get("projectV2Field")
    elif field_type == "iteration":
        field_data = result.get("data", {}).get("createProjectV2Field", {}).get("projectV2Field")
    else:
        field_data = result.get("data", {}).get("createProjectV2Field", {}).get("projectV2Field")
    
    if field_data:
        print(f"✓ Created field: {field_name}")
        return field_data.get("id")
    return None

def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else "bromso"
    project_number = sys.argv[2] if len(sys.argv) > 2 else "17"
    token = sys.argv[3] if len(sys.argv) > 3 else os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("Error: GitHub token is required.")
        print(f"Usage: {sys.argv[0]} [owner] [project_number] [github_token]")
        print("Or set GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    # Load project config
    config_file = os.path.join(os.path.dirname(__file__), "project_config.json")
    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    project_config = config_data.get("project", {})
    
    print(f"Configuring project #{project_number} for {owner}...")
    print()
    
    # Get project ID
    project_id = get_project_id(owner, project_number, token)
    if not project_id:
        print("Failed to get project ID")
        sys.exit(1)
    
    print()
    print("Adding custom fields...")
    print()
    
    # Add fields
    fields = project_config.get("fields", [])
    for field in fields:
        field_name = field.get("name")
        field_type = field.get("type")
        options = field.get("options")
        description = field.get("description")
        config = field.get("config")
        
        # Map field types
        if field_type == "iteration":
            add_field_to_project(project_id, field_name, "iteration", token, options, description, config)
        elif field_type == "single-select":
            add_field_to_project(project_id, field_name, "single-select", token, options, description, config)
        elif field_type == "number":
            add_field_to_project(project_id, field_name, "number", token, options, description, config)
        elif field_type == "text":
            add_field_to_project(project_id, field_name, "text", token, options, description, config)
        elif field_type == "date":
            add_field_to_project(project_id, field_name, "date", token, options, description, config)
    
    print()
    print("Note: Views configuration requires manual setup in GitHub UI or additional GraphQL mutations.")
    print("The custom fields have been added and can now be used to create views manually.")
    print()
    print("Done!")

if __name__ == "__main__":
    main()

