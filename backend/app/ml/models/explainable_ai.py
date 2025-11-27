"""
Explainable AI (XAI) - Making ML Predictions Transparent

Provides explanations for model predictions using:
- SHAP (SHapley Additive exPlanations)
- LIME (Local Interpretable Model-agnostic Explanations)
- Feature Attribution
- Counterfactual Explanations
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class ExplainableAI:
    """
    Wrapper for making any ML model explainable.

    Provides:
    1. Feature importance (global explanations)
    2. Individual prediction explanations (local explanations)
    3. Counterfactual analysis ("What if?" scenarios)
    4. Feature interactions
    """

    def __init__(self, model, feature_names: List[str], background_data: np.ndarray = None):
        """
        Initialize Explainable AI wrapper.

        Args:
            model: Trained ML model (XGBoost, LightGBM, sklearn, etc.)
            feature_names: Names of input features
            background_data: Representative sample for SHAP (optional)
        """
        self.model = model
        self.feature_names = feature_names
        self.background_data = background_data

        self.explainer = None
        self.shap_values = None

        self._initialize_explainer()

    def _initialize_explainer(self):
        """Initialize appropriate SHAP explainer based on model type."""
        if not SHAP_AVAILABLE:
            print("Warning: SHAP not available. Install with: pip install shap")
            return

        try:
            # Try TreeExplainer for tree-based models (XGBoost, LightGBM, RandomForest)
            if hasattr(self.model, 'get_booster') or hasattr(self.model, 'booster_'):
                # XGBoost or LightGBM
                self.explainer = shap.TreeExplainer(self.model)

            elif hasattr(self.model, 'estimators_'):
                # Random Forest or Gradient Boosting
                self.explainer = shap.TreeExplainer(self.model)

            else:
                # Fallback to KernelExplainer (model-agnostic but slower)
                if self.background_data is not None:
                    self.explainer = shap.KernelExplainer(
                        self.model.predict,
                        self.background_data[:100]  # Use subset for speed
                    )
                else:
                    print("Warning: Background data needed for KernelExplainer")

        except Exception as e:
            print(f"Warning: Could not initialize SHAP explainer: {e}")

    def explain_prediction(self, X: np.ndarray, index: int = None) -> Dict[str, Any]:
        """
        Explain a single prediction or batch of predictions.

        Args:
            X: Input features (single sample or batch)
            index: If X is batch, which sample to explain (None = all)

        Returns:
            Detailed explanation with feature contributions
        """
        if not SHAP_AVAILABLE or self.explainer is None:
            return self._fallback_explanation(X, index)

        # Ensure X is 2D
        if len(X.shape) == 1:
            X = X.reshape(1, -1)

        # Get SHAP values
        try:
            shap_values = self.explainer.shap_values(X)

            # Handle multi-class case (take first class or average)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            # If specific index requested
            if index is not None:
                shap_values = shap_values[index:index+1]
                X = X[index:index+1]

        except Exception as e:
            print(f"Error calculating SHAP values: {e}")
            return self._fallback_explanation(X, index)

        # Build explanation
        explanations = []

        for i in range(len(X)):
            sample_shap = shap_values[i] if len(shap_values.shape) > 1 else shap_values
            sample_features = X[i]

            # Sort features by absolute SHAP value
            feature_contributions = [
                {
                    'feature': self.feature_names[j],
                    'value': float(sample_features[j]),
                    'shap_value': float(sample_shap[j]),
                    'impact': 'positive' if sample_shap[j] > 0 else 'negative',
                    'importance': abs(float(sample_shap[j]))
                }
                for j in range(len(self.feature_names))
            ]

            # Sort by importance
            feature_contributions.sort(key=lambda x: x['importance'], reverse=True)

            # Get prediction
            prediction = self.model.predict(X[i:i+1])[0]

            # Base value (expected value)
            base_value = self.explainer.expected_value
            if isinstance(base_value, np.ndarray):
                base_value = base_value[0]

            explanation = {
                'prediction': float(prediction),
                'base_value': float(base_value),
                'feature_contributions': feature_contributions,
                'top_positive_factors': [
                    fc for fc in feature_contributions if fc['impact'] == 'positive'
                ][:3],
                'top_negative_factors': [
                    fc for fc in feature_contributions if fc['impact'] == 'negative'
                ][:3],
                'explanation_text': self._generate_explanation_text(
                    prediction, base_value, feature_contributions
                )
            }

            explanations.append(explanation)

        return explanations[0] if len(explanations) == 1 else explanations

    def _generate_explanation_text(
        self,
        prediction: float,
        base_value: float,
        contributions: List[Dict]
    ) -> str:
        """Generate human-readable explanation."""

        # Get top 3 most important features
        top_features = contributions[:3]

        explanation_parts = []

        if prediction > base_value:
            explanation_parts.append(
                f"Your predicted value is {prediction:.2f}, which is higher than average ({base_value:.2f})."
            )
        else:
            explanation_parts.append(
                f"Your predicted value is {prediction:.2f}, which is lower than average ({base_value:.2f})."
            )

        explanation_parts.append("\nKey factors:")

        for i, feature in enumerate(top_features, 1):
            impact_word = "increases" if feature['impact'] == 'positive' else "decreases"
            explanation_parts.append(
                f"{i}. {feature['feature']} (value: {feature['value']:.2f}) "
                f"{impact_word} your score by {abs(feature['shap_value']):.2f}"
            )

        return " ".join(explanation_parts)

    def _fallback_explanation(self, X: np.ndarray, index: int = None) -> Dict[str, Any]:
        """Fallback explanation when SHAP not available."""

        if len(X.shape) == 1:
            X = X.reshape(1, -1)

        if index is not None:
            X = X[index:index+1]

        # Use basic feature importance if available
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_

            feature_contributions = [
                {
                    'feature': self.feature_names[i],
                    'value': float(X[0, i]),
                    'global_importance': float(importances[i])
                }
                for i in range(len(self.feature_names))
            ]

            feature_contributions.sort(key=lambda x: x['global_importance'], reverse=True)

            return {
                'prediction': float(self.model.predict(X)[0]),
                'method': 'feature_importance',
                'feature_contributions': feature_contributions[:5],
                'note': 'Install shap for detailed explanations: pip install shap'
            }

        return {
            'prediction': float(self.model.predict(X)[0]),
            'method': 'basic',
            'note': 'Model does not support explanations'
        }

    def global_feature_importance(self, X: np.ndarray = None) -> Dict[str, Any]:
        """
        Get global feature importance across all predictions.

        Args:
            X: Optional dataset to calculate importance on

        Returns:
            Global feature importance
        """
        if not SHAP_AVAILABLE or self.explainer is None:
            # Fallback to model's built-in feature importance
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_

                importance_dict = {
                    self.feature_names[i]: float(importances[i])
                    for i in range(len(self.feature_names))
                }

                # Sort by importance
                sorted_importance = sorted(
                    importance_dict.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                return {
                    'method': 'model_feature_importance',
                    'importances': dict(sorted_importance),
                    'top_features': sorted_importance[:10]
                }

            return {'error': 'Feature importance not available'}

        # Use SHAP for global importance
        if X is None:
            if self.background_data is None:
                return {'error': 'No data provided for global importance'}
            X = self.background_data

        try:
            shap_values = self.explainer.shap_values(X)

            # Handle multi-class
            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            # Calculate mean absolute SHAP value for each feature
            mean_shap = np.mean(np.abs(shap_values), axis=0)

            importance_dict = {
                self.feature_names[i]: float(mean_shap[i])
                for i in range(len(self.feature_names))
            }

            sorted_importance = sorted(
                importance_dict.items(),
                key=lambda x: x[1],
                reverse=True
            )

            return {
                'method': 'shap_global',
                'importances': dict(sorted_importance),
                'top_features': sorted_importance[:10],
                'explanation': 'Features ranked by average impact on predictions'
            }

        except Exception as e:
            return {'error': f'Failed to calculate global importance: {e}'}

    def counterfactual_analysis(
        self,
        X: np.ndarray,
        target_change: float,
        feature_constraints: Dict[str, tuple] = None
    ) -> Dict[str, Any]:
        """
        "What if?" analysis - how to change input to achieve target.

        Args:
            X: Current feature values
            target_change: Desired change in prediction
            feature_constraints: Dict of {feature_name: (min, max)} constraints

        Returns:
            Suggested feature changes
        """
        if len(X.shape) == 1:
            X = X.reshape(1, -1)

        current_prediction = self.model.predict(X)[0]
        target_prediction = current_prediction + target_change

        # Simple greedy approach: modify most important features
        suggestions = []

        if not SHAP_AVAILABLE or self.explainer is None:
            return {
                'current_prediction': float(current_prediction),
                'target_prediction': float(target_prediction),
                'suggestions': 'Install SHAP for counterfactual analysis'
            }

        try:
            # Get SHAP values for current input
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            # Sort features by absolute SHAP value
            feature_impacts = [
                (i, self.feature_names[i], shap_values[0][i])
                for i in range(len(self.feature_names))
            ]
            feature_impacts.sort(key=lambda x: abs(x[2]), reverse=True)

            # Suggest changes to top features
            for i, feat_name, shap_val in feature_impacts[:5]:
                current_value = X[0, i]

                # Determine direction of change needed
                if target_change > 0 and shap_val > 0:
                    # Need to increase prediction, and this feature helps when increased
                    suggested_change = "+10%"
                    suggested_value = current_value * 1.1

                elif target_change > 0 and shap_val < 0:
                    # Need to increase prediction, but this feature hurts
                    suggested_change = "-10%"
                    suggested_value = current_value * 0.9

                elif target_change < 0 and shap_val > 0:
                    # Need to decrease prediction, and this feature increases it
                    suggested_change = "-10%"
                    suggested_value = current_value * 0.9

                else:
                    # Need to decrease, this feature decreases
                    suggested_change = "+10%"
                    suggested_value = current_value * 1.1

                # Apply constraints if provided
                if feature_constraints and feat_name in feature_constraints:
                    min_val, max_val = feature_constraints[feat_name]
                    suggested_value = np.clip(suggested_value, min_val, max_val)

                suggestions.append({
                    'feature': feat_name,
                    'current_value': float(current_value),
                    'suggested_value': float(suggested_value),
                    'change': suggested_change,
                    'expected_impact': float(abs(shap_val)),
                    'rationale': self._explain_counterfactual(
                        feat_name, current_value, suggested_value, shap_val, target_change
                    )
                })

            return {
                'current_prediction': float(current_prediction),
                'target_prediction': float(target_prediction),
                'change_needed': float(target_change),
                'suggestions': suggestions,
                'note': 'These are approximate suggestions based on current patterns'
            }

        except Exception as e:
            return {
                'current_prediction': float(current_prediction),
                'target_prediction': float(target_prediction),
                'error': f'Failed to generate counterfactuals: {e}'
            }

    def _explain_counterfactual(
        self,
        feature_name: str,
        current: float,
        suggested: float,
        shap_value: float,
        target_change: float
    ) -> str:
        """Generate explanation for counterfactual suggestion."""

        direction = "increase" if suggested > current else "decrease"
        impact = "increases" if shap_value > 0 else "decreases"

        return (
            f"If you {direction} {feature_name} from {current:.2f} to {suggested:.2f}, "
            f"it typically {impact} your score. "
            f"This change could help you reach your target."
        )

    def feature_interactions(self, X: np.ndarray, top_n: int = 10) -> Dict[str, Any]:
        """
        Analyze feature interactions.

        Args:
            X: Input data
            top_n: Number of top interactions to return

        Returns:
            Feature interaction strengths
        """
        if not SHAP_AVAILABLE or self.explainer is None:
            return {'error': 'SHAP not available for interaction analysis'}

        try:
            # Calculate SHAP interaction values
            shap_interaction_values = self.explainer.shap_interaction_values(X)

            # Sum absolute interaction values across samples
            if len(shap_interaction_values.shape) == 3:
                interaction_strengths = np.mean(np.abs(shap_interaction_values), axis=0)
            else:
                return {'error': 'Interaction values not available for this model'}

            # Find top interactions
            interactions = []

            for i in range(len(self.feature_names)):
                for j in range(i+1, len(self.feature_names)):
                    strength = interaction_strengths[i, j]

                    interactions.append({
                        'feature_1': self.feature_names[i],
                        'feature_2': self.feature_names[j],
                        'interaction_strength': float(strength)
                    })

            # Sort by strength
            interactions.sort(key=lambda x: x['interaction_strength'], reverse=True)

            return {
                'top_interactions': interactions[:top_n],
                'explanation': 'Features that work together to influence predictions'
            }

        except Exception as e:
            return {'error': f'Failed to calculate interactions: {e}'}
