# MCP server for Copilot Studio agents

## Overview

This repository contains a Model Context Protocol (MCP) server that allows you to connect to an agent built using the Copilot Studio from the MCP clients (Claude, Github Copilot Chat)

## Requirements
- Python 3.12
- `uv` installed

```sh
 uv venv
 source .venv/bin/activate
 uv sync
```

### Dev setup

Test it with the MCP Inspector

```
cd src
mcp dev main.py
```

### Code Quality

This project uses [Ruff](https://github.com/charliermarsh/ruff) for code formatting and linting.

#### Installation

Install development dependencies (including Ruff):

```sh
uv pip install -e ".[dev]"
```

#### Usage

To format your code:

```sh
ruff format .
```

To check your code for style issues:

```sh
ruff check .
```

The configuration for Ruff can be found in the `pyproject.toml` file.