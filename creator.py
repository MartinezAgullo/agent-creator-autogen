from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import importlib
import logging
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
from validator import CodeValidator


load_dotenv(override=True)

# Configuration
LLM_MODEL = "gpt-4o-mini"

# Base writable dir inside container
RUNTIME_DIR = Path(os.getenv("AGENT_RUNTIME_DIR", "/runtime"))
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationFailureException(Exception):
    """Raised when code validation fails after retry."""
    pass

class Creator(RoutedAgent):

    # Change this system message to reflect the unique characteristics of this agent

    system_message = """
    You are an Agent that creates AI Agents for defense and military applications.
    Focus on different military domains: Intelligence, Cyber Warfare, Logistics, Special Operations, Naval Strategy, Air Defense, Ground Combat, etc.
    You receive a template in the form of Python code that creates an Agent using Autogen Core and Autogen Agentchat.
    You should use this template to create a new Agent with a unique system message that is different from the template,
    and reflects their unique characteristics, interests and goals.
    You can choose to keep their overall goal the same, or change it.
    You can choose to take this Agent in a completely different direction. The only requirement is that the class must be named Agent,
    and it must inherit from RoutedAgent and have an __init__ method that takes a name parameter.
    Also avoid environmental interests - try to mix up the business verticals so that every agent is different.
    Respond only with the python code, no other text, and no markdown code blocks.
    """


    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model=LLM_MODEL, temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)
        logger.info(f"Creator {name} initialized with model {LLM_MODEL}")

        # Ensure /runtime is in sys.path so new agents are importable
        if str(RUNTIME_DIR) not in sys.path:
            sys.path.insert(0, str(RUNTIME_DIR))


    def get_user_prompt(self):
        prompt = "Please generate a new Agent based strictly on this template. Stick to the class structure. \
            Respond only with the Python code, no other text, and no markdown code blocks.\n\n\
            Be creative about taking the agent in a new direction, but don't change method signatures.\n\n\
            Here is the template:\n\n"
        with open("/app/agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template   
        

    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        filename = message.content
        agent_name = Path(filename).stem
        logger.info(f"Creator: Generating agent code for {agent_name}")
        
        text_message = TextMessage(content=self.get_user_prompt(), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        generated_code = response.chat_message.content
        
        # Clean common LLM formatting issues
        cleaned_code = CodeValidator.clean_code(generated_code)
        
        # Validate the generated code
        is_valid, issues = CodeValidator.validate(cleaned_code)

        if not is_valid:
            logger.error(f"Creator: Generated code for {agent_name} failed validation")
            logger.error(f"Creator: Validation issues: {issues}")
            
            # Try one more time with explicit feedback
            retry_prompt = f"""
                The previous code had these validation issues:
                {chr(10).join(f"- {issue}" for issue in issues)}

                Please generate the code again, ensuring:
                1. Pure Python code (no markdown)
                2. Class named 'Agent' inheriting from RoutedAgent
                3. Has __init__ and handle_message methods
                4. No forbidden imports (subprocess, eval, socket, etc.)
                5. Code length between 500-15000 characters

                Template:
                """
            retry_prompt += self.get_user_prompt()
            
            logger.info(f"Creator: Retrying code generation for {agent_name}")
            text_message = TextMessage(content=retry_prompt, source="user")
            response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
            generated_code = response.chat_message.content
            cleaned_code = CodeValidator.clean_code(generated_code)
            
            # Validate retry
            is_valid, issues = CodeValidator.validate(cleaned_code)
            if not is_valid:
                logger.error(f"Creator: Retry failed for {agent_name}. Issues: {issues}")
                error_msg = f"Failed to generate valid agent code after retry.\nIssues:\n" + "\n".join(f"- {i}" for i in issues)
                raise ValidationFailureException(error_msg)
            
            logger.info(f"Creator: Retry successful for {agent_name}")

        # Write validated code
        agent_path = RUNTIME_DIR / f"{agent_name}.py"
        with open(agent_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)
        logger.info(f"Creator: Agent code written to {agent_path} ({len(cleaned_code)} chars)")


        # Dynamically import agent from /runtime
        try:
            spec = importlib.util.spec_from_file_location(agent_name, agent_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[agent_name] = module
            spec.loader.exec_module(module)

            await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
            logger.info(f"Creator: Agent {agent_name} is live")
            
            result = await self.send_message(
                messages.Message(content="Provide a strategic analysis or operational concept."),
                AgentId(agent_name, "default")
            )
            logger.info(f"Creator: Received result from {agent_name}")
            return messages.Message(content=result.content)

        except Exception as e:
            logger.error(f"Creator: Failed to execute {agent_name}: {e}")
            error_msg = f"# Execution Failure\n\nAgent code was valid but failed to execute.\n\n## Error:\n{str(e)}"
            raise RuntimeError(error_msg)