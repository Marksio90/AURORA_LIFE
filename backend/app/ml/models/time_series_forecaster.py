"""
Advanced Time Series Forecasting using Prophet and LSTM

Multi-horizon predictions for energy, mood, and productivity.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import pickle

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class LSTMForecaster(nn.Module):
    """LSTM Neural Network for time series forecasting."""

    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(LSTMForecaster, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )

        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        """Forward pass through LSTM."""
        # x shape: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)

        # Use last timestep output
        last_output = lstm_out[:, -1, :]

        # Final prediction
        prediction = self.fc(last_output)
        return prediction


class TimeSeriesForecaster:
    """
    Advanced time series forecasting for life metrics.

    Combines:
    - Prophet: Trend, seasonality, holidays
    - LSTM: Complex patterns, non-linear relationships

    Supports multi-horizon predictions:
    - 1 day ahead
    - 7 days ahead
    - 30 days ahead
    """

    def __init__(self, metric_name: str = "energy", model_type: str = "prophet"):
        """
        Initialize forecaster.

        Args:
            metric_name: Name of metric to forecast (energy, mood, productivity)
            model_type: 'prophet' or 'lstm' or 'ensemble'
        """
        self.metric_name = metric_name
        self.model_type = model_type

        self.prophet_model: Optional[Prophet] = None
        self.lstm_model: Optional[LSTMForecaster] = None

        self.scaler_mean = 0.0
        self.scaler_std = 1.0

    def prepare_data_for_prophet(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for Prophet.

        Prophet expects columns: 'ds' (date), 'y' (value)

        Args:
            df: DataFrame with 'timestamp' and metric columns

        Returns:
            DataFrame ready for Prophet
        """
        if self.metric_name not in df.columns:
            raise ValueError(f"Metric '{self.metric_name}' not found in dataframe")

        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df['timestamp']),
            'y': df[self.metric_name].astype(float)
        })

        # Remove any NaN values
        prophet_df = prophet_df.dropna()

        return prophet_df

    def prepare_data_for_lstm(
        self,
        values: np.ndarray,
        sequence_length: int = 14
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM.

        Args:
            values: Array of metric values over time
            sequence_length: Number of past timesteps to use

        Returns:
            X (sequences), y (targets)
        """
        # Normalize data
        self.scaler_mean = np.mean(values)
        self.scaler_std = np.std(values)

        if self.scaler_std == 0:
            self.scaler_std = 1.0

        normalized = (values - self.scaler_mean) / self.scaler_std

        # Create sequences
        X, y = [], []

        for i in range(len(normalized) - sequence_length):
            X.append(normalized[i:i + sequence_length])
            y.append(normalized[i + sequence_length])

        return np.array(X), np.array(y)

    def train_prophet(self, df: pd.DataFrame, **prophet_kwargs) -> Dict[str, Any]:
        """
        Train Prophet model.

        Args:
            df: DataFrame with timestamp and metric values
            **prophet_kwargs: Additional Prophet parameters

        Returns:
            Training metrics
        """
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet not installed. Install with: pip install prophet")

        prophet_df = self.prepare_data_for_prophet(df)

        # Initialize Prophet with sensible defaults
        self.prophet_model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True if len(prophet_df) > 365 else False,
            changepoint_prior_scale=0.05,  # Flexibility of trend
            seasonality_prior_scale=10.0,  # Strength of seasonality
            **prophet_kwargs
        )

        # Train model
        self.prophet_model.fit(prophet_df)

        # Evaluate on last 20% of data
        split_idx = int(len(prophet_df) * 0.8)
        train_df = prophet_df[:split_idx]
        test_df = prophet_df[split_idx:]

        if len(test_df) > 0:
            # Make predictions on test set
            forecast = self.prophet_model.predict(test_df[['ds']])

            # Calculate metrics
            y_true = test_df['y'].values
            y_pred = forecast['yhat'].values

            mae = np.mean(np.abs(y_true - y_pred))
            rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
            mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100

            metrics = {
                'mae': float(mae),
                'rmse': float(rmse),
                'mape': float(mape),
                'n_samples': len(prophet_df),
                'model_type': 'prophet'
            }
        else:
            metrics = {
                'n_samples': len(prophet_df),
                'model_type': 'prophet',
                'note': 'Insufficient data for validation'
            }

        return metrics

    def train_lstm(
        self,
        values: np.ndarray,
        sequence_length: int = 14,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ) -> Dict[str, Any]:
        """
        Train LSTM model.

        Args:
            values: Time series values
            sequence_length: Lookback window
            epochs: Training epochs
            batch_size: Batch size
            learning_rate: Learning rate

        Returns:
            Training metrics
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not installed. Install with: pip install torch")

        # Prepare data
        X, y = self.prepare_data_for_lstm(values, sequence_length)

        if len(X) < 10:
            return {
                'error': 'Insufficient data for LSTM training',
                'n_samples': len(X),
                'required': 10
            }

        # Split train/val
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Convert to PyTorch tensors
        X_train = torch.FloatTensor(X_train).unsqueeze(-1)  # Add feature dimension
        y_train = torch.FloatTensor(y_train).unsqueeze(-1)
        X_val = torch.FloatTensor(X_val).unsqueeze(-1)
        y_val = torch.FloatTensor(y_val).unsqueeze(-1)

        # Initialize model
        self.lstm_model = LSTMForecaster(input_size=1, hidden_size=64, num_layers=2)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.lstm_model.parameters(), lr=learning_rate)

        # Training loop
        train_losses = []
        val_losses = []

        for epoch in range(epochs):
            # Training
            self.lstm_model.train()

            # Batch training
            for i in range(0, len(X_train), batch_size):
                batch_X = X_train[i:i+batch_size]
                batch_y = y_train[i:i+batch_size]

                # Forward pass
                outputs = self.lstm_model(batch_X)
                loss = criterion(outputs, batch_y)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # Validation
            self.lstm_model.eval()
            with torch.no_grad():
                val_outputs = self.lstm_model(X_val)
                val_loss = criterion(val_outputs, y_val)

            train_losses.append(loss.item())
            val_losses.append(val_loss.item())

            # Early stopping
            if epoch > 10 and val_loss > min(val_losses[-10:]) * 1.1:
                break

        # Calculate final metrics
        self.lstm_model.eval()
        with torch.no_grad():
            val_predictions = self.lstm_model(X_val).numpy()

        # Denormalize
        val_predictions = val_predictions * self.scaler_std + self.scaler_mean
        y_val_denorm = y_val.numpy() * self.scaler_std + self.scaler_mean

        mae = np.mean(np.abs(y_val_denorm - val_predictions))
        rmse = np.sqrt(np.mean((y_val_denorm - val_predictions) ** 2))

        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'epochs_trained': epoch + 1,
            'final_train_loss': float(train_losses[-1]),
            'final_val_loss': float(val_losses[-1]),
            'n_samples': len(X),
            'model_type': 'lstm'
        }

    def predict(
        self,
        df: pd.DataFrame = None,
        values: np.ndarray = None,
        horizon: int = 7
    ) -> Dict[str, Any]:
        """
        Make predictions for future time periods.

        Args:
            df: DataFrame for Prophet (with timestamp column)
            values: Array for LSTM
            horizon: Number of days to forecast

        Returns:
            Predictions with confidence intervals
        """
        if self.model_type == "prophet" and self.prophet_model is not None:
            return self._predict_prophet(df, horizon)

        elif self.model_type == "lstm" and self.lstm_model is not None:
            return self._predict_lstm(values, horizon)

        elif self.model_type == "ensemble":
            # Ensemble both models
            prophet_pred = self._predict_prophet(df, horizon)
            lstm_pred = self._predict_lstm(values, horizon)

            # Average predictions
            ensemble_predictions = [
                (p + l) / 2
                for p, l in zip(prophet_pred['predictions'], lstm_pred['predictions'])
            ]

            return {
                'predictions': ensemble_predictions,
                'dates': prophet_pred['dates'],
                'confidence_intervals': prophet_pred['confidence_intervals'],
                'model_type': 'ensemble',
                'prophet_weight': 0.5,
                'lstm_weight': 0.5
            }
        else:
            return {
                'error': 'Model not trained',
                'model_type': self.model_type
            }

    def _predict_prophet(self, df: pd.DataFrame, horizon: int) -> Dict[str, Any]:
        """Make predictions using Prophet."""
        if self.prophet_model is None:
            raise ValueError("Prophet model not trained")

        # Create future dataframe
        future = self.prophet_model.make_future_dataframe(periods=horizon, freq='D')

        # Make predictions
        forecast = self.prophet_model.predict(future)

        # Extract future predictions only
        forecast_future = forecast.tail(horizon)

        return {
            'predictions': forecast_future['yhat'].tolist(),
            'dates': forecast_future['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'confidence_intervals': [
                {'lower': row['yhat_lower'], 'upper': row['yhat_upper']}
                for _, row in forecast_future.iterrows()
            ],
            'trend': forecast_future['trend'].tolist(),
            'model_type': 'prophet'
        }

    def _predict_lstm(self, values: np.ndarray, horizon: int) -> Dict[str, Any]:
        """Make predictions using LSTM."""
        if self.lstm_model is None:
            raise ValueError("LSTM model not trained")

        self.lstm_model.eval()

        # Start with last sequence from training data
        current_sequence = values[-14:]  # Last 14 days

        # Normalize
        current_sequence = (current_sequence - self.scaler_mean) / self.scaler_std

        predictions = []

        with torch.no_grad():
            for _ in range(horizon):
                # Prepare input
                X = torch.FloatTensor(current_sequence).unsqueeze(0).unsqueeze(-1)

                # Predict next value
                pred = self.lstm_model(X)
                pred_value = pred.item()

                predictions.append(pred_value)

                # Update sequence (rolling window)
                current_sequence = np.append(current_sequence[1:], pred_value)

        # Denormalize predictions
        predictions = np.array(predictions) * self.scaler_std + self.scaler_mean

        # Generate future dates
        last_date = datetime.now()
        future_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
                       for i in range(horizon)]

        return {
            'predictions': predictions.tolist(),
            'dates': future_dates,
            'confidence_intervals': None,  # LSTM doesn't provide confidence intervals by default
            'model_type': 'lstm'
        }

    def save_model(self, path: Path):
        """Save trained model to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'metric_name': self.metric_name,
            'model_type': self.model_type,
            'scaler_mean': self.scaler_mean,
            'scaler_std': self.scaler_std
        }

        if self.prophet_model:
            # Prophet uses its own serialization
            import json
            with open(path.with_suffix('.prophet.json'), 'w') as f:
                json.dump(self.prophet_model.to_json(), f)

        if self.lstm_model:
            # Save PyTorch model
            torch.save(self.lstm_model.state_dict(), path.with_suffix('.lstm.pt'))

        # Save metadata
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

    def load_model(self, path: Path):
        """Load trained model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        self.metric_name = model_data['metric_name']
        self.model_type = model_data['model_type']
        self.scaler_mean = model_data['scaler_mean']
        self.scaler_std = model_data['scaler_std']

        # Load Prophet if exists
        prophet_path = path.with_suffix('.prophet.json')
        if prophet_path.exists() and PROPHET_AVAILABLE:
            import json
            with open(prophet_path, 'r') as f:
                self.prophet_model = Prophet.from_json(json.load(f))

        # Load LSTM if exists
        lstm_path = path.with_suffix('.lstm.pt')
        if lstm_path.exists() and TORCH_AVAILABLE:
            self.lstm_model = LSTMForecaster(input_size=1)
            self.lstm_model.load_state_dict(torch.load(lstm_path))
            self.lstm_model.eval()
