#!/bin/bash

# Script to add labels to a GitHub repository
# Usage: ./add_labels.sh [owner] [repo] [github_token]
# Example: ./add_labels.sh bromso connect-the-dots YOUR_GITHUB_TOKEN

OWNER=${1:-bromso}
REPO=${2:-connect-the-dots}
GITHUB_TOKEN=${3:-${GITHUB_TOKEN}}

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token is required."
    echo "Usage: $0 [owner] [repo] [github_token]"
    echo "Or set GITHUB_TOKEN environment variable"
    exit 1
fi

# Labels to create
LABELS='[
  {"name":"priority:high","color":"b60205","description":"High impact/urgent"},
  {"name":"priority:medium","color":"d93f0b"},
  {"name":"priority:low","color":"fbca04"},
  {"name":"type:feature","color":"0e8a16"},
  {"name":"type:tech-debt","color":"5319e7"},
  {"name":"type:research","color":"c2e0c6"},
  {"name":"type:bug","color":"d73a4a"},
  {"name":"area:platform","color":"0052cc"},
  {"name":"area:collaboration","color":"1d76db"},
  {"name":"stage:discovery","color":"bfdadc"},
  {"name":"stage:alpha","color":"c5def5"},
  {"name":"stage:beta","color":"c7def8"},
  {"name":"stage:ga","color":"bfe5bf"},
  {"name":"risk:high","color":"8b0000"},
  {"name":"risk:medium","color":"ff8c00"},
  {"name":"risk:low","color":"ffd700"}
]'

echo "Adding labels to $OWNER/$REPO..."

# Read labels from JSON and create each one
echo "$LABELS" | jq -r '.[] | @json' | while read -r label; do
    name=$(echo "$label" | jq -r '.name')
    color=$(echo "$label" | jq -r '.color')
    description=$(echo "$label" | jq -r '.description // ""')
    
    # Remove '#' from color if present
    color=$(echo "$color" | tr -d '#')
    
    echo "Creating label: $name"
    
    # Prepare the JSON payload
    if [ -z "$description" ] || [ "$description" == "null" ]; then
        payload=$(jq -n --arg name "$name" --arg color "$color" '{name: $name, color: $color}')
    else
        payload=$(jq -n --arg name "$name" --arg color "$color" --arg desc "$description" '{name: $name, color: $color, description: $desc}')
    fi
    
    # Create or update the label
    response=$(curl -s -w "\n%{http_code}" \
        -X POST "https://api.github.com/repos/$OWNER/$REPO/labels" \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 201 ]; then
        echo "✓ Created label: $name"
    elif [ "$http_code" -eq 422 ]; then
        # Label already exists, try to update it
        echo "  Label $name already exists, updating..."
        update_response=$(curl -s -w "\n%{http_code}" \
            -X PATCH "https://api.github.com/repos/$OWNER/$REPO/labels/$(echo "$name" | sed 's/ /%20/g')" \
            -H "Authorization: Bearer $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "Content-Type: application/json" \
            -d "$payload")
        update_code=$(echo "$update_response" | tail -n1)
        if [ "$update_code" -eq 200 ]; then
            echo "✓ Updated label: $name"
        else
            echo "✗ Failed to update label: $name (HTTP $update_code)"
        fi
    else
        echo "✗ Failed to create label: $name (HTTP $http_code)"
        echo "  Response: $body"
    fi
done

echo ""
echo "Done!"

