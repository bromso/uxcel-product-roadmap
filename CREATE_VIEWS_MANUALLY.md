# How to Create Project Views Manually

Unfortunately, GitHub's Projects V2 API doesn't support creating views programmatically. Views need to be created manually in the GitHub UI. Here's a step-by-step guide to create all 6 views from your configuration.

## Quick Links
- **Your Project**: https://github.com/users/bromso/projects/17

## View 1: Scrum Board

1. Open your project and click **"New view"** or **"+"** button
2. Select **"Board"** view type
3. Name it: **"Scrum Board"**
4. In view settings:
   - **Group by**: Select "Status" field
   - **Visible fields**: Show these fields:
     - Work Item Type
     - Sprint
     - Priority
     - Story Points
     - Risk
     - Epic Link
     - Depends On
   - **Filters**: None (show all items)
5. Save the view

## View 2: Current Sprint

1. Click **"New view"** again
2. Select **"Board"** view type
3. Name it: **"Current Sprint"**
4. In view settings:
   - **Group by**: Select "Status" field
   - **Visible fields**: Show:
     - Work Item Type
     - Priority
     - Story Points
     - Risk
     - Epic Link
     - Depends On
   - **Filters**: 
     - Add filter: **Sprint** → **is** → **current**
5. Save the view

## View 3: Backlog

1. Click **"New view"**
2. Select **"Table"** view type
3. Name it: **"Backlog"**
4. In view settings:
   - **Visible columns**: Add these columns:
     - Status
     - Work Item Type
     - Priority
     - Stage
     - Story Points
     - Risk
     - Epic Link
     - Depends On
     - Start Date
     - Due Date
     - OKR
   - **Filters**: 
     - Add filter: **Status** → **is one of** → Select "Icebox" and "Next Sprint"
   - **Sort by**: 
     - Priority (Ascending)
     - Story Points (Ascending)
5. Save the view

## View 4: Epics Roadmap

1. Click **"New view"**
2. Select **"Timeline"** view type
3. Name it: **"Epics Roadmap"**
4. In view settings:
   - **Date field**: Select "Start Date"
   - **Group by**: Select "Stage" field
   - **Visible fields**: Show:
     - Status
     - Priority
     - Stage
     - Risk
     - OKR
     - Due Date
   - **Filters**: 
     - Add filter: **Work Item Type** → **is** → **Epic**
5. Save the view

## View 5: Kanban (All Work)

1. Click **"New view"**
2. Select **"Board"** view type
3. Name it: **"Kanban (All Work)"**
4. In view settings:
   - **Group by**: Select "Status" field
   - **Visible fields**: Show:
     - Work Item Type
     - Sprint
     - Priority
     - Stage
     - Risk
     - Epic Link
   - **Filters**: None (show all items)
5. Save the view

## View 6: Table (All)

1. Click **"New view"**
2. Select **"Table"** view type
3. Name it: **"Table (All)"**
4. In view settings:
   - **Visible columns**: Add all columns:
     - Status
     - Work Item Type
     - Sprint
     - Priority
     - Stage
     - Story Points
     - Risk
     - Epic Link
     - Depends On
     - Start Date
     - Due Date
     - OKR
   - **Filters**: None (show all items)
   - **Sort by**: (optional, as needed)
5. Save the view

## Tips

- You can reorder views by dragging them in the view tabs
- You can edit any view later by clicking the three-dot menu (⋯) next to the view name
- Views are saved automatically as you configure them
- Field visibility can be toggled by clicking the column/field headers

## Verification

After creating all views, you should see 7 total views (6 custom + 1 default "Product Roadmap").

All views are now ready to use with your custom fields!

