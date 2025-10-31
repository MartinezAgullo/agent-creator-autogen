from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from pathlib import Path
import messages
import random
import os
import logging

load_dotenv(override=True)

# Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
ASSESS_DIR = Path(os.getenv("ASSESSMENT_DIR", "/assessments"))
RUNTIME_DIR = Path(os.getenv("AGENT_RUNTIME_DIR", "/runtime"))

# Logging setup
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Agent(RoutedAgent):

    # System message — defines personality & expertise of each agent

    system_message = """
    You are a defense and military strategic analyst. Your task is to develop or refine operational concepts, tactical solutions, or defense technology applications using Agentic AI.
    Your areas of expertise: [Cybersecurity, Intelligence Analysis, Logistics, Reconnaissance, etc.]
    You focus on: [operational efficiency, threat detection, force protection, etc.]
    You prioritize: mission success, security, reliability over innovation for innovation's sake.
    You are analytical, cautious, risk-aware and detail-oriented.
    Your weaknesses: can be overly conservative, may overlook unconventional approaches.
    Provide your analysis in a structured, clear and actionable format.
    """

    # Behavior tuning
    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.8 # More peer-review & refinement
    #CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.2 # For operations that requeire fast decissionnaking 


    # Note: You can also change the code to make the behavior different, but be careful to keep method signatures the same

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model=LLM_MODEL, temperature=0.4)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)
        
        # Ensure runtime and assessment dirs exist (in container)
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        ASSESS_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"Agent {name} initialized with model {LLM_MODEL}")

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        logger.info(f"{self.id.type}: Received message")
        
        # Step 1: Generate initial idea
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content

        # Step 2: Maybe bounce to another agent for refinement
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            logger.info(f"{self.id.type}: Bouncing idea to {recipient.type}")
            bounce_msg = (
                f"Here is my idea. It may not be your speciality, but please refine it and make it better.\n\n{idea}"
            )
            response = await self.send_message(messages.Message(content=bounce_msg), recipient)
            idea = response.content

        # Step 3: Persist analysis to assessments folder
        try:
            output_path = ASSESS_DIR / f"assessment_{self.id.type}.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(idea)
            logger.info(f"{self.id.type}: Saved analysis to {output_path}")
        except Exception as e:
            logger.error(f"{self.id.type}: Failed to save analysis: {e}")

        logger.info(f"{self.id.type}: Completed processing")
        return messages.Message(content=idea)