"""Visualize the hierarchical LangGraph architecture.

This script generates a visual representation of the graph that can be viewed in a browser.
"""

from ai_engine.graph.hierarchical_graph import create_hierarchical_graph
from ai_engine.graph.engine import DecisionEngine


def save_mermaid_diagram():
    """Generate and save a Mermaid diagram of the graph."""
    print("Creating hierarchical graph...")
    graph = create_hierarchical_graph()
    
    # Get Mermaid diagram
    try:
        mermaid_png = graph.get_graph().draw_mermaid_png()
        
        # Save as PNG
        with open("hierarchical_graph.png", "wb") as f:
            f.write(mermaid_png)
        
        print("✅ Graph saved as hierarchical_graph.png")
        print("   Open this file to view the graph visualization!")
        
    except Exception as e:
        print(f"⚠️  Could not generate PNG: {e}")
        print("   Trying Mermaid syntax instead...")
        
        # Fallback: Get Mermaid syntax
        try:
            mermaid_syntax = graph.get_graph().draw_mermaid()
            
            # Save as Mermaid file
            with open("hierarchical_graph.mmd", "w") as f:
                f.write(mermaid_syntax)
            
            print("✅ Graph saved as hierarchical_graph.mmd")
            print("   You can visualize this at: https://mermaid.live")
            print("   Or use VS Code with the Mermaid extension")
            
            # Also create HTML file
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Hierarchical LangGraph Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{ startOnLoad: true }});</script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .mermaid {{
            text-align: center;
            background: white;
        }}
        .info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Hierarchical Multi-Agent Trading System</h1>
        
        <div class="mermaid">
{mermaid_syntax}
        </div>
        
        <div class="info">
            <h3>Architecture Flow:</h3>
            <ul>
                <li><strong>Supervisor Agent</strong>: Analyzes user request and generates execution plan (LCEL)</li>
                <li><strong>Router</strong>: LLM dynamically decides which subgraph to execute next</li>
                <li><strong>Agent Subgraphs</strong>: Each runs worker → evaluator pattern
                    <ul>
                        <li>Market Agent: Technical analysis (RSI, EMA, volume)</li>
                        <li>Sentiment Agent: Social sentiment (Twitter, Reddit, LunarCrush)</li>
                        <li>ML Agent: ML predictions (direction, volatility)</li>
                        <li>Risk Agent: Risk validation (stop loss, position size)</li>
                    </ul>
                </li>
                <li><strong>Aggregator</strong>: Synthesizes all outputs into final trading decision (LCEL)</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
            
            with open("hierarchical_graph.html", "w") as f:
                f.write(html_content)
            
            print("✅ Interactive HTML visualization saved as hierarchical_graph.html")
            print("   Open this file in your browser to see the graph!")
            
        except Exception as e2:
            print(f"❌ Could not generate visualization: {e2}")


def print_graph_structure():
    """Print a text representation of the graph structure."""
    print("\n" + "="*80)
    print("HIERARCHICAL GRAPH STRUCTURE")
    print("="*80)
    
    print("""
    START
      ↓
    supervisor (Supervisor Agent)
      - Generates execution plan
      - Extracts trading rules
      ↓
    [Router decides next action]
      ↓
    ├─→ market_subgraph
    │     - Worker: Technical analysis (deterministic)
    │     - Evaluator: Validates quality (LCEL)
    │     ↓
    │   [Router decides next]
    │
    ├─→ sentiment_subgraph
    │     - Worker: Social sentiment (deterministic)
    │     - Evaluator: Checks reliability (LCEL)
    │     ↓
    │   [Router decides next]
    │
    ├─→ ml_subgraph
    │     - Worker: ML predictions (deterministic)
    │     - Evaluator: Judges confidence (LCEL)
    │     ↓
    │   [Router decides next]
    │
    ├─→ risk_subgraph
    │     - Worker: Risk validation (deterministic)
    │     - Evaluator: Reviews risk management (LCEL)
    │     ↓
    │   [Router decides next]
    │
    └─→ final_decision
          - Aggregates all subgraph outputs
          - Applies trading rules
          - Generates final decision (LCEL)
          ↓
        END
    """)
    
    print("\nKey Features:")
    print("  • Dynamic Routing: LLM decides execution flow (not hardcoded)")
    print("  • Each Agent = Subgraph: Self-contained worker → evaluator")
    print("  • LCEL Everywhere: All LLM calls use prompt | llm | parser")
    print("  • Model-Agnostic: Can use Claude, GPT, or Gemini per agent")
    print("\n" + "="*80)


if __name__ == "__main__":
    print("🎨 Visualizing Hierarchical LangGraph\n")
    
    # Print text structure
    print_graph_structure()
    
    # Generate visual diagrams
    print("\nGenerating visual diagrams...")
    save_mermaid_diagram()
    
    print("\n✅ Done! Check the generated files:")
    print("   1. hierarchical_graph.html - Open in browser (recommended)")
    print("   2. hierarchical_graph.mmd - Mermaid syntax")
    print("   3. hierarchical_graph.png - PNG image (if available)")
