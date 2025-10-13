from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv
import logging


load_dotenv(override=True)

# Configuration
LLM_MODEL = "gpt-4o-mini"

# Logging setup
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Agent(RoutedAgent):

    # Note: Change this system message to reflect the unique characteristics of this agent

    system_message = """
    You are a defense and military strategic analyst. Your task is to develop or refine operational concepts, tactical solutions, or defense technology applications using Agentic AI.
    Your areas of expertise: [Cybersecurity, Intelligence Analysis, Logistics, Reconnaissance, etc.]
    You focus on: [operational efficiency, threat detection, force protection, etc.]
    You prioritize: mission success, security, reliability over innovation for innovation's sake.
    You are analytical, cautious, risk-aware and detail-oriented.
    Your weaknesses: can be overly conservative, may overlook unconventional approaches.
    Provide your analysis in a structured, clear and actionable format.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.8 # For critical analysis, I may want to favour getting second opinion
    
    #CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.2 # Foroperations that requeire fasr decissionnaking 


    # Note: You can also change the code to make the behavior different, but be careful to keep method signatures the same

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model=LLM_MODEL, temperature=0.4)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)
        logger.info(f"Agent {name} initialized with model {LLM_MODEL}")

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        logger.info(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content

        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            logger.info(f"{self.id.type}: Bouncing idea to {recipient.type}")
            message = f"Here is my idea. It may not be your speciality, but please refine it and make it better. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content

        logger.info(f"{self.id.type}: Completed processing")
        return messages.Message(content=idea)