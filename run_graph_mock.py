"""Run the hierarchical graph with mock data - no real integrations needed.

This demonstrates the complete flow:
  Supervisor → Router → Agents (market/sentiment/ml/risk) → Final Decision

All workers use mock data, but the graph execution is REAL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from ai_engine.graph.engine import DecisionEngine
from ai_engine.context.schema import DecisionContext
import json

# Load environment variables with explicit path and override
# This ensures we get the real values, not placeholder/masked values
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


def run_mock_trading_decision():
    """Run the full hierarchical graph with mock data."""
    
    print("🚀 Starting Hierarchical Multi-Agent Trading System")
    print("=" * 80)
    print()
    
    # Initialize the decision engine
    print("📊 Initializing Decision Engine...")
    engine = DecisionEngine()  # Uses hierarchical graph by default
    print("✅ Engine initialized\n")
    
    # Prepare mock input data
    symbol = "ETH"
    prices = [3200.0, 3220.0, 3250.0, 3280.0, 3300.0, 3280.0, 3290.0, 3310.0, 3330.0, 3350.0]
    volumes = [1000, 1200, 1100, 1300, 1250, 1150, 1200, 1400, 1350, 1300]
    user_request = "What do you think about ETH? Should I buy?"
    
    print(f"📈 Input Data:")
    print(f"   Symbol: {symbol}")
    print(f"   Prices: {prices[:3]}... (last: ${prices[-1]:.2f})")
    print(f"   Volumes: {volumes[:3]}...")
    print(f"   User Request: '{user_request}'")
    print()
    print("=" * 80)
    print()
    
    # Run the decision workflow
    print("🔄 Executing Hierarchical Graph...")
    print()
    print("   Flow: Supervisor → Router → Agents → Aggregator")
    print()
    
    try:
        result = engine.decide(
            symbol=symbol,
            prices=prices,
            volumes=volumes,
            user_request=user_request
        )
        
        print()
        print("=" * 80)
        print("✅ EXECUTION COMPLETE")
        print("=" * 80)
        print()
        
        # Display results
        print("📋 SUPERVISOR PLAN:")
        if result.get("supervisor_plan"):
            plan = result["supervisor_plan"]
            print(f"   Required Subgraphs: {plan.get('required_subgraphs', [])}")
            print(f"   Reasoning: {plan.get('reasoning', 'N/A')[:100]}...")
        print()
        
        print("📊 AGENT OUTPUTS:")
        print()
        
        if result.get("market_agent_output"):
            print("   🔹 Market Agent (Technical Analysis):")
            market = result["market_agent_output"]
            print(f"      RSI: {market.get('rsi', 'N/A')}")
            print(f"      EMA Signal: {market.get('ema_signal', 'N/A')}")
            print(f"      Volume Signal: {market.get('volume_signal', 'N/A')}")
            print(f"      Trend: {market.get('trend_direction', 'N/A')}")
            print()
        
        if result.get("sentiment_agent_output"):
            print("   🔹 Sentiment Agent (Social Analysis):")
            sentiment = result["sentiment_agent_output"]
            print(f"      Overall Sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
            print(f"      Social Volume: {sentiment.get('social_volume', 'N/A')}")
            print(f"      Signal: {sentiment.get('sentiment_signal', 'N/A')}")
            print()
        
        if result.get("ml_agent_output"):
            print("   🔹 ML Agent (Predictions):")
            ml = result["ml_agent_output"]
            print(f"      Direction: {ml.get('predicted_direction', 'N/A')}")
            print(f"      Confidence: {ml.get('direction_confidence', 'N/A')}")
            print(f"      Volatility: {ml.get('predicted_volatility', 'N/A')}")
            print()
        
        if result.get("risk_agent_output"):
            print("   🔹 Risk Agent (Validation):")
            risk = result["risk_agent_output"]
            print(f"      All Checks Passed: {risk.get('all_checks_passed', 'N/A')}")
            print(f"      Risk Level: {risk.get('risk_level', 'N/A')}")
            print(f"      Stop Loss: {risk.get('stop_loss_message', 'N/A')[:60]}...")
            print()
        
        print("=" * 80)
        print("🎯 FINAL DECISION:")
        print("=" * 80)
        
        if result.get("final_decision"):
            decision = result["final_decision"]
            print()
            print(f"   Action: {decision.get('action', 'N/A').upper()}")
            print(f"   Confidence: {decision.get('confidence', 0) * 100:.1f}%")
            print(f"   Quantity: {decision.get('quantity', 0)}")
            print(f"   Risk Approved: {decision.get('risk_approved', False)}")
            print()
            print(f"   Reasoning:")
            reasoning = decision.get('reasoning', 'N/A')
            # Wrap reasoning text
            words = reasoning.split()
            line = "      "
            for word in words:
                if len(line) + len(word) + 1 > 75:
                    print(line)
                    line = "      " + word
                else:
                    line += " " + word if line != "      " else word
            if line != "      ":
                print(line)
            print()
            
            if decision.get('stop_loss'):
                print(f"   Stop Loss: ${decision['stop_loss']:.2f}")
            if decision.get('take_profit'):
                print(f"   Take Profit: ${decision['take_profit']:.2f}")
        
        print()
        print("=" * 80)
        print()
        
        # Save full result to JSON
        with open("trading_decision_result.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        print("💾 Full result saved to: trading_decision_result.json")
        print()
        
        return result
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print()
    result = run_mock_trading_decision()
    
    if result:
        print()
        print("✅ SUCCESS! The hierarchical graph executed completely.")
        print()
        print("What happened:")
        print("  1. ✅ Supervisor analyzed request and generated plan")
        print("  2. ✅ Router dynamically decided execution order")
        print("  3. ✅ Each agent subgraph executed (worker → evaluator)")
        print("  4. ✅ Aggregator synthesized final decision")
        print()
        print("All workers used MOCK DATA (no real API calls).")
        print("But the GRAPH EXECUTION was 100% REAL!")
        print()
        print("Next steps:")
        print("  • Check trading_decision_result.json for full output")
        print("  • Open hierarchical_graph.html to see the graph structure")
        print("  • When ready, add real integrations to workers")
        print()
