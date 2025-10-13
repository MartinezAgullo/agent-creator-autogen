# AI Agent Generator

Multi-agent system that creates and coordinates AI agents for defense and military strategic analysis using Microsoft AutoGen.

## What It Does

- **Generates** {HOW_MANY_AGENTS} **AI agents** with unique military specializations (cyber, intelligence, logistics, etc.)
- Agents autonomously develop **operational concepts and tactical solutions**
- **Collaborative refinement**: Agents randomly consult each other to improve analyses
- Outputs saved as markdown files (idea1.md, idea2.md, etc.)

## Quick Start

```bash
# Install dependencies
uv sync

# Run
uv run world.py

```

Key Files
---------

-   `world.py` - Orchestrates agent creation and execution
-   `creator.py` - Generates new specialized agents dynamically
-   `agent.py` - Base template for military analyst agents
-   `messages.py` - Agent communication protocol

Configuration
-------------

-   **Number of agents**: Edit `HOW_MANY_AGENTS` in `world.py`
-   **Specializations**: Modify `system_message` in `agent.py` and `creator.py`
-   **Collaboration rate**: Adjust `CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER` in `agent.py`
-   **Temperature**: Control creativity in model_client initialization

Requirements
------------

-   Python 3.10+
-   OpenAI API key in `.env`
-   AutoGen libraries

Security Note
-------------

⚠️ This system generates and executes code dynamically. Do not include classified information in prompts or system messages.