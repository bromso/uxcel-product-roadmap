# Setup Instructions for GitHub Project Configuration

## Current Status

✅ Labels added to repository  
✅ Milestones added to repository  
⏳ Project fields and views - Requires authentication with project scopes

## Next Steps

### To Complete Project Configuration:

1. **Authenticate with Project Scopes**

   Run one of these commands to add the required scopes:

   ```bash
   gh auth refresh --scopes "read:project,write:project"
   ```

   Or if you need to re-authenticate:

   ```bash
   gh auth login --scopes "read:project,write:project"
   ```

2. **Run the Configuration Script**

   ```bash
   ./configure_project_gh.sh bromso 17
   ```

3. **Verify Configuration**

   - Go to https://github.com/users/bromso/projects/17
   - Check that all custom fields appear in the field list
   - Create views manually if needed (views are best created in UI)

## Manual View Creation

After fields are added, you can create the views manually in the GitHub UI:

1. Open your project: https://github.com/users/bromso/projects/17
2. Click "New view" or "Add view"
3. Select the view type (Board, Table, or Timeline)
4. Configure the view according to the specifications in `project_config.json`

### View Specifications:

- **Scrum Board**: Board view, group by Status, show specified fields
- **Current Sprint**: Board view, filter by Sprint = current
- **Backlog**: Table view, filter by Status in [Icebox, Next Sprint]
- **Epics Roadmap**: Timeline view, group by Stage, filter by Work Item Type = Epic
- **Kanban (All Work)**: Board view, group by Status
- **Table (All)**: Table view, show all fields

## What's Already Done

- ✅ 16 labels created in the repository
- ✅ 6 milestones created with due dates
- ✅ Configuration files prepared for project setup

## Troubleshooting

If you encounter scope errors:

1. Check your token scopes: `gh auth status`
2. Ensure you have `read:project` and `write:project` scopes
3. Refresh your token with: `gh auth refresh --scopes "read:project,write:project"`

If fields aren't being created:

1. Check that the project number is correct (17)
2. Verify you have write access to the project
3. Check the error messages in the script output

