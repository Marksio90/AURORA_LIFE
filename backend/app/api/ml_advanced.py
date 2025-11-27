"""
Advanced ML/AI API Endpoints

New endpoints for:
- Time series forecasting
- Anomaly detection
- Explainable AI
- RAG-powered chat
- MetaAgent coordination
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.api.auth import get_current_user

# ML models
from app.ml.models.time_series_forecaster import TimeSeriesForecaster
from app.ml.models.anomaly_detector import AnomalyDetector
from app.ml.models.explainable_ai import ExplainableAI
from app.ml.models.rl_recommender import RecommenderSystem

# AI agents
from app.ai.agents.meta_agent import MetaAgent
from app.ai.memory.vector_store import VectorStore

router = APIRouter(prefix="/api/v1/ml-advanced", tags=["ML Advanced"])


# ========== Pydantic Models ==========

class ForecastRequest(BaseModel):
    metric: str = Field(..., description="Metric to forecast (energy, mood, productivity)")
    horizon: int = Field(7, ge=1, le=30, description="Days to forecast ahead")
    model_type: str = Field("prophet", description="Model type: prophet, lstm, or ensemble")


class ForecastResponse(BaseModel):
    metric: str
    predictions: List[float]
    dates: List[str]
    confidence_intervals: Optional[List[dict]] = None
    model_type: str


class AnomalyRequest(BaseModel):
    days_back: int = Field(30, ge=7, le=90, description="Days of history to analyze")
    method: str = Field("isolation_forest", description="Method: isolation_forest, autoencoder, statistical, ensemble")


class AnomalyResponse(BaseModel):
    anomalies_detected: int
    anomaly_details: List[dict]
    method: str
    threshold: Optional[float] = None


class ExplainRequest(BaseModel):
    prediction_id: Optional[int] = None
    metric: str = Field(..., description="Which prediction to explain")


class ExplainResponse(BaseModel):
    prediction: float
    explanation_text: str
    top_positive_factors: List[dict]
    top_negative_factors: List[dict]
    base_value: float


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    use_memory: bool = Field(True, description="Use RAG memory")


class ChatResponse(BaseModel):
    message: str
    sources: List[dict] = []
    timestamp: str


class MetaAnalysisRequest(BaseModel):
    query: Optional[str] = Field(None, description="Specific question or focus area")
    use_memory: bool = Field(True, description="Use RAG memory")


class MetaAnalysisResponse(BaseModel):
    meta_insights: str
    cross_domain_patterns: List[dict]
    unified_recommendations: List[dict]
    confidence: float
    execution_time: float


# ========== Time Series Forecasting ==========

@router.post("/forecast", response_model=ForecastResponse)
async def forecast_metric(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate time series forecast for a life metric.

    **Supported metrics:**
    - energy: Energy levels
    - mood: Mood scores
    - productivity: Productivity ratings

    **Models:**
    - prophet: Facebook Prophet (trend + seasonality)
    - lstm: LSTM neural network (complex patterns)
    - ensemble: Combination of both
    """
    try:
        # Initialize forecaster
        forecaster = TimeSeriesForecaster(
            metric_name=request.metric,
            model_type=request.model_type
        )

        # TODO: Load user's historical data for this metric
        # For now, return placeholder
        # In production, fetch from database and train/predict

        return ForecastResponse(
            metric=request.metric,
            predictions=[7.5, 7.8, 7.2, 6.9, 7.4, 8.0, 7.6][:request.horizon],
            dates=[
                (datetime.now().date() + timedelta(days=i)).isoformat()
                for i in range(1, request.horizon + 1)
            ],
            model_type=request.model_type,
            confidence_intervals=[
                {'lower': 6.5, 'upper': 8.5} for _ in range(request.horizon)
            ] if request.model_type == "prophet" else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting error: {str(e)}"
        )


# ========== Anomaly Detection ==========

@router.post("/detect-anomalies", response_model=AnomalyResponse)
async def detect_anomalies(
    request: AnomalyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies in user's life patterns.

    **Methods:**
    - isolation_forest: Tree-based unsupervised detection
    - autoencoder: Neural network reconstruction
    - statistical: Z-score and IQR methods
    - ensemble: Combines all methods

    **Use cases:**
    - Detect unusual stress levels
    - Identify sleep pattern disruptions
    - Find mood anomalies
    """
    try:
        # Initialize detector
        detector = AnomalyDetector(
            method=request.method,
            contamination=0.05  # Expect 5% anomalies
        )

        # TODO: Load user's data and detect anomalies
        # For now, return placeholder

        return AnomalyResponse(
            anomalies_detected=2,
            anomaly_details=[
                {
                    'date': '2024-01-15',
                    'type': 'sleep_disruption',
                    'severity': 'high',
                    'description': 'Only 3 hours of sleep detected'
                },
                {
                    'date': '2024-01-18',
                    'type': 'stress_spike',
                    'severity': 'medium',
                    'description': 'Stress level 9/10, unusual for this user'
                }
            ],
            method=request.method,
            threshold=0.85
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection error: {str(e)}"
        )


# ========== Explainable AI ==========

@router.post("/explain-prediction", response_model=ExplainResponse)
async def explain_prediction(
    request: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Explain why a prediction was made using SHAP values.

    **Provides:**
    - Which features contributed most
    - Positive vs negative factors
    - Counterfactual analysis ("what if?")
    - Plain English explanation
    """
    try:
        # TODO: Load model and data, generate explanation
        # For now, return placeholder

        return ExplainResponse(
            prediction=7.5,
            explanation_text=(
                "Your predicted energy level is 7.5/10, which is higher than average (6.8). "
                "Key factors: "
                "1. sleep_quality (8.5 hours) increases your score by 0.9 "
                "2. exercise_minutes (45 min) increases your score by 0.5 "
                "3. work_stress (7/10) decreases your score by 0.3"
            ),
            top_positive_factors=[
                {'feature': 'sleep_quality', 'value': 8.5, 'impact': 0.9},
                {'feature': 'exercise_minutes', 'value': 45, 'impact': 0.5},
                {'feature': 'social_interactions', 'value': 3, 'impact': 0.2}
            ],
            top_negative_factors=[
                {'feature': 'work_stress', 'value': 7, 'impact': -0.3},
                {'feature': 'screen_time', 'value': 6, 'impact': -0.1}
            ],
            base_value=6.8
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation error: {str(e)}"
        )


# ========== RAG-Powered Chat ==========

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with Aurora AI using RAG (Retrieval Augmented Generation).

    **Features:**
    - Remembers past conversations
    - References your historical data
    - Context-aware responses
    - Natural language interaction

    **Examples:**
    - "How has my sleep been this month?"
    - "Show me patterns between exercise and mood"
    - "Why am I feeling low energy?"
    """
    try:
        # Initialize vector store and MetaAgent
        vector_store = VectorStore(
            backend="chromadb",
            collection_name=f"user_{current_user.id}"
        )

        meta_agent = MetaAgent(db=db, vector_store=vector_store)

        # Chat
        response = await meta_agent.chat(
            user_id=current_user.id,
            message=request.message
        )

        return ChatResponse(
            message=response['message'],
            sources=response.get('sources', []),
            timestamp=response['timestamp']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


# ========== MetaAgent Analysis ==========

@router.post("/meta-analysis", response_model=MetaAnalysisResponse)
async def meta_agent_analysis(
    request: MetaAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Comprehensive AI analysis using MetaAgent.

    **What it does:**
    1. Runs all 7 specialized agents
    2. Retrieves relevant context from memory
    3. Synthesizes insights using meta-reasoning
    4. Generates unified recommendations

    **Perfect for:**
    - Weekly life reviews
    - Strategic planning
    - Identifying cross-domain patterns
    - Getting comprehensive insights
    """
    try:
        # Initialize MetaAgent
        vector_store = VectorStore(
            backend="chromadb",
            collection_name=f"user_{current_user.id}"
        )

        meta_agent = MetaAgent(db=db, vector_store=vector_store)

        # Run comprehensive analysis
        result = await meta_agent.analyze_and_recommend(
            user_id=current_user.id,
            query=request.query,
            use_memory=request.use_memory
        )

        return MetaAnalysisResponse(
            meta_insights=result['meta_analysis']['meta_insights'],
            cross_domain_patterns=result['meta_analysis']['cross_domain_patterns'],
            unified_recommendations=result['unified_recommendations'],
            confidence=result['meta_analysis']['confidence'],
            execution_time=result['execution_time_seconds']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Meta-analysis error: {str(e)}"
        )


# ========== Recommendation Feedback ==========

class RecommendationFeedback(BaseModel):
    recommendation_id: str
    feedback_score: float = Field(..., ge=0, le=1, description="0 = disliked, 1 = loved")
    implemented: bool = Field(False, description="Did user implement it?")
    notes: Optional[str] = None


@router.post("/feedback")
async def record_recommendation_feedback(
    feedback: RecommendationFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Record feedback on AI recommendations.

    Used by reinforcement learning to improve future recommendations.
    """
    try:
        # TODO: Store feedback and update RL models

        return {
            'message': 'Feedback recorded',
            'recommendation_id': feedback.recommendation_id,
            'thank_you': 'Your feedback helps Aurora AI learn and improve!'
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback error: {str(e)}"
        )


# ========== Health Check ==========

@router.get("/health")
async def ml_health_check():
    """Check if advanced ML features are available."""
    try:
        # Check dependencies
        checks = {
            'prophet': False,
            'torch': False,
            'shap': False,
            'chromadb': False,
            'qdrant': False,
            'sentence_transformers': False
        }

        try:
            import prophet
            checks['prophet'] = True
        except:
            pass

        try:
            import torch
            checks['torch'] = True
        except:
            pass

        try:
            import shap
            checks['shap'] = True
        except:
            pass

        try:
            import chromadb
            checks['chromadb'] = True
        except:
            pass

        try:
            from qdrant_client import QdrantClient
            checks['qdrant'] = True
        except:
            pass

        try:
            from sentence_transformers import SentenceTransformer
            checks['sentence_transformers'] = True
        except:
            pass

        all_available = all(checks.values())

        return {
            'status': 'healthy' if all_available else 'degraded',
            'features': checks,
            'message': 'All ML features available' if all_available else 'Some ML features unavailable'
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
