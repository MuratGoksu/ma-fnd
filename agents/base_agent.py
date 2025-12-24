"""
Base Agent class with communication capabilities
All agents inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .message_broker import MessageBroker, AgentMessage, get_broker, MessageType


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.broker: MessageBroker = get_broker()
        self.broker.subscribe(self.agent_id, self._handle_message)
        self.state: Dict[str, Any] = {}
    
    def _handle_message(self, message: AgentMessage):
        """Default message handler - can be overridden"""
        if message.agent_id != self.agent_id:  # Don't process own messages
            self.on_message(message)
    
    def on_message(self, message: AgentMessage):
        """Override this method to handle incoming messages"""
        pass
    
    def send_message(
        self,
        message_type: str,
        content: Dict[str, Any],
        target_agents: List[str]
    ):
        """Send a message to other agents"""
        message = self.broker.create_message(
            agent_id=self.agent_id,
            message_type=message_type,
            content=content,
            target_agents=target_agents
        )
        self.broker.publish(message)
    
    def broadcast(self, message_type: str, content: Dict[str, Any]):
        """Broadcast message to all agents"""
        message = self.broker.create_message(
            agent_id=self.agent_id,
            message_type=message_type,
            content=content,
            target_agents=["*"]
        )
        self.broker.broadcast(message)
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method - must be implemented by subclasses"""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return self.state.copy()
    
    def update_state(self, key: str, value: Any):
        """Update agent state"""
        self.state[key] = value

