#!/bin/bash

# Script to add milestones to a GitHub repository
# Usage: ./add_milestones.sh [owner] [repo] [github_token]
# Example: ./add_milestones.sh bromso uxcel-product-roadmap YOUR_GITHUB_TOKEN

OWNER=${1:-bromso}
REPO=${2:-uxcel-product-roadmap}
GITHUB_TOKEN=${3:-${GITHUB_TOKEN}}

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token is required."
    echo "Usage: $0 [owner] [repo] [github_token]"
    echo "Or set GITHUB_TOKEN environment variable"
    exit 1
fi

# Milestones to create
MILESTONES='[
  {"title":"Discovery","description":"Problem validation, value prop, v1 scope, instrumentation plan","due_on":"2025-11-14T23:59:59Z"},
  {"title":"MVP/Alpha","description":"Core collaboration primitives; internal dogfood","due_on":"2025-12-05T23:59:59Z"},
  {"title":"Private Beta","description":"Invite-only; analytics + feedback live","due_on":"2026-01-09T23:59:59Z"},
  {"title":"Public Beta","description":"Self-serve signup, pricing experiment, scale validation","due_on":"2026-02-07T23:59:59Z"},
  {"title":"GA","description":"Hardening, billing, support ops, SLAs","due_on":"2026-03-07T23:59:59Z"},
  {"title":"Post-GA Growth","description":"Expansion features, retention levers, integrations","due_on":"2026-04-18T23:59:59Z"}
]'

echo "Adding milestones to $OWNER/$REPO..."
echo ""

# Read milestones from JSON and create each one
echo "$MILESTONES" | jq -r '.[] | @json' | while read -r milestone; do
    title=$(echo "$milestone" | jq -r '.title')
    description=$(echo "$milestone" | jq -r '.description // ""')
    due_on=$(echo "$milestone" | jq -r '.due_on // ""')
    
    echo "Creating milestone: $title"
    
    # Prepare the JSON payload
    if [ -z "$description" ] || [ "$description" == "null" ]; then
        if [ -z "$due_on" ] || [ "$due_on" == "null" ]; then
            payload=$(jq -n --arg title "$title" '{title: $title}')
        else
            payload=$(jq -n --arg title "$title" --arg due_on "$due_on" '{title: $title, due_on: $due_on}')
        fi
    else
        if [ -z "$due_on" ] || [ "$due_on" == "null" ]; then
            payload=$(jq -n --arg title "$title" --arg desc "$description" '{title: $title, description: $desc}')
        else
            payload=$(jq -n --arg title "$title" --arg desc "$description" --arg due_on "$due_on" '{title: $title, description: $desc, due_on: $due_on}')
        fi
    fi
    
    # Create the milestone
    response=$(curl -s -w "\n%{http_code}" \
        -X POST "https://api.github.com/repos/$OWNER/$REPO/milestones" \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 201 ]; then
        echo "✓ Created milestone: $title"
    elif [ "$http_code" -eq 422 ]; then
        # Milestone might already exist, try to find and update it
        echo "  Milestone $title might already exist, checking..."
        
        # Get existing milestones
        existing_response=$(curl -s -w "\n%{http_code}" \
            -X GET "https://api.github.com/repos/$OWNER/$REPO/milestones?state=all" \
            -H "Authorization: Bearer $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json")
        
        existing_code=$(echo "$existing_response" | tail -n1)
        existing_body=$(echo "$existing_response" | sed '$d')
        
        if [ "$existing_code" -eq 200 ]; then
            milestone_num=$(echo "$existing_body" | jq -r ".[] | select(.title == \"$title\") | .number" | head -1)
            
            if [ -n "$milestone_num" ]; then
                echo "  Found existing milestone #$milestone_num, updating..."
                update_response=$(curl -s -w "\n%{http_code}" \
                    -X PATCH "https://api.github.com/repos/$OWNER/$REPO/milestones/$milestone_num" \
                    -H "Authorization: Bearer $GITHUB_TOKEN" \
                    -H "Accept: application/vnd.github+json" \
                    -H "Content-Type: application/json" \
                    -d "$payload")
                update_code=$(echo "$update_response" | tail -n1)
                if [ "$update_code" -eq 200 ]; then
                    echo "✓ Updated milestone: $title"
                else
                    echo "✗ Failed to update milestone: $title (HTTP $update_code)"
                fi
            else
                echo "✗ Failed to create milestone: $title (already exists but couldn't find it)"
            fi
        else
            echo "✗ Failed to create milestone: $title (could not check existing milestones)"
        fi
    else
        echo "✗ Failed to create milestone: $title (HTTP $http_code)"
        echo "  Response: $body"
    fi
    echo ""
done

echo "Done!"

