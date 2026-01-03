"""Decision engine - orchestrates the hierarchical LangGraph workflow."""

from typing import Dict, Any, Optional
import time
from datetime import datetime

from ..context.schema import DecisionContext
from ..context.builder import ContextBuilder
from .hierarchical_graph import create_hierarchical_graph
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """Main decision engine that orchestrates the LangGraph workflow."""
    
    def __init__(self, use_hierarchical: bool = True, use_simple_graph: bool = False):
        """Initialize the decision engine.
        
        Args:
            use_hierarchical: DEPRECATED - Always uses hierarchical architecture now
            use_simple_graph: DEPRECATED - No longer supported
        """
        if not use_hierarchical:
            logger.warning(
                "use_hierarchical=False is deprecated. "
                "Only hierarchical architecture is supported now."
            )
        if use_simple_graph:
            logger.warning(
                "use_simple_graph is deprecated. "
                "Only hierarchical architecture is supported now."
            )
            
        self.context_builder = ContextBuilder()
        self.use_hierarchical = True  # Always True now
        self.use_simple_graph = False  # Always False now
        
        self.graph = create_hierarchical_graph()
        logger.info("Decision engine initialized with hierarchical graph (supervisor → agents)")

    
    def decide(
        self,
        symbol: str,
        prices: list[float],
        volumes: list[float],
        user_request: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the decision workflow and return the final decision.
        
        Args:
            symbol: Trading symbol
            prices: Historical price data
            volumes: Historical volume data
            user_request: User's trading request (for hierarchical mode)
            **kwargs: Additional parameters (rules, positions, etc.)
            
        Returns:
            Final trading decision
        """
        start_time = time.time()
        logger.info(f"Starting decision workflow for {symbol}")
        
        try:
            # For hierarchical graph, create simpler context
            if self.use_hierarchical:
                # Extract enriched rules from kwargs if provided
                enriched_rules = kwargs.get("rules", [])
                # Format rules as descriptive strings for supervisor
                trading_rules = []
                if enriched_rules:
                    for rule in enriched_rules:
                        # Create a human-readable rule description
                        conditions_str = ", ".join([
                            f"{c['field']} {c['operator']} {c['value']}" 
                            for c in rule.get('conditions', [])
                        ])
                        rule_str = f"{rule.get('name', 'Unnamed Rule')}: {rule.get('action', 'UNKNOWN').upper()} when {conditions_str}"
                        if rule.get('metadata', {}).get('description'):
                            rule_str += f" - {rule['metadata']['description']}"
                        trading_rules.append(rule_str)
                
                context = DecisionContext(
                    symbol=symbol,
                    prices=prices,
                    volumes=volumes,
                    request_id=user_request or f"Decision for {symbol}",
                    user_request=user_request,
                    trading_rules=trading_rules,
                )
            else:
                # Build full context for legacy graphs
                context = self.context_builder.build_context(
                    symbol=symbol,
                    prices=prices,
                    volumes=volumes,
                    **kwargs
                )
            
            # Execute the graph
            result = self.graph.invoke(context)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Extract final decision
            if isinstance(result, DecisionContext):
                final_decision = result.final_decision or result.decision_agent_output
            elif isinstance(result, dict):
                final_decision = result.get("final_decision") or result.get("decision_agent_output")
            else:
                final_decision = None
            
            if final_decision is None:
                logger.error("No final decision produced")
                final_decision = {
                    "action": "hold",
                    "confidence": 0.0,
                    "reasoning": "No decision produced by workflow",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # Add metadata
            final_decision["processing_time_ms"] = processing_time_ms
            final_decision["symbol"] = symbol
            
            # Add supervisor plan info if hierarchical
            if self.use_hierarchical and isinstance(result, DecisionContext):
                final_decision["supervisor_plan"] = result.supervisor_plan
                # Include enriched rules in the response
                if kwargs.get("rules"):
                    final_decision["enriched_rules"] = kwargs["rules"]
            
            logger.info(
                f"Decision completed for {symbol}: {final_decision.get('action', 'unknown')} "
                f"({processing_time_ms:.2f}ms)"
            )
            
            return final_decision
        
        except Exception as e:
            logger.error(f"Error in decision workflow: {e}", exc_info=True)
            return {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": f"Error in decision workflow: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    async def decide_async(
        self,
        symbol: str,
        prices: list[float],
        volumes: list[float],
        user_request: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of decide (for FastAPI integration).
        
        Args:
            symbol: Trading symbol
            prices: Historical price data
            volumes: Historical volume data
            user_request: User's trading request
            **kwargs: Additional parameters
            
        Returns:
            Final trading decision
        """
        # For now, just wrap the sync version
        # In production, you'd use ainvoke() with async agents
        return self.decide(symbol, prices, volumes, user_request, **kwargs)
