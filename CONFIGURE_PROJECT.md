# Configure Project Fields - Step by Step

Since GitHub project fields require special API scopes, here's how to configure them:

## Quick Setup (If you have project scopes)

Run:
```bash
./configure_project_gh.sh bromso 17
```

Or:
```bash
python3 setup_project_fields.py bromso 17
```

## Get Token with Project Scopes

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `read:project` and `write:project`
4. Generate and copy the token

## Using the Token

Set it as an environment variable:
```bash
export GITHUB_TOKEN=your_token_here
./configure_project_gh.sh bromso 17
```

## Manual API Calls (Alternative)

If you want to add fields manually using curl:

### 1. Get Project ID

```bash
curl -X POST https://api.github.com/graphql \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { user(login: \"bromso\") { projectV2(number: 17) { id title } } }"
  }'
```

Save the `id` from the response.

### 2. Create Status Field

```bash
curl -X POST https://api.github.com/graphql \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { createProjectV2Field(input: { projectId: \"PROJECT_ID\", dataType: SINGLE_SELECT, name: \"Status\", singleSelectOptions: [{name: \"Icebox\"}, {name: \"Next Sprint\"}, {name: \"Current Sprint\"}, {name: \"Blocked\"}, {name: \"Test\"}, {name: \"Done\"}] }) { projectV2Field { ... on ProjectV2SingleSelectField { id name } } } }"
  }'
```

### 3. Continue for other fields

See `project_config.json` for all field definitions.

## After Fields are Added

1. Go to: https://github.com/users/bromso/projects/17
2. Click "New view" to create views manually
3. Configure views according to `project_config.json`

