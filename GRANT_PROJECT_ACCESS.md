# How to Grant Project Access to GitHub CLI

To configure GitHub projects, you need to grant the `project` scope to your GitHub CLI authentication. The `project` scope grants both read and write access to user and organization projects.

## Method 1: Refresh GitHub CLI Authentication (Recommended)

Run this command in your terminal:

```bash
gh auth refresh --scopes "project"
```

Or if you want to keep existing scopes and add project:

```bash
gh auth refresh --scopes "read:org,repo,project"
```

This will open your browser and ask you to authorize the additional permissions.

## Method 2: Re-authenticate GitHub CLI

If refresh doesn't work, re-authenticate completely:

```bash
gh auth login --scopes "project"
```

Follow the prompts:
1. Choose GitHub.com
2. Choose your preferred protocol (HTTPS recommended)
3. Authenticate via web browser
4. The `project` scope will be requested automatically

## Method 3: Create a Personal Access Token (Classic)

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Project Configuration")
4. Select these scopes:
   - ✅ `project` - Grants read and write access to projects
   - ✅ `repo` - For repository access (if not already selected)
5. Click "Generate token"
6. Copy the token immediately (you won't see it again!)

Then use it:
```bash
export GITHUB_TOKEN=your_token_here
gh auth login --with-token <<< "$GITHUB_TOKEN"
```

Or use it directly with the scripts:
```bash
export GITHUB_TOKEN=your_token_here
./configure_project_gh.sh bromso 17
```

## Verify Access

Check if you have the right scopes:

```bash
gh auth status
```

You should see `project` in the scopes list.

## After Granting Access

Once you have the correct scopes, run:

```bash
./configure_project_gh.sh bromso 17
```

This will add all the custom fields to your project!

