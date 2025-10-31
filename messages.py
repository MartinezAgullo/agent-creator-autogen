from dataclasses import dataclass
from autogen_core import AgentId
import glob
import os
import logging
from pathlib import Path
import random

logger = logging.getLogger(__name__)

@dataclass
class Message:
    content: str


def find_recipient() -> AgentId:
    # Busca otro agente al que enviar ese mensaje
    try:
        runtime_dir = Path(os.getenv("AGENT_RUNTIME_DIR", "/runtime"))
        agent_files = glob.glob(str(runtime_dir / "agent*.py")) # los clones se llaman agente1.py, agente2.py, agente3.py, etc etc
        agent_names = [Path(f).stem for f in agent_files if Path(f).stem != "agent"]
        if not agent_names:
            raise RuntimeError("No agents found in runtime directory")
        agent_name = random.choice(agent_names)
        logger.info(f"Selecting agent for refinement: {agent_name}") # elige un agente al azar
        return AgentId(agent_name, "default")
    
    except Exception as e:
        print(f"Exception finding recipient: {e}")
        return AgentId("agent1", "default")
