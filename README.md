# GitHub Project Configuration

This directory contains scripts and configuration to set up the GitHub project with custom fields and views.

## Setup

### 1. Authenticate with Proper Scopes

The GitHub token needs `read:project` and `write:project` scopes to configure projects via API.

#### Option A: Using GitHub CLI

1. Re-authenticate GitHub CLI with project scopes:
   ```bash
   gh auth login --scopes "read:project,write:project"
   ```

2. Or refresh your existing token:
   ```bash
   gh auth refresh --scopes "read:project,write:project"
   ```

#### Option B: Using Personal Access Token

1. Go to https://github.com/settings/tokens
2. Create a new token or edit an existing one
3. Select scopes: `read:project` and `write:project`
4. Save the token and use it with the scripts:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

### 2. Run the Configuration Script

Once authenticated with proper scopes:

```bash
./configure_project_gh.sh bromso 17
```

Or with Python script:
```bash
python3 configure_project.py bromso 17 "$GITHUB_TOKEN"
```

## Manual Configuration (Alternative)

If you prefer to configure the project manually through the GitHub UI:

1. Go to your project: https://github.com/users/bromso/projects/17
2. Click on the settings/gear icon
3. Add custom fields as specified in `project_config.json`
4. Create views as needed

## Files

- `project_config.json` - Complete project configuration with fields and views
- `configure_project_gh.sh` - Bash script using GitHub CLI (recommended)
- `configure_project.py` - Python script using GraphQL API
- `add_labels.sh` - Script to add labels to repository
- `add_milestones.sh` - Script to add milestones to repository

## Project Fields

The configuration includes the following custom fields:

- **Status** (single-select): Icebox, Next Sprint, Current Sprint, Blocked, Test, Done
- **Work Item Type** (single-select): Epic, Story, Task, Bug, Spike, Chore
- **Sprint** (iteration): 2-week sprints starting Monday
- **Priority** (single-select): High, Medium, Low
- **Stage** (single-select): Discovery, Alpha, Private Beta, Public Beta, GA, Post-GA
- **Risk** (single-select): High, Medium, Low
- **Estimate** (number)
- **Story Points** (number)
- **Epic Link** (text)
- **Depends On** (text)
- **OKR** (text)
- **Start Date** (date)
- **Due Date** (date)

## Views

The configuration includes 6 views:

1. **Scrum Board** - Board view grouped by Status
2. **Current Sprint** - Board view filtered to current sprint
3. **Backlog** - Table view of Icebox and Next Sprint items
4. **Epics Roadmap** - Timeline view of Epics grouped by Stage
5. **Kanban (All Work)** - Board view of all work items
6. **Table (All)** - Complete table view of all items

