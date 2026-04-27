import random
import hashlib
import time
import threading
from typing import List, Dict, Any, Optional

class LLMNode:
    """Represents a single LLM API Key node for load balancing"""
    def __init__(self, key_id: int, weight: int = 1):
        self.key_id = key_id
        self.weight = weight
        self.active_connections = 0
        self.fail_count = 0
        self.last_fail_time = 0
        self.is_circuit_breaker_open = False
        
        # For Weighted Round Robin (Smooth WRR)
        self.current_weight = 0
        self.effective_weight = weight

    def reset_wrr(self):
        self.current_weight = 0

class LoadBalancer:
    """Base class for LLM Load Balancers"""
    def __init__(self, nodes: List[LLMNode]):
        self.nodes = nodes
        self.lock = threading.Lock()

    def select(self, context: Dict[str, Any] = None) -> Optional[LLMNode]:
        raise NotImplementedError()

class RoundRobinBalancer(LoadBalancer):
    def __init__(self, nodes: List[LLMNode]):
        super().__init__(nodes)
        self.current_index = 0

    def select(self, context: Dict[str, Any] = None) -> Optional[LLMNode]:
        with self.lock:
            if not self.nodes:
                return None
            
            # Filter available nodes (not breaker open)
            available_nodes = [n for n in self.nodes if not n.is_circuit_breaker_open]
            if not available_nodes:
                return None
            
            node = available_nodes[self.current_index % len(available_nodes)]
            self.current_index = (self.current_index + 1) % len(available_nodes)
            return node

class WeightedRoundRobinBalancer(LoadBalancer):
    """Nginx-style Smooth Weighted Round Robin"""
    def select(self, context: Dict[str, Any] = None) -> Optional[LLMNode]:
        with self.lock:
            available_nodes = [n for n in self.nodes if not n.is_circuit_breaker_open]
            if not available_nodes:
                return None
            
            total_weight = 0
            best_node = None
            
            for node in available_nodes:
                node.current_weight += node.effective_weight
                total_weight += node.effective_weight
                
                if best_node is None or node.current_weight > best_node.current_weight:
                    best_node = node
            
            if best_node:
                best_node.current_weight -= total_weight
            
            return best_node

class RandomBalancer(LoadBalancer):
    def select(self, context: Dict[str, Any] = None) -> Optional[LLMNode]:
        available_nodes = [n for n in self.nodes if not n.is_circuit_breaker_open]
        if not available_nodes:
            return None
            
        total_weight = sum(n.weight for n in available_nodes)
        if total_weight <= 0:
            return random.choice(available_nodes)
            
        r = random.uniform(0, total_weight)
        upto = 0
        for n in available_nodes:
            if upto + n.weight >= r:
                return n
            upto += n.weight
        return available_nodes[-1]

class ConsistentHashBalancer(LoadBalancer):
    def __init__(self, nodes: List[LLMNode], replicas: int = 160):
        super().__init__(nodes)
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        self._build_ring()

    def _build_ring(self):
        self.ring = {}
        for node in self.nodes:
            for i in range(self.replicas):
                h = self._hash(f"{node.key_id}:{i}")
                self.ring[h] = node
        self.sorted_keys = sorted(self.ring.keys())

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def select(self, context: Dict[str, Any] = None) -> Optional[LLMNode]:
        if not self.nodes:
            return None
            
        # Context should provide a key for hashing, e.g. user_id
        hash_key = str(context.get('user_id', 'default')) if context else 'default'
        h = self._hash(hash_key)
        
        # Simple ring search
        for key in self.sorted_keys:
            if h <= key:
                node = self.ring[key]
                if not node.is_circuit_breaker_open:
                    return node
        
        # Fallback to first if not found or wrapped around
        for key in self.sorted_keys:
            node = self.ring[key]
            if not node.is_circuit_breaker_open:
                return node
                
        return None

class LeastConnectionsBalancer(LoadBalancer):
    def select(self, context: Dict[str, Any] = None) -> Optional[LLMNode]:
        available_nodes = [n for n in self.nodes if not n.is_circuit_breaker_open]
        if not available_nodes:
            return None
            
        return min(available_nodes, key=lambda n: n.active_connections)

class LLMLBService:
    _instances = {} # strategy -> Balancer
    _nodes_cache = {} # model_id -> List[LLMNode]
    _lock = threading.Lock()

    @classmethod
    def get_balancer(cls, strategy: str, nodes: List[LLMNode]) -> LoadBalancer:
        if strategy == 'weighted_round_robin':
            return WeightedRoundRobinBalancer(nodes)
        elif strategy == 'round_robin':
            return RoundRobinBalancer(nodes)
        elif strategy == 'random':
            return RandomBalancer(nodes)
        elif strategy == 'consistent_hash':
            return ConsistentHashBalancer(nodes)
        elif strategy == 'least_connections':
            return LeastConnectionsBalancer(nodes)
        else:
            return RoundRobinBalancer(nodes)

    @classmethod
    def select_node(cls, model_id: int, strategy: str, nodes: List[LLMNode], context: Dict[str, Any] = None) -> Optional[LLMNode]:
        # Simple strategy to reuse balancers if nodes didn't change
        # In a real system, we'd check if node list changed
        balancer = cls.get_balancer(strategy, nodes)
        return balancer.select(context)
