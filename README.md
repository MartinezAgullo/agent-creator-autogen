# AI Agent Generator for Defense Analysis

Multi-agent system that dynamically creates and coordinates AI agents for defense and military strategic analysis using Microsoft AutoGen. Agents autonomously develop operational concepts, tactical solutions, and collaborate to refine analyses.

## Features

- **Dynamic Agent Generation**: Creates specialized AI agents with unique military domains (cyber warfare, intelligence, logistics, naval strategy, etc.)
- **Autonomous Collaboration**: Agents consult each other to refine and improve strategic analyses
- **Sandboxed Execution**: All agent code runs in isolated Docker containers with security hardening
- **Structured Outputs**: Analysis results saved as markdown files in `./assessments/`

## Architecture

The system uses a multi-layered security approach:
- **Container Isolation**: Docker with read-only filesystem and resource limits
- **User Isolation**: Non-root execution (UID 1000)
- **Filesystem Protection**: Code base mounted read-only, writable tmpfs for runtime
- **Resource Constraints**: 2GB RAM, 2 CPUs, 128 process limit
- **Network Access**: Restricted to OpenAI API only

## Prerequisites

- Docker Desktop (macOS ARM64)
- OpenAI API key
- Python 3.10+ (for local development)

## Quick Start

1. **Configure environment**:
   ```bash
   # Edit .env and add your OpenAI API key
   ```

2. **Verify setup**:
   ```bash
   chmod +x test_setup.sh
   ./test_setup.sh
   ```

3. **Run sandbox**:
   ```bash
   chmod +x run_sandbox.sh
   ./run_sandbox.sh
   ```

4. **View results**:
   ```bash
   ls assessments/
   cat assessments/assessment_1.md
   ```

## Sandbox Security

The system executes dynamically generated code in a hardened Docker container:

- **Read-only root filesystem** with tmpfs for necessary writable directories
- **Non-privileged user** (sandbox, UID 1000)
- **Dropped capabilities** (--cap-drop ALL)
- **Resource limits** to prevent DoS
- **Ephemeral runtime**: Generated agents destroyed after execution
- **Persistent outputs**: Only analysis markdown files survive in `./assessments/`

⚠️ **Security Note**: While sandboxed, this system generates and executes LLM-produced code. Do not include classified information in prompts or system messages.

## Configuration

Edit variables in `run_sandbox.sh`:
- `MEMORY_LIMIT`: Container memory (default: 2g)
- `CPUS`: CPU allocation (default: 2.0)
- `PIDS_LIMIT`: Max processes (default: 128)

Edit variables in `world.py`:
- `HOW_MANY_AGENTS`: Number of agents to create (default: 10)

Modify agent behavior in `agent.py`:
- `CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER`: Collaboration probability (default: 0.8)

## Project Structure

```
.
├── run_sandbox.sh          # Sandbox execution script
├── Dockerfile              # Container image definition
├── test_setup.sh           # Pre-flight checks
├── world.py                # Agent orchestration
├── creator.py              # Dynamic agent generator
├── agent.py                # Agent template
├── messages.py             # Communication protocol
└── assessments/            # Output directory (created automatically)
```


## Requirements

- Docker Desktop 4.0+ with ARM64 support
- 4GB+ RAM available for Docker
- OpenAI API key with GPT-4 access
- macOS ARM64 (Apple Silicon)

## License

GNU General Public License (GPL) 3.0

## Author

Pablo Martínez Agulló

<!-- ## What It Does

- **Generates** {HOW_MANY_AGENTS} **AI agents** with unique military specializations (cyber, intelligence, logistics, etc.)
- Agents autonomously develop **operational concepts and tactical solutions**
- **Collaborative refinement**: Agents randomly consult each other to improve analyses
- Outputs saved as markdown files (idea1.md, idea2.md, etc.) -->


<!-- **Concepts**
- **Runtime**: The execution environment where agents live and communicate. Manages message routing between agents.
- **Host service**: The server that runs the runtime. Listens for connections (e.g., on `localhost:50051`). One host can serve multiple workers.
- **Worker**: A client that connects to the host to register and run agents. Sends/receives messages through the host's runtime. -->



<!-- 
tree -I "__pycache__|__init__.py|uv.lock|README.md|tests|*.log|*.db*|*.png|*.PNG|*.md" 
 -->
