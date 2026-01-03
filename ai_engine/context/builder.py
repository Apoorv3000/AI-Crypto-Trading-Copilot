"""Context builder module.

Combines all tool outputs into a unified DecisionContext object.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .schema import (
    DecisionContext,
    MarketContext,
    MLContext,
    SentimentContext,
    RulesContext,
    RiskContext,
    HistoryContext,
)
from ..tools import (
    get_market_indicators,
    get_ml_predictions,
    get_sentiment_analysis,
    evaluate_rules,
    check_risk_constraints,
)


class ContextBuilder:
    """Builds DecisionContext from input parameters and tool outputs."""
    
    def __init__(self):
        """Initialize the context builder."""
        pass
    
    def build_context(
        self,
        symbol: str,
        prices: List[float],
        volumes: List[float],
        rules: List[Dict[str, Any]] = None,
        proposed_action: str = "hold",
        proposed_size: float = 0.0,
        account_balance: float = 10000.0,
        current_positions: Dict[str, float] = None,
        entry_price: Optional[float] = None,
        fear_greed_index: Optional[float] = None,
        history: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> DecisionContext:
        """Build complete decision context from input parameters.
        
        Args:
            symbol: Trading symbol
            prices: Historical price data
            volumes: Historical volume data
            rules: User-defined trading rules
            proposed_action: Proposed trading action
            proposed_size: Proposed position size
            account_balance: Account balance
            current_positions: Current positions
            entry_price: Entry price for stop loss
            fear_greed_index: Fear & greed index
            history: Historical performance data
            **kwargs: Additional parameters
            
        Returns:
            Complete DecisionContext object
        """
        request_id = kwargs.get("request_id", str(uuid.uuid4()))
        timestamp = datetime.utcnow().isoformat()
        
        # Get market indicators
        market_data = get_market_indicators(symbol, prices, volumes)
        market_context = MarketContext(**market_data)
        
        # Get ML predictions
        ml_data = get_ml_predictions(symbol, prices, market_data)
        ml_context = MLContext(**ml_data)
        
        # Get sentiment analysis
        sentiment_data = get_sentiment_analysis(symbol, fear_greed_index)
        sentiment_context = SentimentContext(**sentiment_data)
        
        # Evaluate rules
        if rules is None:
            rules = []
        
        # Build context for rule evaluation
        rule_eval_context = {
            "market": market_data,
            "ml": ml_data,
            "sentiment": sentiment_data,
        }
        rules_data = evaluate_rules(rules, rule_eval_context)
        rules_context = RulesContext(**rules_data)
        
        # Check risk constraints
        risk_data = check_risk_constraints(
            symbol=symbol,
            proposed_action=proposed_action,
            proposed_size=proposed_size,
            current_price=market_data["current_price"],
            account_balance=account_balance,
            current_positions=current_positions or {},
            entry_price=entry_price,
            volatility=ml_data["volatility"],
        )
        risk_context = RiskContext(**risk_data)
        
        # Build history context
        if history is None:
            history = {}
        history_context = HistoryContext(**history)
        
        # Create complete decision context
        context = DecisionContext(
            symbol=symbol,
            request_id=request_id,
            timestamp=timestamp,
            market=market_context,
            ml=ml_context,
            sentiment=sentiment_context,
            rules=rules_context,
            risk=risk_context,
            history=history_context,
        )
        
        return context
    
    def update_context(
        self,
        context: DecisionContext,
        **updates
    ) -> DecisionContext:
        """Update an existing context with new data.
        
        Args:
            context: Existing DecisionContext
            **updates: Fields to update
            
        Returns:
            Updated DecisionContext
        """
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        return context
