"""
ULTRA-LOW LATENCY Performance Monitor
Real-time latency tracking and optimization diagnostics
Monitors: Agent response time, audio processing, connection overhead
"""

import asyncio
import time
import statistics
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class LatencyMetrics:
    """Track latency metrics for performance analysis"""
    session_id: str
    timestamp: float = field(default_factory=time.time)
    
    # Connection metrics
    room_connection_ms: Optional[float] = None
    participant_ready_ms: Optional[float] = None
    agent_creation_ms: Optional[float] = None
    session_start_ms: Optional[float] = None
    
    # Audio processing metrics
    audio_frames_processed: int = 0
    avg_audio_processing_ms: Optional[float] = None
    
    # End-to-end metrics
    total_setup_time_ms: Optional[float] = None
    
    def __str__(self) -> str:
        return (
            f"Latency Metrics [{self.session_id}]:\n"
            f"  Room Connection: {self.room_connection_ms:.0f}ms\n"
            f"  Participant Ready: {self.participant_ready_ms:.0f}ms\n"
            f"  Agent Creation: {self.agent_creation_ms:.0f}ms\n"
            f"  Session Start: {self.session_start_ms:.0f}ms\n"
            f"  Total Setup: {self.total_setup_time_ms:.0f}ms\n"
            f"  Audio Frames: {self.audio_frames_processed}"
        )


class PerformanceMonitor:
    """
    Real-time performance monitoring for ultra-low latency optimization
    Tracks and analyzes latency metrics across all sessions
    """
    
    def __init__(self):
        self.sessions: Dict[str, LatencyMetrics] = {}
        self.historical_metrics: List[LatencyMetrics] = []
        self.start_time = time.time()
        
    def create_session(self, session_id: str) -> LatencyMetrics:
        """Create a new session for latency tracking"""
        metrics = LatencyMetrics(session_id=session_id)
        self.sessions[session_id] = metrics
        return metrics
    
    def end_session(self, session_id: str):
        """End a session and archive metrics"""
        if session_id in self.sessions:
            metrics = self.sessions.pop(session_id)
            self.historical_metrics.append(metrics)
            
            # Keep only last 100 sessions in memory
            if len(self.historical_metrics) > 100:
                self.historical_metrics = self.historical_metrics[-100:]
    
    def get_statistics(self) -> Dict:
        """Get performance statistics across all sessions"""
        if not self.historical_metrics:
            return {"status": "no_data", "sessions": 0}
        
        setup_times = [m.total_setup_time_ms for m in self.historical_metrics if m.total_setup_time_ms]
        room_connections = [m.room_connection_ms for m in self.historical_metrics if m.room_connection_ms]
        agent_creations = [m.agent_creation_ms for m in self.historical_metrics if m.agent_creation_ms]
        
        return {
            "status": "ok",
            "sessions": len(self.historical_metrics),
            "active_sessions": len(self.sessions),
            "uptime_seconds": time.time() - self.start_time,
            "avg_setup_time_ms": statistics.mean(setup_times) if setup_times else 0,
            "median_setup_time_ms": statistics.median(setup_times) if setup_times else 0,
            "min_setup_time_ms": min(setup_times) if setup_times else 0,
            "max_setup_time_ms": max(setup_times) if setup_times else 0,
            "avg_room_connection_ms": statistics.mean(room_connections) if room_connections else 0,
            "avg_agent_creation_ms": statistics.mean(agent_creations) if agent_creations else 0,
            "target_latency_ms": 500,
            "achievement_rate": self._calculate_achievement_rate(setup_times),
        }
    
    def _calculate_achievement_rate(self, setup_times: List[float], target: float = 500) -> float:
        """Calculate percentage of sessions meeting latency target"""
        if not setup_times:
            return 0.0
        meeting_target = sum(1 for t in setup_times if t <= target)
        return (meeting_target / len(setup_times)) * 100
    
    def print_report(self):
        """Print performance report to console"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 70)
        print("⚡ ULTRA-LOW LATENCY PERFORMANCE REPORT")
        print("=" * 70)
        print(f"Sessions Completed: {stats['sessions']}")
        print(f"Active Sessions: {stats['active_sessions']}")
        print(f"Uptime: {stats['uptime_seconds']:.0f}s")
        print("-" * 70)
        print(f"Average Setup Time: {stats['avg_setup_time_ms']:.0f}ms")
        print(f"Median Setup Time: {stats['median_setup_time_ms']:.0f}ms")
        print(f"Min Setup Time: {stats['min_setup_time_ms']:.0f}ms")
        print(f"Max Setup Time: {stats['max_setup_time_ms']:.0f}ms")
        print("-" * 70)
        print(f"Avg Room Connection: {stats['avg_room_connection_ms']:.0f}ms")
        print(f"Avg Agent Creation: {stats['avg_agent_creation_ms']:.0f}ms")
        print("-" * 70)
        print(f"Target Latency: {stats['target_latency_ms']}ms")
        print(f"Achievement Rate: {stats['achievement_rate']:.1f}%")
        print("=" * 70)
        
        # Performance analysis
        avg_time = stats['avg_setup_time_ms']
        if avg_time < 400:
            print("✅ EXCELLENT - Ultra-low latency achieved!")
        elif avg_time < 500:
            print("✅ GOOD - Meeting target latency")
        elif avg_time < 700:
            print("⚠️  ACCEPTABLE - Above target, optimization recommended")
        else:
            print("❌ SLOW - Optimization required")
        print("=" * 70 + "\n")


class LatencyTracker:
    """Simple latency tracker for individual operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.perf_counter()
        return self
    
    def stop(self) -> float:
        """Stop timing and return latency in milliseconds"""
        self.end_time = time.perf_counter()
        latency_ms = (self.end_time - self.start_time) * 1000
        return latency_ms
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency = self.stop()
        logger.info(f"⚡ {self.operation_name}: {latency:.0f}ms")


# Global performance monitor instance
global_monitor = PerformanceMonitor()


async def performance_report_task(interval_seconds: int = 300):
    """
    Background task to print performance reports periodically
    Run this in your main application loop
    """
    while True:
        await asyncio.sleep(interval_seconds)
        global_monitor.print_report()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return global_monitor


# Example usage in agent.py:
"""
from performance_monitor import get_monitor, LatencyTracker

async def entrypoint(ctx: JobContext):
    monitor = get_monitor()
    session_id = ctx.room.name
    metrics = monitor.create_session(session_id)
    
    # Track room connection
    with LatencyTracker("Room Connection") as tracker:
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    metrics.room_connection_ms = tracker.stop()
    
    # ... rest of your code
    
    monitor.end_session(session_id)
"""


if __name__ == "__main__":
    # Demo usage
    monitor = PerformanceMonitor()
    
    # Simulate some sessions
    for i in range(10):
        session_id = f"test-session-{i}"
        metrics = monitor.create_session(session_id)
        metrics.room_connection_ms = 50 + (i * 10)
        metrics.participant_ready_ms = 30 + (i * 5)
        metrics.agent_creation_ms = 100 + (i * 15)
        metrics.session_start_ms = 200 + (i * 20)
        metrics.total_setup_time_ms = sum([
            metrics.room_connection_ms,
            metrics.participant_ready_ms,
            metrics.agent_creation_ms,
            metrics.session_start_ms,
        ])
        monitor.end_session(session_id)
    
    # Print report
    monitor.print_report()

