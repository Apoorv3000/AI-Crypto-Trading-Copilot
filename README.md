# AI Trading Engine - Hierarchical Multi-Agent System

A production-ready hierarchical multi-agent trading system built with **LangGraph**, **LangChain**, and **Pydantic**. Each agent is a self-contained subgraph following clean architecture principles.

## 🚀 Features

- **Hierarchical Architecture**: Supervisor → Router → Agent Subgraphs → Aggregator
- **Clean Agent Design**: Each agent has schema → worker → evaluator → graph
- **LCEL Everywhere**: All LLM calls use `prompt | llm | parser` pattern
- **Model-Agnostic**: Support for Claude, GPT, and Gemini
- **Production Integrations**: Hyperliquid, Privy, Twitter, Reddit, LunarCrush
- **Type-Safe**: Pydantic validation throughout
- **Dynamic Routing**: LLM-driven execution flow (not hardcoded)

## 🏗️ Architecture

### Hierarchical Flow
```
User Request
    ↓
Supervisor Agent (generates plan with LCEL)
    ↓
Router (LLM decides next subgraph)
    ↓
Agent Subgraphs (each is worker → evaluator)
    ├── Market Agent (technical analysis)
    ├── Sentiment Agent (social sentiment)
    ├── ML Agent (predictions)
    └── Risk Agent (validation)
    ↓
Aggregator (synthesizes decision with LCEL)
    ↓
Final Trading Decision
```

### Agent Structure
Each agent follows the same clean pattern:
- `schema.py`: Pydantic models for inputs/outputs
- `worker.py`: Deterministic computation (no LLM)
- `evaluator.py`: LLM validation using LCEL
- `graph.py`: Subgraph builder (worker → evaluator)

## 📁 Project Structure

```
ai_engine/
├── agents/                      # Self-contained agent subgraphs
│   ├── supervisor/             # Top-level orchestrator
│   │   └── agent.py           # Supervisor with LCEL
│   ├── market/                # Technical analysis
│   ├── sentiment/             # Social sentiment
│   ├── ml/                    # ML predictions
│   └── risk/                  # Risk validation
├── integrations/              # External data sources
│   ├── hyperliquid.py        # Exchange integration
│   ├── privy.py              # Wallet management
│   ├── twitter.py            # Twitter sentiment
│   ├── reddit.py             # Reddit sentiment
│   └── crypto_social.py      # LunarCrush/Santiment
├── graph/
│   ├── hierarchical_graph.py # Main orchestration
│   └── engine.py             # Decision engine
├── tools/                    # Deterministic tools
├── context/                  # Shared state management
└── utils/
    └── llm_v2.py            # Model-agnostic LLM utility
```
4. **Risk Agent** → Checks risk constraints
5. **Decision Agent** (LLM) → Makes final decision
6. **Evaluator Agent** (LLM) → Validates and enforces JSON output

### Layer 4: FastAPI Service
- `POST /ai/decide` - Make trading decisions
- `GET /health` - Health check
- `GET /ai/status` - Engine status

## 📦 Installation

### Prerequisites
- Python 3.13+
- Poetry (for dependency management)
- Anthropic API key (for Claude)

### Setup

1. **Clone and install dependencies:**
```bash
cd ai_engine
poetry install
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Activate virtual environment:**
```bash
poetry shell
```

## 🚀 Usage

### Running the API Server

```bash
# Start the FastAPI server
poetry run uvicorn ai_engine.api.server:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### Making a Decision Request

#### Using cURL:

```bash
curl -X POST "http://localhost:8000/ai/decide" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USD",
    "prices": [50000, 50100, 50200, 50300, 50250, 50400, 50500, 50450, 50600, 50700],
    "volumes": [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500],
    "proposed_action": "buy",
    "proposed_size": 1000.0,
    "account_balance": 10000.0,
    "fear_greed_index": 65.0
  }'
```

#### Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/ai/decide",
    json={
        "symbol": "BTC/USD",
        "prices": [50000, 50100, 50200, 50300, 50250, 50400, 50500],
        "volumes": [1000, 1100, 1050, 1200, 1150, 1300, 1250],
        "proposed_action": "buy",
        "proposed_size": 1000.0,
        "account_balance": 10000.0,
    }
)

decision = response.json()
print(f"Action: {decision['action']}")
print(f"Confidence: {decision['confidence']}")
print(f"Reasoning: {decision['reasoning']}")
```

### Example Response

```json
{
  "symbol": "BTC/USD",
  "action": "buy",
  "confidence": 0.75,
  "reasoning": "Strong bullish signals from market (RSI oversold, bullish trend, EMA crossover) combined with positive ML prediction (75% up probability) and bullish sentiment. Risk checks passed.",
  "position_size": 1000.0,
  "stop_loss": 49500.0,
  "take_profit": 52000.0,
  "risk_score": 0.35,
  "timestamp": "2025-12-29T10:30:00Z",
  "processing_time_ms": 250.5,
  "request_id": "req_123456",
  "signals": {
    "market": "bullish",
    "ml": "bullish",
    "sentiment": "positive",
    "risk": "proceed"
  }
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ai_engine

# Run specific test file
poetry run pytest tests/test_tools.py

# Run with verbose output
poetry run pytest -v
```

## 📁 Project Structure

```
ai_engine/
├── tools/              # Deterministic tools (no LLM)
│   ├── market.py      # Market indicators
│   ├── ml.py          # ML predictions
│   ├── sentiment.py   # Sentiment analysis
│   ├── rules.py       # Rules evaluation
│   └── risk.py        # Risk management
│
├── context/           # Context building
│   ├── schema.py      # Pydantic schemas
│   └── builder.py     # Context builder
│
├── agents/            # LangGraph agents
│   ├── market_agent.py
│   ├── ml_agent.py
│   ├── sentiment_agent.py
│   ├── risk_agent.py
│   ├── decision_agent.py    # LLM-based
│   └── evaluator_agent.py   # LLM-based
│
├── graph/             # LangGraph workflow
│   ├── graph_definition.py
│   ├── engine.py
│   └── router.py
│
├── api/               # FastAPI service
│   ├── server.py
│   ├── routes.py
│   └── models.py
│
└── utils/             # Utilities
    ├── llm.py         # LangChain wrapper
    ├── json_guard.py  # JSON validation
    └── logger.py      # Logging

tests/
├── test_tools.py
├── test_agents.py
├── test_graph.py
└── test_api.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```env
# LLM Configuration
ANTHROPIC_API_KEY=your_api_key_here

# Optional: Override defaults
LOG_LEVEL=INFO
```

### User-Defined Rules

You can pass custom trading rules:

```json
{
  "rules": [
    {
      "name": "RSI Oversold Buy",
      "conditions": [
        {"field": "market.rsi", "operator": "lt", "value": 30}
      ],
      "action": "buy",
      "logic": "AND",
      "confidence": 0.8
    },
    {
      "name": "High Volatility Avoid",
      "conditions": [
        {"field": "ml.volatility", "operator": "gt", "value": 0.05}
      ],
      "action": "hold",
      "logic": "AND",
      "confidence": 0.9
    }
  ]
}
```

## 🔌 Integration with Argo Workflows

This engine is designed to be called by Argo Workflows:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: trading-decision
spec:
  entrypoint: make-decision
  templates:
  - name: make-decision
    http:
      url: http://ai-engine:8000/ai/decide
      method: POST
      body: |
        {
          "symbol": "{{workflow.parameters.symbol}}",
          "prices": {{workflow.parameters.prices}},
          "volumes": {{workflow.parameters.volumes}}
        }
```

## 📊 Development

### Code Formatting

```bash
# Format code
poetry run black ai_engine tests

# Sort imports
poetry run isort ai_engine tests

# Lint
poetry run ruff check ai_engine tests
```

### Adding New Tools

1. Create tool function in `ai_engine/tools/`
2. Import in `ai_engine/tools/__init__.py`
3. Call from `ContextBuilder.build_context()`

### Adding New Agents

1. Create agent function in `ai_engine/agents/`
2. Add to graph in `graph_definition.py`
3. Update workflow edges

## 🚨 Safety Features

- **Risk Blockers**: Prevents trades that violate risk constraints
- **JSON Validation**: Ensures all outputs are valid and safe
- **Confidence Scoring**: Every decision includes a confidence score
- **Stop Loss**: Automatic stop loss recommendations
- **Position Limits**: Enforces position size and exposure limits

## 📝 License

MIT License - see LICENSE file

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📧 Support

For issues or questions, please open a GitHub issue.

---

Built with ❤️ using LangChain, LangGraph, and FastAPI
# AI-Crypto-Trading-Copilot
