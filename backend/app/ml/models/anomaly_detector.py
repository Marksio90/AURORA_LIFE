"""
Anomaly Detection for Life Events and Metrics

Detects unusual patterns in:
- Energy levels
- Mood swings
- Sleep patterns
- Stress spikes
- Activity anomalies

Uses:
- Isolation Forest (unsupervised)
- Autoencoders (neural network based)
- Statistical methods (Z-score, IQR)
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pickle
from datetime import datetime, timedelta

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class Autoencoder(nn.Module):
    """
    Autoencoder for anomaly detection.

    Learns to compress and reconstruct normal patterns.
    High reconstruction error = anomaly.
    """

    def __init__(self, input_dim: int, encoding_dim: int = 8):
        super(Autoencoder, self).__init__()

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, encoding_dim),
            nn.ReLU()
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
            nn.Sigmoid()
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AnomalyDetector:
    """
    Multi-method anomaly detection for life metrics.

    Combines:
    1. Isolation Forest - unsupervised tree-based
    2. Autoencoder - neural reconstruction error
    3. Statistical - Z-score and IQR methods
    """

    def __init__(self, method: str = "isolation_forest", contamination: float = 0.05):
        """
        Initialize anomaly detector.

        Args:
            method: 'isolation_forest', 'autoencoder', 'statistical', or 'ensemble'
            contamination: Expected proportion of anomalies (0.01 = 1%)
        """
        self.method = method
        self.contamination = contamination

        self.isolation_forest: Optional[IsolationForest] = None
        self.autoencoder: Optional[Autoencoder] = None
        self.scaler: Optional[StandardScaler] = None

        self.threshold_reconstruction_error = None
        self.statistical_mean = None
        self.statistical_std = None
        self.iqr_bounds = None

        self.feature_names = []

    def train_isolation_forest(self, X: np.ndarray, feature_names: List[str] = None) -> Dict[str, Any]:
        """
        Train Isolation Forest detector.

        Args:
            X: Feature matrix (n_samples, n_features)
            feature_names: Names of features

        Returns:
            Training metrics
        """
        if feature_names:
            self.feature_names = feature_names

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1
        )

        self.isolation_forest.fit(X_scaled)

        # Get anomaly scores
        scores = self.isolation_forest.score_samples(X_scaled)
        predictions = self.isolation_forest.predict(X_scaled)

        n_anomalies = np.sum(predictions == -1)
        anomaly_rate = n_anomalies / len(X)

        return {
            'method': 'isolation_forest',
            'n_samples': len(X),
            'n_anomalies_detected': int(n_anomalies),
            'anomaly_rate': float(anomaly_rate),
            'contamination': self.contamination,
            'score_range': {
                'min': float(scores.min()),
                'max': float(scores.max()),
                'mean': float(scores.mean())
            }
        }

    def train_autoencoder(
        self,
        X: np.ndarray,
        feature_names: List[str] = None,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ) -> Dict[str, Any]:
        """
        Train Autoencoder detector.

        Args:
            X: Feature matrix
            feature_names: Names of features
            epochs: Training epochs
            batch_size: Batch size
            learning_rate: Learning rate

        Returns:
            Training metrics
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not installed")

        if feature_names:
            self.feature_names = feature_names

        # Scale features to [0, 1]
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Normalize to [0, 1] for sigmoid output
        X_min = X_scaled.min(axis=0)
        X_max = X_scaled.max(axis=0)
        X_normalized = (X_scaled - X_min) / (X_max - X_min + 1e-10)

        # Convert to tensor
        X_tensor = torch.FloatTensor(X_normalized)

        # Initialize autoencoder
        input_dim = X.shape[1]
        encoding_dim = max(2, input_dim // 4)

        self.autoencoder = Autoencoder(input_dim=input_dim, encoding_dim=encoding_dim)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.autoencoder.parameters(), lr=learning_rate)

        # Training loop
        losses = []

        for epoch in range(epochs):
            # Shuffle data
            indices = torch.randperm(len(X_tensor))

            epoch_loss = 0.0
            n_batches = 0

            for i in range(0, len(indices), batch_size):
                batch_indices = indices[i:i+batch_size]
                batch_X = X_tensor[batch_indices]

                # Forward pass
                reconstructed = self.autoencoder(batch_X)
                loss = criterion(reconstructed, batch_X)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            avg_loss = epoch_loss / n_batches
            losses.append(avg_loss)

        # Calculate reconstruction errors
        self.autoencoder.eval()
        with torch.no_grad():
            reconstructed = self.autoencoder(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1).numpy()

        # Set threshold at percentile based on contamination
        percentile = 100 * (1 - self.contamination)
        self.threshold_reconstruction_error = np.percentile(reconstruction_errors, percentile)

        n_anomalies = np.sum(reconstruction_errors > self.threshold_reconstruction_error)

        return {
            'method': 'autoencoder',
            'n_samples': len(X),
            'n_anomalies_detected': int(n_anomalies),
            'anomaly_rate': float(n_anomalies / len(X)),
            'reconstruction_error_threshold': float(self.threshold_reconstruction_error),
            'final_loss': float(losses[-1]),
            'epochs_trained': epochs
        }

    def train_statistical(self, X: np.ndarray, feature_names: List[str] = None) -> Dict[str, Any]:
        """
        Train statistical anomaly detection.

        Uses Z-score and IQR methods.

        Args:
            X: Feature matrix
            feature_names: Names of features

        Returns:
            Training metrics
        """
        if feature_names:
            self.feature_names = feature_names

        # Calculate statistics
        self.statistical_mean = np.mean(X, axis=0)
        self.statistical_std = np.std(X, axis=0)

        # IQR method
        q1 = np.percentile(X, 25, axis=0)
        q3 = np.percentile(X, 75, axis=0)
        iqr = q3 - q1

        self.iqr_bounds = {
            'lower': q1 - 1.5 * iqr,
            'upper': q3 + 1.5 * iqr
        }

        # Detect anomalies using Z-score (threshold = 3)
        z_scores = np.abs((X - self.statistical_mean) / (self.statistical_std + 1e-10))
        z_anomalies = np.any(z_scores > 3, axis=1)

        # Detect anomalies using IQR
        iqr_anomalies = np.any(
            (X < self.iqr_bounds['lower']) | (X > self.iqr_bounds['upper']),
            axis=1
        )

        # Combine both methods
        combined_anomalies = z_anomalies | iqr_anomalies

        n_anomalies = np.sum(combined_anomalies)

        return {
            'method': 'statistical',
            'n_samples': len(X),
            'n_anomalies_z_score': int(np.sum(z_anomalies)),
            'n_anomalies_iqr': int(np.sum(iqr_anomalies)),
            'n_anomalies_combined': int(n_anomalies),
            'anomaly_rate': float(n_anomalies / len(X))
        }

    def detect(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Detect anomalies in new data.

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Anomaly predictions and scores
        """
        if self.method == "isolation_forest":
            return self._detect_isolation_forest(X)

        elif self.method == "autoencoder":
            return self._detect_autoencoder(X)

        elif self.method == "statistical":
            return self._detect_statistical(X)

        elif self.method == "ensemble":
            # Combine all methods
            if_result = self._detect_isolation_forest(X)
            ae_result = self._detect_autoencoder(X)
            stat_result = self._detect_statistical(X)

            # Voting: if 2+ methods detect anomaly, it's an anomaly
            anomalies = (
                if_result['anomalies'] +
                ae_result['anomalies'] +
                stat_result['anomalies']
            ) >= 2

            return {
                'anomalies': anomalies.tolist(),
                'anomaly_indices': np.where(anomalies)[0].tolist(),
                'method': 'ensemble',
                'individual_results': {
                    'isolation_forest': if_result,
                    'autoencoder': ae_result,
                    'statistical': stat_result
                }
            }
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _detect_isolation_forest(self, X: np.ndarray) -> Dict[str, Any]:
        """Detect using Isolation Forest."""
        if self.isolation_forest is None:
            raise ValueError("Isolation Forest not trained")

        X_scaled = self.scaler.transform(X)

        predictions = self.isolation_forest.predict(X_scaled)
        scores = self.isolation_forest.score_samples(X_scaled)

        anomalies = predictions == -1

        # Get top anomalous features for each anomaly
        anomaly_details = []
        for idx in np.where(anomalies)[0]:
            anomaly_details.append({
                'index': int(idx),
                'anomaly_score': float(scores[idx]),
                'features': self.feature_names if self.feature_names else None
            })

        return {
            'anomalies': anomalies.tolist(),
            'anomaly_indices': np.where(anomalies)[0].tolist(),
            'scores': scores.tolist(),
            'anomaly_details': anomaly_details,
            'method': 'isolation_forest'
        }

    def _detect_autoencoder(self, X: np.ndarray) -> Dict[str, Any]:
        """Detect using Autoencoder."""
        if self.autoencoder is None:
            raise ValueError("Autoencoder not trained")

        X_scaled = self.scaler.transform(X)

        # Normalize
        X_min = X_scaled.min(axis=0)
        X_max = X_scaled.max(axis=0)
        X_normalized = (X_scaled - X_min) / (X_max - X_min + 1e-10)

        X_tensor = torch.FloatTensor(X_normalized)

        # Reconstruct
        self.autoencoder.eval()
        with torch.no_grad():
            reconstructed = self.autoencoder(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1).numpy()

        anomalies = reconstruction_errors > self.threshold_reconstruction_error

        anomaly_details = []
        for idx in np.where(anomalies)[0]:
            anomaly_details.append({
                'index': int(idx),
                'reconstruction_error': float(reconstruction_errors[idx]),
                'threshold': float(self.threshold_reconstruction_error)
            })

        return {
            'anomalies': anomalies.tolist(),
            'anomaly_indices': np.where(anomalies)[0].tolist(),
            'reconstruction_errors': reconstruction_errors.tolist(),
            'threshold': float(self.threshold_reconstruction_error),
            'anomaly_details': anomaly_details,
            'method': 'autoencoder'
        }

    def _detect_statistical(self, X: np.ndarray) -> Dict[str, Any]:
        """Detect using statistical methods."""
        if self.statistical_mean is None:
            raise ValueError("Statistical model not trained")

        # Z-score method
        z_scores = np.abs((X - self.statistical_mean) / (self.statistical_std + 1e-10))
        z_anomalies = np.any(z_scores > 3, axis=1)

        # IQR method
        iqr_anomalies = np.any(
            (X < self.iqr_bounds['lower']) | (X > self.iqr_bounds['upper']),
            axis=1
        )

        # Combined
        anomalies = z_anomalies | iqr_anomalies

        anomaly_details = []
        for idx in np.where(anomalies)[0]:
            anomalous_features = []

            # Find which features are anomalous
            for feat_idx in range(X.shape[1]):
                z_score = z_scores[idx, feat_idx]
                value = X[idx, feat_idx]

                if z_score > 3 or value < self.iqr_bounds['lower'][feat_idx] or value > self.iqr_bounds['upper'][feat_idx]:
                    feat_name = self.feature_names[feat_idx] if self.feature_names else f"feature_{feat_idx}"
                    anomalous_features.append({
                        'feature': feat_name,
                        'value': float(value),
                        'z_score': float(z_score),
                        'expected_range': [
                            float(self.iqr_bounds['lower'][feat_idx]),
                            float(self.iqr_bounds['upper'][feat_idx])
                        ]
                    })

            anomaly_details.append({
                'index': int(idx),
                'anomalous_features': anomalous_features
            })

        return {
            'anomalies': anomalies.tolist(),
            'anomaly_indices': np.where(anomalies)[0].tolist(),
            'z_scores': z_scores.tolist(),
            'anomaly_details': anomaly_details,
            'method': 'statistical'
        }

    def explain_anomaly(self, X: np.ndarray, index: int) -> Dict[str, Any]:
        """
        Explain why a specific data point is anomalous.

        Args:
            X: Feature matrix
            index: Index of the anomaly

        Returns:
            Detailed explanation
        """
        if index >= len(X):
            raise ValueError(f"Index {index} out of range")

        sample = X[index:index+1]

        explanation = {
            'index': index,
            'sample_values': sample[0].tolist(),
            'feature_names': self.feature_names if self.feature_names else [f"feature_{i}" for i in range(X.shape[1])],
            'anomaly_reasons': []
        }

        # Statistical explanation
        if self.statistical_mean is not None:
            z_scores = np.abs((sample - self.statistical_mean) / (self.statistical_std + 1e-10))

            for feat_idx in range(X.shape[1]):
                z_score = z_scores[0, feat_idx]
                if z_score > 3:
                    feat_name = explanation['feature_names'][feat_idx]
                    explanation['anomaly_reasons'].append({
                        'feature': feat_name,
                        'reason': 'Statistical outlier (Z-score > 3)',
                        'z_score': float(z_score),
                        'value': float(sample[0, feat_idx]),
                        'expected_mean': float(self.statistical_mean[feat_idx]),
                        'expected_std': float(self.statistical_std[feat_idx])
                    })

        # Autoencoder explanation
        if self.autoencoder is not None:
            X_scaled = self.scaler.transform(sample)
            X_min = X_scaled.min(axis=0)
            X_max = X_scaled.max(axis=0)
            X_normalized = (X_scaled - X_min) / (X_max - X_min + 1e-10)
            X_tensor = torch.FloatTensor(X_normalized)

            self.autoencoder.eval()
            with torch.no_grad():
                reconstructed = self.autoencoder(X_tensor)
                reconstruction_error = torch.mean((X_tensor - reconstructed) ** 2).item()

            if reconstruction_error > self.threshold_reconstruction_error:
                explanation['anomaly_reasons'].append({
                    'reason': 'High reconstruction error (unusual pattern)',
                    'reconstruction_error': float(reconstruction_error),
                    'threshold': float(self.threshold_reconstruction_error)
                })

        return explanation

    def save_model(self, path: Path):
        """Save trained models."""
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'method': self.method,
            'contamination': self.contamination,
            'feature_names': self.feature_names,
            'isolation_forest': self.isolation_forest,
            'scaler': self.scaler,
            'threshold_reconstruction_error': self.threshold_reconstruction_error,
            'statistical_mean': self.statistical_mean,
            'statistical_std': self.statistical_std,
            'iqr_bounds': self.iqr_bounds
        }

        # Save main model data
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

        # Save autoencoder separately if exists
        if self.autoencoder:
            torch.save(self.autoencoder.state_dict(), path.with_suffix('.ae.pt'))

    def load_model(self, path: Path):
        """Load trained models."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        self.method = model_data['method']
        self.contamination = model_data['contamination']
        self.feature_names = model_data['feature_names']
        self.isolation_forest = model_data['isolation_forest']
        self.scaler = model_data['scaler']
        self.threshold_reconstruction_error = model_data['threshold_reconstruction_error']
        self.statistical_mean = model_data['statistical_mean']
        self.statistical_std = model_data['statistical_std']
        self.iqr_bounds = model_data['iqr_bounds']

        # Load autoencoder if exists
        ae_path = path.with_suffix('.ae.pt')
        if ae_path.exists() and TORCH_AVAILABLE:
            # Reconstruct autoencoder (need input_dim from scaler)
            if self.scaler is not None:
                input_dim = self.scaler.mean_.shape[0]
                encoding_dim = max(2, input_dim // 4)

                self.autoencoder = Autoencoder(input_dim=input_dim, encoding_dim=encoding_dim)
                self.autoencoder.load_state_dict(torch.load(ae_path))
                self.autoencoder.eval()
