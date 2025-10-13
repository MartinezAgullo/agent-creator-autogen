from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from agent import Agent
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio
from pathlib import Path
import logging

# Configuration
HOW_MANY_AGENTS = 10
OUTPUT_DIR = "assessments"

# Logging setup
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
# Silence verbose AutoGen loggers
logging.getLogger('autogen_core').setLevel(logging.WARNING)
logging.getLogger('autogen_core.events').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def create_and_message(worker: GrpcWorkerAgentRuntime, creator_id: AgentId, i: int) -> None:

    try:
        logger.info(f"Creating agent {i}")
        result = await worker.send_message(messages.Message(content=f"agent{i}.py"), creator_id)

        # Create output directory if it doesn't exist
        output_path = Path(OUTPUT_DIR)
        output_path.mkdir(exist_ok=True)

        # Save assessment in the designated folder
        output_file = output_path / f"assessment_{i}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.content)
        logger.info(f"Assessment {i} saved to {output_file}")

    except Exception as e:
        logger.error(f"Failed to run worker {i} due to exception: {e}")

async def main() -> None:
    logger.info("Starting multi-agent system")
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start()
    logger.info("Host started")

    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()
    logger.info("Worker runtime started")

    result = await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    creator_id = AgentId("Creator", "default")
    coroutines = [create_and_message(worker, creator_id, i) for i in range(1, HOW_MANY_AGENTS+1)]
    await asyncio.gather(*coroutines)
    logger.info("All agents completed")

    try:
        await worker.stop()
        await host.stop()
        logger.info("System shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    asyncio.run(main())


