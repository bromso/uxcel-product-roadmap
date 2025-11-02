#!/bin/bash

# Script to create views in a GitHub project
# Usage: ./create_project_views.sh [owner] [project_number]

OWNER=${1:-bromso}
PROJECT_NUMBER=${2:-17}

echo "Creating views for project #${PROJECT_NUMBER} for ${OWNER}..."
echo ""

# Get project ID
echo "Getting project information..."
PROJECT_INFO=$(gh api graphql -f query="{
  user(login: \"${OWNER}\") {
    projectV2(number: ${PROJECT_NUMBER}) {
      id
      title
    }
  }
}")

PROJECT_ID=$(echo "$PROJECT_INFO" | jq -r '.data.user.projectV2.id')
PROJECT_TITLE=$(echo "$PROJECT_INFO" | jq -r '.data.user.projectV2.title')

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "null" ]; then
    echo "Failed to get project ID"
    exit 1
fi

echo "Found project: ${PROJECT_TITLE} (ID: ${PROJECT_ID})"
echo ""

# Get all field IDs first
echo "Getting field IDs..."
FIELDS_INFO=$(gh api graphql -f query="{
  user(login: \"${OWNER}\") {
    projectV2(number: ${PROJECT_NUMBER}) {
      fields(first: 100) {
        nodes {
          ... on ProjectV2Field {
            id
            name
          }
          ... on ProjectV2SingleSelectField {
            id
            name
          }
          ... on ProjectV2IterationField {
            id
            name
          }
        }
      }
    }
  }
}")

# Store field IDs in a temp file for lookup
echo "$FIELDS_INFO" | jq -r '.data.user.projectV2.fields.nodes[] | "\(.name)|\(.id)"' > /tmp/project_fields.txt

get_field_id() {
    grep "^$1|" /tmp/project_fields.txt | cut -d'|' -f2
}

echo "Creating views..."
echo ""

# Load config
CONFIG_FILE="project_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found"
    exit 1
fi

# Create views
jq -c '.project.views[]' "$CONFIG_FILE" | while read -r view; do
    VIEW_NAME=$(echo "$view" | jq -r '.name')
    VIEW_TYPE=$(echo "$view" | jq -r '.type | ascii_upcase')
    GROUP_BY=$(echo "$view" | jq -r '.group_by // empty')
    
    echo "Creating view: ${VIEW_NAME} (${VIEW_TYPE})"
    
    # Map view type to GraphQL enum
    case "$VIEW_TYPE" in
        "BOARD") VIEW_ENUM="BOARD" ;;
        "TABLE") VIEW_ENUM="TABLE" ;;
        "TIMELINE") VIEW_ENUM="TIMELINE" ;;
        *) VIEW_ENUM="TABLE" ;;
    esac
    
    # Get groupBy field ID if specified
    GROUP_BY_ID=""
    if [ -n "$GROUP_BY" ] && [ "$GROUP_BY" != "null" ]; then
        GROUP_BY_ID=$(get_field_id "$GROUP_BY")
    fi
    
    # Build the mutation - start with basic view creation
    if [ -n "$GROUP_BY_ID" ]; then
        # For board views with grouping
        QUERY="mutation {
          createProjectV2View(input: {
            projectId: \"${PROJECT_ID}\"
            name: \"${VIEW_NAME}\"
            viewType: ${VIEW_ENUM}
            groupByFields: [\"${GROUP_BY_ID}\"]
          }) {
            projectV2View {
              id
              name
            }
          }
        }"
    else
        # Simple view without grouping
        QUERY="mutation {
          createProjectV2View(input: {
            projectId: \"${PROJECT_ID}\"
            name: \"${VIEW_NAME}\"
            viewType: ${VIEW_ENUM}
          }) {
            projectV2View {
              id
              name
            }
          }
        }"
    fi
    
    RESULT=$(gh api graphql -f query="$QUERY" 2>&1)
    
    if echo "$RESULT" | jq -e '.errors' > /dev/null 2>&1; then
        ERROR_MSG=$(echo "$RESULT" | jq -r '.errors[0].message // .errors[0].type // "Unknown error"')
        if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"duplicate"* ]]; then
            echo "  ⚠ View '${VIEW_NAME}' may already exist"
        else
            echo "  ✗ Error: ${ERROR_MSG}"
        fi
    else
        VIEW_ID=$(echo "$RESULT" | jq -r '.data.createProjectV2View.projectV2View.id // empty')
        if [ -n "$VIEW_ID" ] && [ "$VIEW_ID" != "null" ]; then
            echo "  ✓ Created view: ${VIEW_NAME} (ID: ${VIEW_ID})"
            
            # Note: Filters and field visibility would need additional API calls
            # GitHub's API for view configuration is limited, some settings may need manual setup
        else
            echo "  ✓ Created view: ${VIEW_NAME}"
        fi
    fi
    echo ""
done

# Cleanup
rm -f /tmp/project_fields.txt

echo "Done!"
echo ""
echo "Note: View filters and field visibility settings may need to be configured manually"
echo "in the GitHub UI, as the API has limited support for these features."

