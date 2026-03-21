# agentix

**Unified CLI for Jira, Confluence, and Jenkins** — designed for both humans and AI agents.

agentix provides a consistent, JSON-first interface to Atlassian and Jenkins APIs, making it ideal for automation, scripting, and agentic workflows.

## Features

- 🔄 **Unified Interface**: Single CLI for Jira, Confluence, and Jenkins
- 📊 **JSON-First Output**: Default JSON format for easy parsing by agents and scripts
- 🔍 **Schema Introspection**: Machine-readable command metadata via `agentix schema`
- 🔐 **Modern Authentication**: Bearer token and API token support
- 📋 **Human-Friendly**: Optional table output format for terminal use
- ⚙️ **Multi-Profile**: Manage multiple environments (dev, staging, prod)
- 🧪 **Well-Tested**: Comprehensive test suite with 67+ tests

## Installation

### Using uv (recommended)

```bash
uv pip install agentix-cli
```

### Using pip

```bash
pip install agentix-cli
```

## Quick Start

### 1. Configure

Run the interactive setup wizard:

```bash
agentix config init
```

This will prompt you to configure:
- **Jira**: Base URL, email, API token
- **Confluence**: Base URL, email, API token (can reuse Jira credentials for Atlassian Cloud)
- **Jenkins**: Base URL, username, API token

Configuration is saved to `~/.config/agentix/config.toml`

### 2. Verify

```bash
agentix jira project list
agentix confluence space list
agentix jenkins job list
```

## Usage

### Jira

```bash
# List issues in a project
agentix jira issue list --project PROJ

# Get issue details
agentix jira issue get PROJ-123

# Create an issue
agentix jira issue create --project PROJ --summary "Fix bug" --type Bug

# Search with JQL
agentix jira search --jql "assignee = currentUser() AND status = 'In Progress'"

# List projects
agentix jira project list

# Manage sprints
agentix jira sprint list --board-id 123
agentix jira sprint get 456
```

### Confluence

```bash
# Get a page by ID
agentix confluence page get 123456

# Search for pages
agentix confluence page search --query "architecture" --space ENG

# Create a page
agentix confluence page create \
  --space-id 789 \
  --title "New Page" \
  --body "<p>Content here</p>"

# Update a page
agentix confluence page update 123456 \
  --title "Updated Title" \
  --body "<p>New content</p>"

# List spaces
agentix confluence space list
```

### Jenkins

```bash
# List jobs
agentix jenkins job list

# Get job details
agentix jenkins job get my-pipeline

# Trigger a build
agentix jenkins job build my-pipeline

# Build with parameters
agentix jenkins job build my-pipeline \
  -P ENVIRONMENT=staging \
  -P VERSION=1.2.3

# Wait for build to complete
agentix jenkins job build my-pipeline --wait --timeout 600

# Get build status
agentix jenkins build status my-pipeline

# Get build logs
agentix jenkins build logs my-pipeline --tail 50
```

### Output Formats

By default, agentix outputs JSON for easy parsing:

```bash
# JSON output (default)
agentix jira issue get PROJ-123

# Human-readable table
agentix --format table jira issue list --project PROJ
```

### Multiple Profiles

Manage multiple environments:

```bash
# Use a specific profile
agentix --profile staging jira issue list

# Set default profile
export AGENTIX_DEFAULT_PROFILE=staging
agentix jira issue list
```

## For AI Agents & Automation

### Schema Introspection

agentix provides machine-readable command metadata, enabling agents to discover and understand available commands programmatically:

```bash
# Get all top-level commands
agentix schema

# Get Jira subcommands
agentix schema jira

# Get specific command details (arguments, options, types)
agentix schema jira issue get

# Get full nested command tree
agentix schema --full jira
```

**Example schema output:**

```json
{
  "command": "agentix jira issue get",
  "description": "Get issue details.",
  "arguments": [
    {
      "name": "issue_key",
      "type": "string",
      "required": true,
      "multiple": false,
      "nargs": 1
    }
  ],
  "options": [],
  "subcommands": []
}
```

This makes agentix ideal for:
- 🤖 AI agents that need to discover capabilities
- 🔧 Dynamic CLI tool generation
- 📚 Automated documentation
- ✅ Integration testing

### Local Development

When developing locally, run commands via `uv`:

```bash
# Option 1: Use uv run (recommended)
uv run agentix jira issue list

# Option 2: Activate virtual environment first
source .venv/bin/activate
agentix jira issue list
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/saggl/agentix.git
cd agentix

# Install in development mode
uv pip install -e .

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/agentix --cov-report=html
```

### Project Structure

```
agentix/
├── src/agentix/          # Main package
│   ├── cli.py           # Root CLI entrypoint
│   ├── commands/        # Generic commands (schema)
│   ├── config/          # Configuration management
│   ├── core/            # Core utilities (auth, HTTP, output)
│   ├── jira/            # Jira integration
│   ├── confluence/      # Confluence integration
│   └── jenkins/         # Jenkins integration
├── tests/               # Test suite (67+ tests)
├── CLAUDE.md           # Development guidelines
└── pyproject.toml      # Package configuration
```

### Contributing

1. Create a feature branch
2. Make your changes
3. **Write tests** (required for new commands - see `CLAUDE.md`)
4. Run tests: `uv run pytest`
5. Create a pull request

See `CLAUDE.md` for detailed development guidelines.

## License

MIT
