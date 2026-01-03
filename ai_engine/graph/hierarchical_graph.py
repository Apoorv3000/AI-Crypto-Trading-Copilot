"""Hierarchical LangGraph workflow with supervisor-subgraph architecture.

Clean architecture:
    Supervisor → Router → Subgraphs → Aggregator
    
Each subgraph is self-contained with:
    - schema.py: Pydantic models
    - worker.py: Deterministic computation
    - evaluator.py: LLM validation (LCEL)
    - graph.py: Subgraph builder
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from ..context.schema import DecisionContext
from ..agents.supervisor.agent import supervisor_agent
from ..agents.market import create_market_subgraph, MarketSubgraphState
# ML subgraph temporarily disabled - not yet implemented
# from ..agents.ml import create_ml_subgraph, MLSubgraphState
from ..agents.sentiment import create_sentiment_subgraph, SentimentSubgraphState
from ..agents.risk import create_risk_subgraph, RiskSubgraphState
from ..utils.llm_v2 import get_llm, LLMConfig
from ..utils.logger import get_logger
from ..utils.json_fixer import fix_json_string

logger = get_logger(__name__)


class ResilientPydanticParser(PydanticOutputParser):
    """Pydantic parser that fixes common JSON issues before parsing."""
    
    def parse(self, text: str):
        """Parse with JSON fixing."""
        try:
            return super().parse(text)
        except OutputParserException as e:
            try:
                fixed_text = fix_json_string(text)
                return super().parse(fixed_text)
            except Exception:
                raise e


# ============================================================================
# Router Decision Model
# ============================================================================

class RouterDecision(BaseModel):
    """Decision made by the router for next subgraph to execute."""
    
    next_action: Literal[
        "market_subgraph",
        # "ml_subgraph",  # Disabled - not yet implemented
        "sentiment_subgraph",
        "risk_subgraph",
        "final_decision",
        "END"
    ] = Field(description="Which subgraph or action to execute next")
    
    reasoning: str = Field(description="Why this action was chosen")


# ============================================================================
# Subgraph Wrapper Nodes (Connect DecisionContext to subgraph states)
# ============================================================================

def market_subgraph_node(context: DecisionContext) -> DecisionContext:
    """Execute market analysis subgraph.
    
    Converts DecisionContext → MarketSubgraphState → run subgraph → update context
    """
    logger.info(f"Executing market subgraph for {context.symbol}")
    
    try:
        # Create subgraph state
        state = MarketSubgraphState(
            symbol=context.symbol,
            prices=context.prices,
            volumes=context.volumes,
        )
        
        # Execute subgraph
        subgraph = create_market_subgraph()
        result = subgraph.invoke(state)
        
        # Update main context with results (result is a dict from LangGraph)
        if result.get("worker_output"):
            context.market_agent_output = result["worker_output"] if isinstance(result["worker_output"], dict) else result["worker_output"].model_dump()
        
        if result.get("evaluation"):
            context.market_agent_output = context.market_agent_output or {}
            context.market_agent_output["evaluation"] = result["evaluation"] if isinstance(result["evaluation"], dict) else result["evaluation"].model_dump()
        
        if result.get("error"):
            logger.warning(f"Market subgraph error: {result['error']}")
            context.market_agent_output = context.market_agent_output or {}
            context.market_agent_output["error"] = result["error"]
        
        logger.info("Market subgraph completed")
        
    except Exception as e:
        logger.error(f"Market subgraph node error: {e}", exc_info=True)
        context.market_agent_output = {"error": str(e)}
    
    return context


def ml_subgraph_node(context: DecisionContext) -> DecisionContext:
    """Execute ML prediction subgraph."""
    logger.info(f"Executing ML subgraph for {context.symbol}")
    
    try:
        state = MLSubgraphState(
            symbol=context.symbol,
            prices=context.prices,
            volumes=context.volumes,
        )
        
        subgraph = create_ml_subgraph()
        result = subgraph.invoke(state)
        
        if result.get("worker_output"):
            context.ml_agent_output = result["worker_output"] if isinstance(result["worker_output"], dict) else result["worker_output"].model_dump()
        
        if result.get("evaluation"):
            context.ml_agent_output = context.ml_agent_output or {}
            context.ml_agent_output["evaluation"] = result["evaluation"] if isinstance(result["evaluation"], dict) else result["evaluation"].model_dump()
        
        if result.get("error"):
            logger.warning(f"ML subgraph error: {result['error']}")
            context.ml_agent_output = context.ml_agent_output or {}
            context.ml_agent_output["error"] = result["error"]
        
        logger.info("ML subgraph completed")
        
    except Exception as e:
        logger.error(f"ML subgraph node error: {e}", exc_info=True)
        context.ml_agent_output = {"error": str(e)}
    
    return context


def sentiment_subgraph_node(context: DecisionContext) -> DecisionContext:
    """Execute sentiment analysis subgraph."""
    logger.info(f"Executing sentiment subgraph for {context.symbol}")
    
    try:
        state = SentimentSubgraphState(
            symbol=context.symbol,
        )
        
        subgraph = create_sentiment_subgraph()
        result = subgraph.invoke(state)
        
        if result.get("worker_output"):
            context.sentiment_agent_output = result["worker_output"] if isinstance(result["worker_output"], dict) else result["worker_output"].model_dump()
        
        if result.get("evaluation"):
            context.sentiment_agent_output = context.sentiment_agent_output or {}
            context.sentiment_agent_output["evaluation"] = result["evaluation"] if isinstance(result["evaluation"], dict) else result["evaluation"].model_dump()
        
        if result.get("error"):
            logger.warning(f"Sentiment subgraph error: {result['error']}")
            context.sentiment_agent_output = context.sentiment_agent_output or {}
            context.sentiment_agent_output["error"] = result["error"]
        
        logger.info("Sentiment subgraph completed")
        
    except Exception as e:
        logger.error(f"Sentiment subgraph node error: {e}", exc_info=True)
        context.sentiment_agent_output = {"error": str(e)}
    
    return context


def risk_subgraph_node(context: DecisionContext) -> DecisionContext:
    """Execute risk validation subgraph."""
    logger.info(f"Executing risk subgraph for {context.symbol}")
    
    try:
        # Determine current price from prices array
        current_price = context.prices[-1] if context.prices else 100.0
        
        # Default action/quantity
        action = "buy"
        quantity = 1
        
        # If we have a preliminary decision, use that
        if context.decision_agent_output:
            action = context.decision_agent_output.get("action", "buy")
            quantity = context.decision_agent_output.get("quantity", 1)
        
        state = RiskSubgraphState(
            symbol=context.symbol,
            current_price=current_price,
            proposed_action=action,
            proposed_quantity=quantity,
        )
        
        subgraph = create_risk_subgraph()
        result = subgraph.invoke(state)
        
        if result.get("worker_output"):
            context.risk_agent_output = result["worker_output"] if isinstance(result["worker_output"], dict) else result["worker_output"].model_dump()
        
        if result.get("evaluation"):
            context.risk_agent_output = context.risk_agent_output or {}
            context.risk_agent_output["evaluation"] = result["evaluation"] if isinstance(result["evaluation"], dict) else result["evaluation"].model_dump()
        
        if result.get("error"):
            logger.warning(f"Risk subgraph error: {result['error']}")
            context.risk_agent_output = context.risk_agent_output or {}
            context.risk_agent_output["error"] = result["error"]
        
        logger.info("Risk subgraph completed")
        
    except Exception as e:
        logger.error(f"Risk subgraph node error: {e}", exc_info=True)
        context.risk_agent_output = {"error": str(e)}
    
    return context


# ============================================================================
# Router Node (LLM-driven dynamic routing)
# ============================================================================

def route_next_subgraph(context: DecisionContext) -> str:
    """Use LLM to decide which subgraph to execute next.
    
    This is the core of hierarchical routing - the LLM decides the execution path.
    Uses LCEL: prompt | llm | parser
    """
    logger.info("Router deciding next action")
    
    try:
        # Check what's been completed
        completed = []
        if context.market_agent_output:
            completed.append("market")
        if context.ml_agent_output:
            completed.append("ml")
        if context.sentiment_agent_output:
            completed.append("sentiment")
        if context.risk_agent_output:
            completed.append("risk")
        if context.final_decision:
            return "END"
        
        # Create parser with JSON fixing
        parser = ResilientPydanticParser(pydantic_object=RouterDecision)
        
        # Create prompt
        system_message = """You are a workflow router for a trading decision system.

Your job is to decide which subgraph should execute next based on:
1. The supervisor's plan
2. What's already been completed
3. Logical dependencies between subgraphs

Available subgraphs:
- market_subgraph: Technical analysis (RSI, EMA, trend)
- sentiment_subgraph: Sentiment analysis (social, news)
- risk_subgraph: Risk validation (constraints, limits)
- final_decision: Synthesize all data into trading decision

Note: ML subgraph temporarily disabled (not yet implemented)

Rules:
1. Data gathering subgraphs (market, sentiment) can run in any order
2. Risk subgraph should run after we have initial data
3. final_decision should run ONLY after all needed subgraphs complete
4. Skip subgraphs if supervisor plan doesn't require them
5. END only after final_decision is set

{format_instructions}"""

        human_message = """Symbol: {symbol}
User Request: {request_id}

Supervisor Plan:
{supervisor_plan}

Completed Subgraphs: {completed}

What should execute next?"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message),
        ])
        
        # Build LCEL chain
        llm = get_llm(**LLMConfig.ROUTER)  # Use configured router LLM
        chain = prompt | llm | parser
        
        # Invoke
        decision = chain.invoke({
            "symbol": context.symbol,
            "request_id": context.request_id,
            "supervisor_plan": context.supervisor_plan or "No plan set",
            "completed": completed if completed else "None",
            "format_instructions": parser.get_format_instructions(),
        })
        
        logger.info(f"Router decision: {decision.next_action} - {decision.reasoning}")
        return decision.next_action
        
    except Exception as e:
        logger.error(f"Router error: {e}", exc_info=True)
        # Fallback to simple logic
        return fallback_router(context)


def fallback_router(context: DecisionContext) -> str:
    """Fallback router if LLM fails - uses simple sequential logic."""
    
    if not context.market_agent_output:
        return "market_subgraph"
    if not context.sentiment_agent_output:
        return "sentiment_subgraph"
    # ML subgraph disabled - not yet implemented
    # if not context.ml_agent_output:
    #     return "ml_subgraph"
    if not context.risk_agent_output:
        return "risk_subgraph"
    if not context.final_decision:
        return "final_decision"
    return "END"


# ============================================================================
# Final Decision Aggregator (LCEL)
# ============================================================================

class FinalTradingDecision(BaseModel):
    """Final trading decision synthesized from all subgraphs."""
    
    action: Literal["buy", "sell", "hold"] = Field(description="Trading action")
    confidence: float = Field(ge=0.0, le=1.0, description="Decision confidence")
    quantity: int = Field(ge=0, description="Quantity to trade")
    
    reasoning: str = Field(description="Detailed reasoning for decision")
    
    risk_approved: bool = Field(description="Whether risk checks passed")
    
    stop_loss: float | None = Field(default=None, description="Recommended stop loss")
    take_profit: float | None = Field(default=None, description="Recommended take profit")


def final_decision_node(context: DecisionContext) -> DecisionContext:
    """Synthesize all subgraph outputs into final trading decision.
    
    Uses LCEL: prompt | llm | parser
    """
    logger.info("Generating final trading decision")
    
    try:
        # Create parser with JSON fixing
        parser = ResilientPydanticParser(pydantic_object=FinalTradingDecision)
        
        # Create prompt
        system_message = """You are a trading decision synthesizer.

Your job is to analyze ALL subgraph outputs and make a final trading decision.

Consider:
1. Market technical indicators
2. ML predictions
3. Sentiment signals
4. Risk constraints

Make a decision that:
- Aligns with the data
- Respects risk limits
- Has clear reasoning

{format_instructions}"""

        human_message = """Symbol: {symbol}
Current Price: {price:.2f}

Market Analysis:
{market}

ML Predictions:
{ml}

Sentiment Analysis:
{sentiment}

Risk Validation:
{risk}

Make your final trading decision."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message),
        ])
        
        # Build LCEL chain
        llm = get_llm(**LLMConfig.AGGREGATOR)  # Use configured aggregator LLM
        chain = prompt | llm | parser
        
        # Invoke
        current_price = context.prices[-1] if context.prices else 100.0
        
        decision = chain.invoke({
            "symbol": context.symbol,
            "price": current_price,
            "market": context.market_agent_output or "No data",
            "ml": context.ml_agent_output or "No data",
            "sentiment": context.sentiment_agent_output or "No data",
            "risk": context.risk_agent_output or "No data",
            "format_instructions": parser.get_format_instructions(),
        })
        
        # Update context
        context.final_decision = decision.model_dump()
        context.decision_agent_output = decision.model_dump()
        
        logger.info(f"Final decision: {decision.action} with confidence {decision.confidence:.2f}")
        
    except Exception as e:
        logger.error(f"Final decision error: {e}", exc_info=True)
        # Safe fallback
        context.final_decision = {
            "action": "hold",
            "confidence": 0.0,
            "quantity": 0,
            "reasoning": f"Error in decision synthesis: {str(e)}",
            "risk_approved": False,
        }
    
    return context


# ============================================================================
# Main Hierarchical Graph Builder
# ============================================================================

def create_hierarchical_graph() -> StateGraph:
    """Create the hierarchical graph with supervisor, router, and subgraphs.
    
    Architecture:
        START
          ↓
        Supervisor (generates plan)
          ↓
        Router (decides next subgraph) ←──┐
          ↓                                │
        [Subgraphs]                        │
          market_subgraph ─────────────────┤
          ml_subgraph ─────────────────────┤
          sentiment_subgraph ──────────────┤
          risk_subgraph ───────────────────┤
          final_decision                   │
          ↓                                │
        Router (check if done) ────────────┘
          ↓
        END
    
    Returns:
        Compiled hierarchical graph
    """
    logger.info("Creating hierarchical graph")
    
    # Create main graph with DecisionContext as state
    graph = StateGraph(DecisionContext)
    
    # Add supervisor node (generates plan)
    graph.add_node("supervisor", supervisor_agent)
    
    # Add subgraph wrapper nodes
    graph.add_node("market_subgraph", market_subgraph_node)
    # ML subgraph disabled - not yet implemented
    # graph.add_node("ml_subgraph", ml_subgraph_node)
    graph.add_node("sentiment_subgraph", sentiment_subgraph_node)
    graph.add_node("risk_subgraph", risk_subgraph_node)
    
    # Add final decision node
    graph.add_node("final_decision", final_decision_node)
    
    # Start with supervisor
    graph.set_entry_point("supervisor")
    
    # After supervisor, router decides next action
    graph.add_conditional_edges(
        "supervisor",
        route_next_subgraph,
        {
            "market_subgraph": "market_subgraph",
            # "ml_subgraph": "ml_subgraph",  # Disabled
            "sentiment_subgraph": "sentiment_subgraph",
            "risk_subgraph": "risk_subgraph",
            "final_decision": "final_decision",
            "END": END,
        }
    )
    
    # After each subgraph, router decides what's next
    for subgraph_name in ["market_subgraph", "sentiment_subgraph", "risk_subgraph"]:  # Removed ml_subgraph
        graph.add_conditional_edges(
            subgraph_name,
            route_next_subgraph,
            {
                "market_subgraph": "market_subgraph",
                # "ml_subgraph": "ml_subgraph",  # Disabled
                "sentiment_subgraph": "sentiment_subgraph",
                "risk_subgraph": "risk_subgraph",
                "final_decision": "final_decision",
                "END": END,
            }
        )
    
    # After final decision, always end
    graph.add_edge("final_decision", END)
    
    # Compile
    workflow = graph.compile()
    
    logger.info("Hierarchical graph created successfully")
    return workflow
