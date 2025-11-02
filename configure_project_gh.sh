#!/bin/bash

# Script to configure GitHub project using GitHub CLI
# Usage: ./configure_project_gh.sh [owner] [project_number]

OWNER=${1:-bromso}
PROJECT_NUMBER=${2:-17}

echo "Configuring project #${PROJECT_NUMBER} for ${OWNER}..."
echo ""

# Get project ID using GraphQL
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
    echo "Failed to get project ID. Make sure:"
    echo "  1. GitHub CLI is authenticated (gh auth login)"
    echo "  2. You have access to the project"
    echo "  3. The project number is correct"
    exit 1
fi

echo "Found project: ${PROJECT_TITLE} (ID: ${PROJECT_ID})"
echo ""

# Load config
CONFIG_FILE="project_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found"
    exit 1
fi

echo "Adding custom fields..."
echo ""

# Process each field from the config
jq -c '.project.fields[]' "$CONFIG_FILE" | while read -r field; do
    FIELD_NAME=$(echo "$field" | jq -r '.name')
    FIELD_TYPE=$(echo "$field" | jq -r '.type')
    
    echo "Creating field: ${FIELD_NAME} (${FIELD_TYPE})"
    
    if [ "$FIELD_TYPE" == "single-select" ]; then
        OPTIONS=$(echo "$field" | jq -c '.options // []')
        OPTIONS_JSON=$(echo "$OPTIONS" | jq -c 'map({name: .})')
        
        QUERY="mutation {
          createProjectV2Field(input: {
            projectId: \"${PROJECT_ID}\"
            dataType: SINGLE_SELECT
            name: \"${FIELD_NAME}\"
            singleSelectOptions: ${OPTIONS_JSON}
          }) {
            projectV2Field {
              ... on ProjectV2SingleSelectField {
                id
                name
              }
            }
          }
        }"
        
        RESULT=$(gh api graphql -f query="$QUERY" 2>&1)
        
        if echo "$RESULT" | jq -e '.errors' > /dev/null 2>&1; then
            ERROR_MSG=$(echo "$RESULT" | jq -r '.errors[0].message // .errors[0].type // "Unknown error"')
            if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"duplicate"* ]]; then
                echo "  ⚠ Field '${FIELD_NAME}' may already exist"
            else
                echo "  ✗ Error: ${ERROR_MSG}"
            fi
        else
            echo "  ✓ Created field: ${FIELD_NAME}"
        fi
        
    elif [ "$FIELD_TYPE" == "iteration" ]; then
        DURATION=$(echo "$field" | jq -r '.config.duration_weeks // 2')
        START_DAY=$(echo "$field" | jq -r '.config.start_day_of_week // "MON"')
        
        # Map day names to GraphQL enum values
        case "$START_DAY" in
            "Mon"|"MON"|"Monday") START_DAY_ENUM="MONDAY" ;;
            "Tue"|"TUE"|"Tuesday") START_DAY_ENUM="TUESDAY" ;;
            "Wed"|"WED"|"Wednesday") START_DAY_ENUM="WEDNESDAY" ;;
            "Thu"|"THU"|"Thursday") START_DAY_ENUM="THURSDAY" ;;
            "Fri"|"FRI"|"Friday") START_DAY_ENUM="FRIDAY" ;;
            "Sat"|"SAT"|"Saturday") START_DAY_ENUM="SATURDAY" ;;
            "Sun"|"SUN"|"Sunday") START_DAY_ENUM="SUNDAY" ;;
            *) START_DAY_ENUM="MONDAY" ;;
        esac
        
        QUERY="mutation {
          createProjectV2Field(input: {
            projectId: \"${PROJECT_ID}\"
            dataType: ITERATION
            name: \"${FIELD_NAME}\"
            iterationConfig: {
              duration: ${DURATION}
              startDay: ${START_DAY_ENUM}
            }
          }) {
            projectV2Field {
              ... on ProjectV2IterationField {
                id
                name
              }
            }
          }
        }"
        
        RESULT=$(gh api graphql -f query="$QUERY" 2>&1)
        
        if echo "$RESULT" | jq -e '.errors' > /dev/null 2>&1; then
            ERROR_MSG=$(echo "$RESULT" | jq -r '.errors[0].message // .errors[0].type // "Unknown error"')
            if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"duplicate"* ]]; then
                echo "  ⚠ Field '${FIELD_NAME}' may already exist"
            else
                echo "  ✗ Error: ${ERROR_MSG}"
            fi
        else
            echo "  ✓ Created field: ${FIELD_NAME}"
        fi
        
    elif [ "$FIELD_TYPE" == "number" ]; then
        QUERY="mutation {
          createProjectV2Field(input: {
            projectId: \"${PROJECT_ID}\"
            dataType: NUMBER
            name: \"${FIELD_NAME}\"
          }) {
            projectV2Field {
              ... on ProjectV2Field {
                id
                name
              }
            }
          }
        }"
        
        RESULT=$(gh api graphql -f query="$QUERY" 2>&1)
        
        if echo "$RESULT" | jq -e '.errors' > /dev/null 2>&1; then
            ERROR_MSG=$(echo "$RESULT" | jq -r '.errors[0].message // .errors[0].type // "Unknown error"')
            if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"duplicate"* ]]; then
                echo "  ⚠ Field '${FIELD_NAME}' may already exist"
            else
                echo "  ✗ Error: ${ERROR_MSG}"
            fi
        else
            echo "  ✓ Created field: ${FIELD_NAME}"
        fi
        
    elif [ "$FIELD_TYPE" == "text" ]; then
        QUERY="mutation {
          createProjectV2Field(input: {
            projectId: \"${PROJECT_ID}\"
            dataType: TEXT
            name: \"${FIELD_NAME}\"
          }) {
            projectV2Field {
              ... on ProjectV2Field {
                id
                name
              }
            }
          }
        }"
        
        RESULT=$(gh api graphql -f query="$QUERY" 2>&1)
        
        if echo "$RESULT" | jq -e '.errors' > /dev/null 2>&1; then
            ERROR_MSG=$(echo "$RESULT" | jq -r '.errors[0].message // .errors[0].type // "Unknown error"')
            if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"duplicate"* ]]; then
                echo "  ⚠ Field '${FIELD_NAME}' may already exist"
            else
                echo "  ✗ Error: ${ERROR_MSG}"
            fi
        else
            echo "  ✓ Created field: ${FIELD_NAME}"
        fi
        
    elif [ "$FIELD_TYPE" == "date" ]; then
        QUERY="mutation {
          createProjectV2Field(input: {
            projectId: \"${PROJECT_ID}\"
            dataType: DATE
            name: \"${FIELD_NAME}\"
          }) {
            projectV2Field {
              ... on ProjectV2Field {
                id
                name
              }
            }
          }
        }"
        
        RESULT=$(gh api graphql -f query="$QUERY" 2>&1)
        
        if echo "$RESULT" | jq -e '.errors' > /dev/null 2>&1; then
            ERROR_MSG=$(echo "$RESULT" | jq -r '.errors[0].message // .errors[0].type // "Unknown error"')
            if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"duplicate"* ]]; then
                echo "  ⚠ Field '${FIELD_NAME}' may already exist"
            else
                echo "  ✗ Error: ${ERROR_MSG}"
            fi
        else
            echo "  ✓ Created field: ${FIELD_NAME}"
        fi
    else
        echo "  ⚠ Unknown field type: ${FIELD_TYPE}"
    fi
    echo ""
done

echo ""
echo "Note: Views need to be created manually in the GitHub UI after fields are set up."
echo "The custom fields are now available in your project!"
echo ""
echo "Done!"

