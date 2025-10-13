from dataclasses import dataclass
from autogen_core import AgentId
import glob
import os


import random

@dataclass
class Message:
    content: str


def find_recipient() -> AgentId:
    # Busca otro agente al que enviar ese mensaje
    try:
        agent_files = glob.glob("agent*.py") # los clones se llaman agente1.py, agente2.py, agente3.py, etc etc
        agent_names = [os.path.splitext(file)[0] for file in agent_files]
        agent_names.remove("agent")
        agent_name = random.choice(agent_names) # elige un agente al azar
        print(f"Selecting agent for refinement: {agent_name}")
        return AgentId(agent_name, "default")
    except Exception as e:
        print(f"Exception finding recipient: {e}")
        return AgentId("agent1", "default")
