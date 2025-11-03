"""
Metrics collection for multi-agent execution tracking.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import json


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    agent_id: str
    start_time: datetime
    end_time: datetime
    success: bool
    code_length: int
    error_message: Optional[str] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'agent_id': self.agent_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'code_length': self.code_length,
            'error_message': self.error_message
        }


class MetricsCollector:
    """Collects and aggregates metrics across all agents."""
    
    def __init__(self):
        self.metrics: List[AgentMetrics] = []
    
    def record(self, metric: AgentMetrics) -> None:
        """Record a single agent's metrics."""
        self.metrics.append(metric)
    
    def get_summary(self) -> dict:
        """Generate summary statistics."""
        if not self.metrics:
            return {'error': 'No metrics collected'}
        
        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]
        
        return {
            'execution_time': datetime.now().isoformat(),
            'total_agents': len(self.metrics),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.metrics) * 100,
            'total_duration_seconds': sum(m.duration_seconds for m in self.metrics),
            'avg_duration_seconds': sum(m.duration_seconds for m in self.metrics) / len(self.metrics),
            'min_duration_seconds': min(m.duration_seconds for m in self.metrics),
            'max_duration_seconds': max(m.duration_seconds for m in self.metrics),
            'total_code_generated_chars': sum(m.code_length for m in self.metrics),
            'agents': [m.to_dict() for m in self.metrics]
        }
    
    def save_summary(self, output_path: Path) -> None:
        """Save metrics summary to JSON file."""
        summary = self.get_summary()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def print_summary(self) -> None:
        """Print summary to console."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("EXECUTION METRICS SUMMARY")
        print("="*60)
        print(f"Total Agents:     {summary['total_agents']}")
        print(f"Successful:       {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed:           {summary['failed']}")
        print(f"Avg Duration:     {summary['avg_duration_seconds']:.2f}s")
        print(f"Min Duration:     {summary['min_duration_seconds']:.2f}s")
        print(f"Max Duration:     {summary['max_duration_seconds']:.2f}s")
        print(f"Total Duration:   {summary['total_duration_seconds']:.2f}s")
        print(f"Code Generated:   {summary['total_code_generated_chars']:,} chars")
        print("="*60)
        
        if summary['failed'] > 0:
            print("\nFailed Agents:")
            for metric in self.metrics:
                if not metric.success:
                    print(f"  - {metric.agent_id}: {metric.error_message}")
            print("="*60)