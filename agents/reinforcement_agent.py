"""
Reinforcement Agent (RLA)
Görev: Sistem öğrenmesi
"""
from typing import Dict, Any, List, Optional, Tuple
from .base_agent import BaseAgent
import random


class ReinforcementAgent(BaseAgent):
    """
    Reinforcement Agent - Sistem öğrenmesi
    Deep Q-Learning, Policy Gradient için hazır
    """
    
    def __init__(self):
        super().__init__("RLA")
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.action_history: List[Dict[str, Any]] = []
        self.reward_history: List[float] = []
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # Exploration rate
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        state = data.get("state", {})
        action = data.get("action")
        reward = data.get("reward")
        
        if action and reward is not None:
            # Öğrenme
            learning_result = self.learn(state, action, reward)
            
            result = {
                "status": "learned",
                "learning": learning_result,
                "q_value": learning_result.get("q_value", 0.0)
            }
        else:
            # Aksiyon seçimi
            action_result = self.select_action(state)
            
            result = {
                "status": "action_selected",
                "action": action_result.get("action"),
                "q_value": action_result.get("q_value", 0.0)
            }
        
        # Mesaj gönder
        self.send_message(
            message_type="feedback",
            content={
                "type": "reinforcement_update",
                "data": result
            },
            target_agents=["JA", "OA"]
        )
        
        return result
    
    def learn(self, state: Dict[str, Any], action: str, reward: float) -> Dict[str, Any]:
        """Q-Learning öğrenme"""
        state_key = self._state_to_key(state)
        
        # Q-table'ı başlat
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        if action not in self.q_table[state_key]:
            self.q_table[state_key][action] = 0.0
        
        # Mevcut Q değeri
        current_q = self.q_table[state_key][action]
        
        # Q-Learning güncelleme
        # Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        # Basitleştirilmiş: Q(s,a) = Q(s,a) + α[r - Q(s,a)]
        new_q = current_q + self.learning_rate * (reward - current_q)
        
        self.q_table[state_key][action] = new_q
        
        # Geçmişe ekle
        self.action_history.append({
            "state": state_key,
            "action": action,
            "reward": reward,
            "q_value": new_q
        })
        self.reward_history.append(reward)
        
        return {
            "state": state_key,
            "action": action,
            "reward": reward,
            "old_q_value": current_q,
            "q_value": new_q,
            "improvement": new_q - current_q
        }
    
    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Aksiyon seçimi (epsilon-greedy)"""
        state_key = self._state_to_key(state)
        
        # Q-table'ı başlat
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        
        # Epsilon-greedy: exploration vs exploitation
        if random.random() < self.epsilon:
            # Exploration: rastgele aksiyon
            actions = ["accept", "reject", "review", "request_more_info"]
            action = random.choice(actions)
        else:
            # Exploitation: en yüksek Q değerli aksiyon
            if self.q_table[state_key]:
                action = max(
                    self.q_table[state_key],
                    key=self.q_table[state_key].get
                )
            else:
                action = "review"  # Default
        
        q_value = self.q_table[state_key].get(action, 0.0)
        
        return {
            "action": action,
            "q_value": q_value,
            "state": state_key
        }
    
    def calculate_reward(
        self,
        verdict: str,
        ground_truth: str,
        processing_time: float
    ) -> float:
        """Reward hesaplama"""
        reward = 0.0
        
        # Doğru tahmin
        if verdict == ground_truth:
            reward += 1.0
        # False positive
        elif verdict == "FAKE" and ground_truth == "REAL":
            reward -= 0.8
        # False negative
        elif verdict == "REAL" and ground_truth == "FAKE":
            reward -= 1.2
        # UNSURE (küçük ceza)
        elif verdict == "UNSURE":
            reward -= 0.1
        
        # Hız bonusu
        if processing_time < 30.0:  # 30 saniyeden az
            reward += 0.1
        
        return reward
    
    def get_policy(self) -> Dict[str, Dict[str, float]]:
        """Mevcut policy'yi döndür"""
        return self.q_table.copy()
    
    def _state_to_key(self, state: Dict[str, Any]) -> str:
        """State'i key'e çevir"""
        # Basit state representation
        confidence = state.get("confidence", 0.5)
        source_cred = state.get("source_credibility", 0.5)
        
        # Discretize
        conf_bin = int(confidence * 10) / 10
        cred_bin = int(source_cred * 10) / 10
        
        return f"conf_{conf_bin:.1f}_cred_{cred_bin:.1f}"
    
    def get_average_reward(self, window: int = 100) -> float:
        """Son N reward'un ortalaması"""
        if not self.reward_history:
            return 0.0
        
        recent_rewards = self.reward_history[-window:]
        return sum(recent_rewards) / len(recent_rewards)

