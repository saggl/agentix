# agentix

[Description of what agentix does - to be filled in]

## Installation

### Using uv (recommended)

```bash
uv pip install agentix-cli
```

### Using pip

```bash
pip install agentix-cli
```

## Usage

### If installed from PyPI

```bash
agentix
```

### If running from local development environment

When developing locally, the `agentix` command needs to be run from within the virtual environment:

```bash
# Option 1: Use uv run (recommended)
uv run agentix

# Option 2: Activate the virtual environment first
source .venv/bin/activate
agentix

# Option 3: Call the script directly
.venv/bin/agentix
```

## Development

```bash
# Clone the repository
git clone https://github.com/saggl/agentix.git
cd agentix

# Install in development mode
uv pip install -e .

# Run tests (when available)
uv run pytest
```

## License

MIT
