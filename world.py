from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from agent import Agent
from creator import Creator, ValidationFailureException
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio
from pathlib import Path
import logging
import os
from datetime import datetime
from metrics import MetricsCollector, AgentMetrics

# Configuration
HOW_MANY_AGENTS = 10
OUTPUT_DIR = Path(os.getenv("ASSESSMENT_DIR", "/assessments"))
AGENT_TIMEOUT_SECONDS = 120  # 2 minutes per agent

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

# Global metrics collector
metrics_collector = MetricsCollector()

async def create_and_message(worker: GrpcWorkerAgentRuntime, creator_id: AgentId, i: int) -> None:
    start_time = datetime.now()
    agent_id = f"agent{i}"

    try:
        logger.info(f"Creating agent {i}")
        # Add timeout to prevent hung agents
        result = await asyncio.wait_for(
            worker.send_message(messages.Message(content=f"agent{i}.py"), creator_id),
            timeout=AGENT_TIMEOUT_SECONDS
        )

        # Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


        # Save assessment in the designated folder
        output_file = OUTPUT_DIR / f"assessment_{i}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.content)
        logger.info(f"Assessment {i} saved to {output_file}")

        # Record successful execution metrics
        metrics_collector.record(AgentMetrics(
            agent_id=agent_id,
            start_time=start_time,
            end_time=datetime.now(),
            success=True,
            code_length=len(result.content),
            error_message=None
        ))

    except asyncio.TimeoutError:
        logger.error(f"Agent {i} timed out after {AGENT_TIMEOUT_SECONDS} seconds")
        
        # Create timeout assessment
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timeout_content = f"# Agent {i} exceeded the {AGENT_TIMEOUT_SECONDS} seconds execution limit."
        output_file = OUTPUT_DIR / f"assessment_{i}_TIMEOUT.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(timeout_content)
        logger.warning(f"Timeout assessment created: {output_file}")

        # Record timeout metrics
        metrics_collector.record(AgentMetrics(
            agent_id=agent_id,
            start_time=start_time,
            end_time=datetime.now(),
            success=False,
            code_length=0,
            error_message=f"Timeout after {AGENT_TIMEOUT_SECONDS}s"
        ))
        
    except ValidationFailureException as e:
        logger.error(f"Agent {i} failed validation")
        
        # Create validation failure assessment
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / f"assessment_{i}_VALIDATION_FAILED.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(e))
        logger.warning(f"Validation failure assessment created: {output_file}")
        
        # Record validation failure metrics
        metrics_collector.record(AgentMetrics(
            agent_id=agent_id,
            start_time=start_time,
            end_time=datetime.now(),
            success=False,
            code_length=0,
            error_message=f"Validation failed: {str(e)[:100]}"
        ))

    except Exception as e:
        logger.error(f"Failed to run worker {i} due to exception: {e}")

        # Record failure metrics
        metrics_collector.record(AgentMetrics(
            agent_id=agent_id,
            start_time=start_time,
            end_time=datetime.now(),
            success=False,
            code_length=0,
            error_message=str(e)
        ))

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

    # Save and print metrics summary
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_collector.save_summary(OUTPUT_DIR / "execution_metrics.json")
    metrics_collector.print_summary()
    logger.info(f"Metrics saved to {OUTPUT_DIR / 'execution_metrics.json'}")


if __name__ == "__main__":
    asyncio.run(main())