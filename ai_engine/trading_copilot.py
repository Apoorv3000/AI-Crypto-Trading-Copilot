"""Integrated trading system with rule enrichment.

This module provides the main entry point that:
1. Takes user's vague query
2. Uses rule enrichment graph to create structured rule
3. Executes trading decision with the enriched rule
"""

from typing import Dict, Any, Optional
import json
from ai_engine.graph.rule_enrichment_graph import enrich_rule
from ai_engine.graph.engine import DecisionEngine
from ai_engine.utils.logger import get_logger

logger = get_logger(__name__)


def execute_trading_decision_with_enrichment(
    user_query: str,
    symbol: str,
    prices: list[float],
    volumes: list[float],
    skip_enrichment: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """Execute trading decision with optional rule enrichment.
    
    Flow:
    1. If user_query is vague, use rule enrichment graph to create structured rule
    2. User confirms the enriched rule (human-in-the-loop)
    3. Execute hierarchical trading graph with the rule
    4. Return final decision
    
    Args:
        user_query: User's natural language query (e.g., "buy ETH when RSI is low")
        symbol: Trading symbol (e.g., "ETH/USD")
        prices: Historical price data
        volumes: Historical volume data
        skip_enrichment: If True, skip rule enrichment and use query directly
        **kwargs: Additional parameters for decision engine
        
    Returns:
        Final trading decision with metadata
    """
    
    print("\n" + "="*70)
    print("🤖 AI TRADING COPILOT - Integrated System")
    print("="*70)
    print(f"\n📊 Symbol: {symbol}")
    print(f"💬 User Query: \"{user_query}\"")
    print("="*70 + "\n")
    
    enriched_rule = None
    
    # Step 1: Rule Enrichment (if not skipped)
    if not skip_enrichment:
        print("🔍 Step 1: Rule Enrichment")
        print("-" * 70)
        print("Analyzing your query to create a structured trading rule...\n")
        
        enriched_rule = enrich_rule(user_query)
        
        if enriched_rule is None:
            print("\n⚠️  Rule enrichment cancelled. Proceeding with original query...\n")
        else:
            print("\n✅ Structured rule created and confirmed!")
            print("-" * 70 + "\n")
    else:
        print("⏭️  Skipping rule enrichment (using query directly)\n")
    
    # Step 2: Execute Trading Decision
    print("🎯 Step 2: Trading Decision Analysis")
    print("-" * 70)
    print("Analyzing market conditions, sentiment, and risk...\n")
    
    engine = DecisionEngine()
    
    # If we have an enriched rule, pass it to the engine
    if enriched_rule:
        # Convert enriched rule to the format expected by the engine
        rules = [enriched_rule]
        kwargs["rules"] = rules
        logger.info(f"Using enriched rule: {enriched_rule['name']}")
    
    # Execute the decision
    decision = engine.decide(
        symbol=symbol,
        prices=prices,
        volumes=volumes,
        user_request=user_query,
        **kwargs
    )
    
    # Step 3: Present Results
    print("\n" + "="*70)
    print("📋 FINAL TRADING DECISION")
    print("="*70)
    
    print(f"\n🎯 Action: {decision.get('action', 'unknown').upper()}")
    print(f"📊 Confidence: {decision.get('confidence', 0.0):.1%}")
    print(f"💭 Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
    
    if decision.get('quantity'):
        print(f"📦 Quantity: {decision.get('quantity')}")
    
    if decision.get('stop_loss'):
        print(f"🛡️  Stop Loss: ${decision.get('stop_loss'):.2f}")
    
    if decision.get('take_profit'):
        print(f"🎯 Take Profit: ${decision.get('take_profit'):.2f}")
    
    print(f"\n⏱️  Processing Time: {decision.get('processing_time_ms', 0):.2f}ms")
    
    if enriched_rule:
        print(f"\n📜 Used Rule: {enriched_rule['name']}")
    
    print("\n" + "="*70)
    
    # Add enriched rule to decision metadata
    if enriched_rule:
        decision["enriched_rule"] = enriched_rule
    
    return decision


def interactive_trading_session():
    """Interactive trading session with rule enrichment.
    
    Allows user to:
    1. Enter multiple trading queries
    2. Each query goes through rule enrichment
    3. Execute trading decisions
    4. Continue with more queries
    """
    
    print("\n" + "="*70)
    print("🤖 AI TRADING COPILOT - Interactive Session")
    print("="*70)
    print("\nWelcome! I'll help you create and execute trading rules.")
    print("\nYou can:")
    print("  • Enter vague queries like 'buy ETH when RSI is low'")
    print("  • I'll ask clarifying questions to build a complete rule")
    print("  • Review and confirm the rule")
    print("  • Execute the trading decision")
    print("\nType 'exit' or 'quit' to end the session.")
    print("="*70 + "\n")
    
    # Example data for testing
    example_prices = [3200, 3210, 3205, 3215, 3220, 3218, 3225, 3230, 3228, 3235]
    example_volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500]
    
    while True:
        print("\n" + "-"*70)
        user_query = input("\n💬 Enter your trading query: ").strip()
        
        if user_query.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Thanks for using AI Trading Copilot. Goodbye!\n")
            break
        
        if not user_query:
            print("⚠️  Please enter a query.")
            continue
        
        # Ask for symbol
        symbol = input("📊 Enter trading symbol (default: ETH/USD): ").strip() or "ETH/USD"
        
        # Execute with enrichment
        try:
            decision = execute_trading_decision_with_enrichment(
                user_query=user_query,
                symbol=symbol,
                prices=example_prices,
                volumes=example_volumes
            )
            
            # Ask if user wants to continue
            continue_choice = input("\n\n🔄 Execute another query? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 Thanks for using AI Trading Copilot. Goodbye!\n")
                break
                
        except Exception as e:
            logger.error(f"Error in trading session: {e}", exc_info=True)
            print(f"\n❌ Error: {str(e)}")
            print("Please try again with a different query.\n")


if __name__ == "__main__":
    """Test the integrated system."""
    
    # Choose mode
    print("\n" + "="*70)
    print("🤖 AI TRADING COPILOT")
    print("="*70)
    print("\nChoose mode:")
    print("  [1] Single query test")
    print("  [2] Interactive session")
    print("="*70)
    
    mode = input("\nMode (1 or 2): ").strip()
    
    if mode == "2":
        interactive_trading_session()
    else:
        # Single query test
        test_query = "buy ETH when RSI is low"
        test_symbol = "ETH/USD"
        test_prices = [3200, 3210, 3205, 3215, 3220, 3218, 3225, 3230, 3228, 3235]
        test_volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500]
        
        decision = execute_trading_decision_with_enrichment(
            user_query=test_query,
            symbol=test_symbol,
            prices=test_prices,
            volumes=test_volumes
        )
        
        print("\n📄 Full Decision JSON:")
        print(json.dumps(decision, indent=2))
