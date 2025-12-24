"""
Inter-Agent Communication Protocol
Event-driven architecture with publish-subscribe pattern
"""
import json
import time
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import threading
from collections import defaultdict


class MessageType(Enum):
    ANALYSIS = "analysis"
    ARGUMENT = "argument"
    DECISION = "decision"
    FEEDBACK = "feedback"
    REQUEST = "request"
    RESPONSE = "response"


@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication"""
    agent_id: str
    timestamp: str
    message_type: str
    content: Dict[str, Any]
    target_agents: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AgentMessage':
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        return cls.from_dict(json.loads(json_str))


class MessageBroker:
    """
    Central message broker for agent communication
    Implements publish-subscribe pattern with event-driven architecture
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_queue: List[AgentMessage] = []
        self.message_history: List[AgentMessage] = []
        self.lock = threading.Lock()
        self.max_history = 1000
    
    def subscribe(self, agent_id: str, callback: Callable[[AgentMessage], None]):
        """Subscribe an agent to receive messages"""
        with self.lock:
            self.subscribers[agent_id].append(callback)
    
    def unsubscribe(self, agent_id: str, callback: Callable[[AgentMessage], None]):
        """Unsubscribe an agent"""
        with self.lock:
            if callback in self.subscribers[agent_id]:
                self.subscribers[agent_id].remove(callback)
    
    def publish(self, message: AgentMessage):
        """Publish a message to target agents"""
        # Prepare under lock
        with self.lock:
            # Add to history
            self.message_history.append(message)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)
            # Add to queue
            self.message_queue.append(message)
            # Copy callbacks to call outside the lock
            callbacks_to_invoke = []
            for target in message.target_agents:
                if target in self.subscribers:
                    # extend with a shallow copy to avoid mutation issues
                    callbacks_to_invoke.extend(list(self.subscribers[target]))
        # Invoke callbacks without holding the lock
        for callback in callbacks_to_invoke:
            try:
                callback(message)
            except Exception as e:
                print(f"[ERROR] Callback failed: {e}")
    
    def broadcast(self, message: AgentMessage):
        """Broadcast message to all subscribers"""
        # Prepare under lock
        with self.lock:
            self.message_history.append(message)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)
            # Flatten all callbacks into a list copy
            callbacks_to_invoke = []
            for _, callbacks in self.subscribers.items():
                callbacks_to_invoke.extend(list(callbacks))
        # Invoke callbacks without holding the lock
        for callback in callbacks_to_invoke:
            try:
                callback(message)
            except Exception as e:
                print(f"[ERROR] Broadcast callback failed: {e}")
    
    def get_messages_for_agent(self, agent_id: str, message_type: Optional[str] = None) -> List[AgentMessage]:
        """Retrieve messages for a specific agent"""
        with self.lock:
            messages = [
                msg for msg in self.message_history
                if agent_id in msg.target_agents or msg.target_agents == ["*"]
            ]
            if message_type:
                messages = [msg for msg in messages if msg.message_type == message_type]
            return messages
    
    def create_message(
        self,
        agent_id: str,
        message_type: str,
        content: Dict[str, Any],
        target_agents: List[str]
    ) -> AgentMessage:
        """Helper method to create standardized messages"""
        return AgentMessage(
            agent_id=agent_id,
            timestamp=datetime.utcnow().isoformat(),
            message_type=message_type,
            content=content,
            target_agents=target_agents
        )


# Global message broker instance
_global_broker: Optional[MessageBroker] = None


def get_broker() -> MessageBroker:
    """Get or create global message broker instance"""
    global _global_broker
    if _global_broker is None:
        _global_broker = MessageBroker()
    return _global_broker


def reset_broker():
    """Reset global broker (useful for testing)"""
    global _global_broker
    _global_broker = MessageBroker()

