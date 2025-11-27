"""
Reinforcement Learning Recommender System

Uses RL to learn optimal recommendations through user feedback.

Implements:
- Multi-Armed Bandits (MAB) for A/B testing
- Contextual Bandits for context-aware recommendations
- Q-Learning for habit optimization
- Policy Gradient for personalized routines
"""
import numpy as np
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import pickle


class MultiArmedBandit:
    """
    Multi-Armed Bandit for recommendation A/B testing.

    Uses epsilon-greedy strategy with Upper Confidence Bound (UCB).
    """

    def __init__(self, n_arms: int, epsilon: float = 0.1, use_ucb: bool = True):
        """
        Initialize MAB.

        Args:
            n_arms: Number of recommendation options
            epsilon: Exploration rate (0.1 = 10% random exploration)
            use_ucb: Use Upper Confidence Bound instead of epsilon-greedy
        """
        self.n_arms = n_arms
        self.epsilon = epsilon
        self.use_ucb = use_ucb

        # Track statistics for each arm
        self.counts = np.zeros(n_arms)  # Times each arm was pulled
        self.values = np.zeros(n_arms)  # Average reward for each arm
        self.total_count = 0

    def select_arm(self) -> int:
        """
        Select which recommendation to show.

        Returns:
            Index of selected arm (recommendation)
        """
        self.total_count += 1

        if self.use_ucb:
            return self._select_ucb()
        else:
            return self._select_epsilon_greedy()

    def _select_epsilon_greedy(self) -> int:
        """Epsilon-greedy selection."""
        if np.random.random() < self.epsilon:
            # Explore: random choice
            return np.random.randint(self.n_arms)
        else:
            # Exploit: best known arm
            return int(np.argmax(self.values))

    def _select_ucb(self) -> int:
        """Upper Confidence Bound selection."""
        # Try each arm at least once
        if self.total_count <= self.n_arms:
            return self.total_count - 1

        # Calculate UCB for each arm
        ucb_values = np.zeros(self.n_arms)

        for i in range(self.n_arms):
            if self.counts[i] == 0:
                ucb_values[i] = float('inf')
            else:
                # UCB = average reward + confidence bonus
                confidence_bonus = np.sqrt(2 * np.log(self.total_count) / self.counts[i])
                ucb_values[i] = self.values[i] + confidence_bonus

        return int(np.argmax(ucb_values))

    def update(self, arm: int, reward: float):
        """
        Update arm statistics after observing reward.

        Args:
            arm: Index of arm that was pulled
            reward: Observed reward (e.g., 1 if user liked it, 0 if not)
        """
        self.counts[arm] += 1

        # Update average reward (incremental mean)
        n = self.counts[arm]
        old_value = self.values[arm]
        self.values[arm] = ((n - 1) / n) * old_value + (1 / n) * reward

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics for all arms."""
        return {
            'arm_counts': self.counts.tolist(),
            'arm_values': self.values.tolist(),
            'total_pulls': int(self.total_count),
            'best_arm': int(np.argmax(self.values)),
            'best_arm_value': float(np.max(self.values))
        }


class ContextualBandit:
    """
    Contextual Bandit for context-aware recommendations.

    Takes user context into account when making recommendations.
    Uses linear regression for each arm.
    """

    def __init__(self, n_arms: int, context_dim: int, alpha: float = 1.0):
        """
        Initialize Contextual Bandit.

        Args:
            n_arms: Number of recommendation options
            context_dim: Dimension of context features
            alpha: Exploration parameter
        """
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha

        # Linear regression parameters for each arm
        # theta[i] = weights for arm i
        self.A = [np.identity(context_dim) for _ in range(n_arms)]  # Design matrix
        self.b = [np.zeros(context_dim) for _ in range(n_arms)]  # Response vector

    def select_arm(self, context: np.ndarray) -> int:
        """
        Select arm based on context.

        Args:
            context: Context features (user state, time, etc.)

        Returns:
            Index of selected arm
        """
        context = np.array(context).flatten()

        if len(context) != self.context_dim:
            raise ValueError(f"Context dimension mismatch: expected {self.context_dim}, got {len(context)}")

        # Calculate UCB for each arm
        ucb_values = np.zeros(self.n_arms)

        for i in range(self.n_arms):
            # Estimate theta (weights) for this arm
            A_inv = np.linalg.inv(self.A[i])
            theta = A_inv.dot(self.b[i])

            # Predicted reward
            predicted_reward = theta.dot(context)

            # Confidence bonus
            confidence = self.alpha * np.sqrt(context.dot(A_inv).dot(context))

            ucb_values[i] = predicted_reward + confidence

        return int(np.argmax(ucb_values))

    def update(self, arm: int, context: np.ndarray, reward: float):
        """
        Update arm parameters after observing reward.

        Args:
            arm: Index of arm that was selected
            context: Context that was used
            reward: Observed reward
        """
        context = np.array(context).flatten()

        # Update design matrix and response vector
        self.A[arm] += np.outer(context, context)
        self.b[arm] += reward * context

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        # Calculate theta for each arm
        thetas = []
        for i in range(self.n_arms):
            try:
                A_inv = np.linalg.inv(self.A[i])
                theta = A_inv.dot(self.b[i])
                thetas.append(theta.tolist())
            except:
                thetas.append([0.0] * self.context_dim)

        return {
            'n_arms': self.n_arms,
            'context_dim': self.context_dim,
            'thetas': thetas
        }


class QLearningRecommender:
    """
    Q-Learning for habit formation and routine optimization.

    Learns optimal action sequences through trial and reward.
    """

    def __init__(
        self,
        n_states: int,
        n_actions: int,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        epsilon: float = 0.1
    ):
        """
        Initialize Q-Learning.

        Args:
            n_states: Number of possible states
            n_actions: Number of possible actions
            learning_rate: How fast to update Q-values (0-1)
            discount_factor: Importance of future rewards (0-1)
            epsilon: Exploration rate
        """
        self.n_states = n_states
        self.n_actions = n_actions
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon

        # Q-table: Q[state][action] = expected reward
        self.Q = np.zeros((n_states, n_actions))

        # Track visits for each state-action pair
        self.visit_counts = np.zeros((n_states, n_actions))

    def select_action(self, state: int) -> int:
        """
        Select action for current state.

        Args:
            state: Current state index

        Returns:
            Action index
        """
        if state >= self.n_states:
            raise ValueError(f"State {state} out of range (max: {self.n_states-1})")

        # Epsilon-greedy
        if np.random.random() < self.epsilon:
            # Explore
            return np.random.randint(self.n_actions)
        else:
            # Exploit
            return int(np.argmax(self.Q[state]))

    def update(
        self,
        state: int,
        action: int,
        reward: float,
        next_state: int
    ):
        """
        Update Q-value after observing transition.

        Args:
            state: Previous state
            action: Action taken
            reward: Immediate reward
            next_state: Resulting state
        """
        # Q-learning update rule
        current_q = self.Q[state][action]
        max_next_q = np.max(self.Q[next_state])

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.Q[state][action] = new_q
        self.visit_counts[state][action] += 1

    def get_policy(self) -> np.ndarray:
        """
        Get current optimal policy (best action for each state).

        Returns:
            Array of best actions for each state
        """
        return np.argmax(self.Q, axis=1)

    def get_statistics(self) -> Dict[str, Any]:
        """Get current Q-learning statistics."""
        policy = self.get_policy()

        return {
            'n_states': self.n_states,
            'n_actions': self.n_actions,
            'policy': policy.tolist(),
            'q_table': self.Q.tolist(),
            'visit_counts': self.visit_counts.tolist(),
            'most_visited_state_actions': self._get_most_visited()
        }

    def _get_most_visited(self, top_k: int = 5) -> List[Dict]:
        """Get most visited state-action pairs."""
        visits = []

        for state in range(self.n_states):
            for action in range(self.n_actions):
                if self.visit_counts[state][action] > 0:
                    visits.append({
                        'state': state,
                        'action': action,
                        'visits': int(self.visit_counts[state][action]),
                        'q_value': float(self.Q[state][action])
                    })

        visits.sort(key=lambda x: x['visits'], reverse=True)
        return visits[:top_k]


class RecommenderSystem:
    """
    Unified Recommender System combining multiple RL algorithms.

    Manages:
    - Multiple bandits for different recommendation types
    - Q-learning for routine optimization
    - User feedback tracking
    """

    def __init__(self):
        """Initialize recommender system."""
        # Track different recommendation types
        self.bandits: Dict[str, MultiArmedBandit] = {}
        self.contextual_bandits: Dict[str, ContextualBandit] = {}
        self.q_learners: Dict[str, QLearningRecommender] = {}

        # Track feedback history
        self.feedback_history = []

    def create_bandit(
        self,
        name: str,
        recommendations: List[str],
        use_ucb: bool = True
    ):
        """
        Create a new multi-armed bandit for a recommendation type.

        Args:
            name: Name of recommendation type (e.g., 'morning_routine')
            recommendations: List of possible recommendations
            use_ucb: Use UCB algorithm
        """
        self.bandits[name] = {
            'bandit': MultiArmedBandit(
                n_arms=len(recommendations),
                use_ucb=use_ucb
            ),
            'recommendations': recommendations
        }

    def create_contextual_bandit(
        self,
        name: str,
        recommendations: List[str],
        context_features: List[str]
    ):
        """
        Create contextual bandit.

        Args:
            name: Name of recommendation type
            recommendations: List of possible recommendations
            context_features: Names of context features
        """
        self.contextual_bandits[name] = {
            'bandit': ContextualBandit(
                n_arms=len(recommendations),
                context_dim=len(context_features)
            ),
            'recommendations': recommendations,
            'context_features': context_features
        }

    def create_q_learner(
        self,
        name: str,
        states: List[str],
        actions: List[str]
    ):
        """
        Create Q-learning agent.

        Args:
            name: Name of habit/routine
            states: List of possible states
            actions: List of possible actions
        """
        self.q_learners[name] = {
            'learner': QLearningRecommender(
                n_states=len(states),
                n_actions=len(actions)
            ),
            'states': states,
            'actions': actions
        }

    def get_recommendation(
        self,
        recommendation_type: str,
        context: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Get a recommendation.

        Args:
            recommendation_type: Type of recommendation
            context: Optional context for contextual bandits

        Returns:
            Recommendation with metadata
        """
        timestamp = datetime.now().isoformat()

        # Check contextual bandit first
        if recommendation_type in self.contextual_bandits and context:
            cb_data = self.contextual_bandits[recommendation_type]
            bandit = cb_data['bandit']

            # Prepare context vector
            context_vector = [
                context.get(feat, 0.0)
                for feat in cb_data['context_features']
            ]

            arm = bandit.select_arm(context_vector)
            recommendation = cb_data['recommendations'][arm]

            return {
                'recommendation': recommendation,
                'arm_index': arm,
                'type': 'contextual_bandit',
                'timestamp': timestamp,
                'context': context
            }

        # Check regular bandit
        elif recommendation_type in self.bandits:
            bandit_data = self.bandits[recommendation_type]
            bandit = bandit_data['bandit']

            arm = bandit.select_arm()
            recommendation = bandit_data['recommendations'][arm]

            return {
                'recommendation': recommendation,
                'arm_index': arm,
                'type': 'multi_armed_bandit',
                'timestamp': timestamp
            }

        else:
            raise ValueError(f"Unknown recommendation type: {recommendation_type}")

    def record_feedback(
        self,
        recommendation_type: str,
        arm_index: int,
        feedback: float,
        context: Dict[str, float] = None
    ):
        """
        Record user feedback on recommendation.

        Args:
            recommendation_type: Type of recommendation
            arm_index: Index of recommendation that was shown
            feedback: User feedback (0-1, where 1 = loved it)
            context: Context if contextual bandit
        """
        # Update bandit
        if recommendation_type in self.contextual_bandits and context:
            cb_data = self.contextual_bandits[recommendation_type]
            context_vector = [
                context.get(feat, 0.0)
                for feat in cb_data['context_features']
            ]
            cb_data['bandit'].update(arm_index, context_vector, feedback)

        elif recommendation_type in self.bandits:
            self.bandits[recommendation_type]['bandit'].update(arm_index, feedback)

        # Record in history
        self.feedback_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': recommendation_type,
            'arm': arm_index,
            'feedback': feedback,
            'context': context
        })

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for all recommenders."""
        stats = {
            'bandits': {},
            'contextual_bandits': {},
            'q_learners': {},
            'total_feedback': len(self.feedback_history)
        }

        for name, data in self.bandits.items():
            stats['bandits'][name] = data['bandit'].get_statistics()

        for name, data in self.contextual_bandits.items():
            stats['contextual_bandits'][name] = data['bandit'].get_statistics()

        for name, data in self.q_learners.items():
            stats['q_learners'][name] = data['learner'].get_statistics()

        return stats

    def save_models(self, path: Path):
        """Save all models."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'bandits': self.bandits,
            'contextual_bandits': self.contextual_bandits,
            'q_learners': self.q_learners,
            'feedback_history': self.feedback_history
        }

        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def load_models(self, path: Path):
        """Load all models."""
        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.bandits = data['bandits']
        self.contextual_bandits = data['contextual_bandits']
        self.q_learners = data['q_learners']
        self.feedback_history = data['feedback_history']
