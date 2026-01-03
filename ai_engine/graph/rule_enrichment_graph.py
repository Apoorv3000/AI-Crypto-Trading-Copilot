"""Rule Enrichment Graph - Convert vague queries to structured trading rules.

This LangGraph takes a natural language query from the user and converts it into
a structured trading rule with human-in-the-loop verification at each step.

Flow:
1. Parse Intent - Understand what the user wants
2. Identify Missing Info - Check what details are needed (thresholds, timeframes, etc.)
3. Generate Questions - Ask clarifying questions
4. Collect Answers - Get user input (terminal prompts)
5. Validate Rule - Ensure rule is complete and valid
6. Human Verification - Show final rule, ask user to confirm/edit
7. Output Structured Rule - Ready for execution
"""

from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv

# Import get_llm - handle both module and direct execution
try:
    from ai_engine.utils.llm_v2 import get_llm
except ImportError:
    from ..utils.llm_v2 import get_llm

# Load environment variables - override any shell variables with .env values
load_dotenv(override=True)


# ============================================================================
# STATE SCHEMA
# ============================================================================

class RuleEnrichmentState(BaseModel):
    """State for rule enrichment graph."""
    
    # Input
    user_query: str = Field(description="Raw user query (e.g., 'buy when RSI is low')")
    
    # Intent parsing
    parsed_intent: Optional[dict] = Field(
        default=None,
        description="Parsed intent: action, indicators, conditions"
    )
    
    # Missing information
    missing_info: list[str] = Field(
        default_factory=list,
        description="List of missing details (thresholds, timeframes, etc.)"
    )
    
    # Questions and answers
    clarifying_questions: list[str] = Field(
        default_factory=list,
        description="Questions to ask the user"
    )
    user_answers: dict[str, str] = Field(
        default_factory=dict,
        description="User's answers to questions"
    )
    
    # Structured rule
    structured_rule: Optional[dict] = Field(
        default=None,
        description="Final structured trading rule"
    )
    
    # Validation
    is_valid: bool = Field(default=False, description="Whether rule is valid")
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Validation errors if any"
    )
    
    # Human verification
    user_confirmed: bool = Field(default=False, description="User confirmed the rule")
    user_modifications: Optional[str] = Field(
        default=None,
        description="User's modifications to the rule"
    )
    
    # Metadata
    completed: bool = Field(default=False, description="Workflow completed")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    model_config = {"arbitrary_types_allowed": True}


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def parse_intent_node(state: RuleEnrichmentState) -> dict:
    """Parse user's intent from natural language query.
    
    Extracts:
    - Action: buy/sell/hold
    - Indicators: RSI, EMA, volume, etc.
    - Conditions: thresholds, comparisons
    - Logic: AND/OR
    """
    llm = get_llm(temperature=0.0)
    
    prompt = f"""Parse this trading query into structured components:

User Query: "{state.user_query}"

Extract:
1. **Action**: buy, sell, or hold
2. **Indicators**: What market indicators are mentioned? (RSI, EMA, volume, price, trend, etc.)
3. **Conditions**: What are the conditions? (e.g., "RSI < 30", "EMA crossed", "volume high")
4. **Thresholds**: Are there specific numbers mentioned?
5. **Timeframe**: Is there a timeframe mentioned? (e.g., "for 3 days", "until price reaches X")
6. **Logic**: AND or OR (if multiple conditions)

Return a JSON object with these fields:
{{
  "action": "buy" | "sell" | "hold",
  "indicators": ["indicator1", "indicator2", ...],
  "conditions": ["condition1", "condition2", ...],
  "thresholds": {{"indicator": value, ...}},
  "timeframe": "description" | null,
  "logic": "AND" | "OR"
}}

Be precise and extract all mentioned details."""

    response = llm.invoke(prompt)
    
    # Parse JSON from response
    import json
    try:
        # Extract JSON from markdown code block if present
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        parsed_intent = json.loads(content)
        
        return {
            "parsed_intent": parsed_intent
        }
    except Exception as e:
        return {
            "error": f"Failed to parse intent: {str(e)}",
            "parsed_intent": None
        }


def identify_missing_info_node(state: RuleEnrichmentState) -> dict:
    """Identify what information is missing to create a complete rule.
    
    Checks:
    - Are thresholds specified? (e.g., RSI < X, but X is missing)
    - Is timeframe clear?
    - Are stop loss / take profit defined?
    - Is position size mentioned?
    - Are risk parameters set?
    """
    llm = get_llm(temperature=0.0)
    
    prompt = f"""Analyze this parsed trading intent and identify missing information:

User Query: "{state.user_query}"

Parsed Intent:
{state.parsed_intent}

Check what's missing to create a complete, executable trading rule:
1. **Threshold Values**: Are numeric thresholds specified? (e.g., "RSI < 30" vs vague "low RSI")
2. **Timeframe**: Is the timeframe clear? (e.g., "hold for 3 days" vs vague "hold")
3. **Position Size**: Is quantity or position size specified?
4. **Risk Parameters**: Stop loss, take profit, max risk percentage?
5. **Condition Specificity**: Are conditions clear enough? (e.g., "EMA crossed" - which EMAs?)

Return a JSON array of missing information items:
[
  "specific detail needed",
  "another detail needed",
  ...
]

If everything is complete, return an empty array: []

Be thorough - we need ALL details to execute the rule safely."""

    response = llm.invoke(prompt)
    
    import json
    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        missing_info = json.loads(content)
        
        return {
            "missing_info": missing_info if isinstance(missing_info, list) else []
        }
    except Exception as e:
        return {
            "error": f"Failed to identify missing info: {str(e)}",
            "missing_info": []
        }


def generate_questions_node(state: RuleEnrichmentState) -> dict:
    """Generate clarifying questions based on missing information."""
    
    if not state.missing_info:
        return {"clarifying_questions": []}
    
    llm = get_llm(temperature=0.3)
    
    prompt = f"""Generate clear, specific questions to fill in missing information:

User Query: "{state.user_query}"
Parsed Intent: {state.parsed_intent}
Missing Information: {state.missing_info}

For each missing piece of information, create ONE specific question that will help the user provide the needed detail.

Guidelines:
- Be specific and actionable
- Provide examples or ranges when helpful
- Ask one thing at a time
- Use natural language, not technical jargon
- Include context about why it's needed

Return a JSON array of questions:
[
  "Question 1?",
  "Question 2?",
  ...
]

Example:
If missing "RSI threshold", ask: "What RSI value should trigger the buy? (Typically oversold is below 30)"
If missing "position size", ask: "How much would you like to invest? (e.g., $1000 or 1 ETH)"
"""

    response = llm.invoke(prompt)
    
    import json
    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        questions = json.loads(content)
        
        return {
            "clarifying_questions": questions if isinstance(questions, list) else []
        }
    except Exception as e:
        return {
            "error": f"Failed to generate questions: {str(e)}",
            "clarifying_questions": []
        }


def collect_answers_node(state: RuleEnrichmentState) -> dict:
    """Collect answers from user via terminal prompts.
    
    This is the human-in-the-loop step where we ask clarifying questions.
    """
    if not state.clarifying_questions:
        return {"user_answers": {}}
    
    print("\n" + "="*70)
    print("📋 RULE CLARIFICATION - We need some details")
    print("="*70)
    print(f"\nYour query: \"{state.user_query}\"")
    print("\nPlease answer the following questions to complete your trading rule:\n")
    
    answers = {}
    
    import sys
    for i, question in enumerate(state.clarifying_questions, 1):
        print(f"\n{i}. {question}")
        sys.stdout.flush()  # Ensure prompt is visible
        answer = input("   Your answer: ").strip()
        
        # Store with question as key for context
        answers[question] = answer
    
    print("\n" + "="*70)
    print("✓ Thank you! Building your structured rule...")
    print("="*70 + "\n")
    
    return {"user_answers": answers}


def validate_and_build_rule_node(state: RuleEnrichmentState) -> dict:
    """Build structured rule from parsed intent and user answers.
    
    Creates a rule in the format expected by the trading system:
    {
        "name": "Rule name",
        "conditions": [
            {"field": "market.rsi", "operator": "lt", "value": 30}
        ],
        "action": "buy",
        "logic": "AND",
        "confidence": 0.8,
        "metadata": {...}
    }
    """
    llm = get_llm(temperature=0.0)
    
    prompt = f"""Build a structured trading rule from this information:

Original Query: "{state.user_query}"
Parsed Intent: {state.parsed_intent}
User Answers: {state.user_answers}

Create a complete, executable trading rule with this EXACT format:
{{
  "name": "Descriptive rule name",
  "conditions": [
    {{
      "field": "market.rsi",  // Available: market.rsi, market.ema_short, market.ema_long, market.volume_ratio, market.trend_direction, sentiment.sentiment_signal, etc.
      "operator": "lt",  // Available: gt, lt, gte, lte, eq, ne
      "value": 30  // Numeric or string value
    }}
  ],
  "action": "buy",  // Must be: buy, sell, or hold
  "logic": "AND",  // Must be: AND or OR (if multiple conditions)
  "confidence": 0.8,  // Your confidence in this rule (0.0-1.0)
  "metadata": {{
    "position_size": "value from user or default",
    "stop_loss": "value from user or null",
    "take_profit": "value from user or null",
    "max_risk_percent": "value from user or 2",
    "timeframe": "value from user or null",
    "description": "Natural language description of the rule"
  }}
}}

CRITICAL REQUIREMENTS:
1. Map user's indicators to correct field paths (e.g., "RSI" → "market.rsi")
2. Use correct operators (gt=greater than, lt=less than, etc.)
3. Convert user's natural language thresholds to numeric values
4. Include ALL information from user answers in metadata
5. Set a reasonable confidence based on rule specificity
6. Action MUST be exactly "buy", "sell", or "hold"

Available field paths:
- market.rsi (0-100)
- market.rsi_signal (oversold/neutral/overbought)
- market.ema_short, market.ema_long (numeric)
- market.ema_signal (bullish/bearish/neutral)
- market.volume_ratio (numeric, >1 is high volume)
- market.volume_signal (high/normal/low)
- market.trend_direction (bullish/bearish/sideways)
- market.trend_strength (0-1)
- sentiment.sentiment_signal (positive/negative/neutral)
- sentiment.average_sentiment (-1 to 1)

Return ONLY the JSON object, no explanation."""

    response = llm.invoke(prompt)
    
    import json
    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        structured_rule = json.loads(content)
        
        # Validate required fields
        required_fields = ["name", "conditions", "action", "logic"]
        missing_fields = [f for f in required_fields if f not in structured_rule]
        
        if missing_fields:
            return {
                "structured_rule": None,
                "is_valid": False,
                "validation_errors": [f"Missing required field: {f}" for f in missing_fields]
            }
        
        # Validate action
        if structured_rule["action"] not in ["buy", "sell", "hold"]:
            return {
                "structured_rule": None,
                "is_valid": False,
                "validation_errors": [f"Invalid action: {structured_rule['action']}. Must be buy, sell, or hold."]
            }
        
        # Validate conditions
        if not structured_rule["conditions"] or not isinstance(structured_rule["conditions"], list):
            return {
                "structured_rule": None,
                "is_valid": False,
                "validation_errors": ["Conditions must be a non-empty list"]
            }
        
        return {
            "structured_rule": structured_rule,
            "is_valid": True,
            "validation_errors": []
        }
        
    except Exception as e:
        return {
            "structured_rule": None,
            "is_valid": False,
            "validation_errors": [f"Failed to build rule: {str(e)}"],
            "error": str(e)
        }


def human_verification_node(state: RuleEnrichmentState) -> dict:
    """Show structured rule to user and ask for confirmation/modifications.
    
    This is the final human-in-the-loop step before returning the rule.
    """
    if not state.is_valid or not state.structured_rule:
        print("\n⚠️  Rule validation failed. Cannot proceed.")
        print(f"Errors: {state.validation_errors}")
        return {
            "user_confirmed": False,
            "completed": True
        }
    
    import json
    
    print("\n" + "="*70)
    print("📊 STRUCTURED TRADING RULE - Review and Confirm")
    print("="*70)
    
    print("\n🎯 Rule Summary:")
    print(f"   Name: {state.structured_rule['name']}")
    print(f"   Action: {state.structured_rule['action'].upper()}")
    print(f"   Logic: {state.structured_rule['logic']}")
    
    print("\n📋 Conditions:")
    for i, condition in enumerate(state.structured_rule['conditions'], 1):
        op_map = {'gt': '>', 'lt': '<', 'gte': '>=', 'lte': '<=', 'eq': '==', 'ne': '!='}
        op_symbol = op_map.get(condition['operator'], condition['operator'])
        print(f"   {i}. {condition['field']} {op_symbol} {condition['value']}")
    
    if 'metadata' in state.structured_rule:
        print("\n⚙️  Metadata:")
        for key, value in state.structured_rule['metadata'].items():
            if value is not None:
                print(f"   {key}: {value}")
    
    print("\n📄 Full Rule (JSON):")
    print(json.dumps(state.structured_rule, indent=2))
    
    print("\n" + "="*70)
    print("\nWhat would you like to do?")
    print("  [y] Confirm and use this rule")
    print("  [n] Cancel")
    print("  [e] Edit (provide modifications in natural language)")
    
    import sys
    sys.stdout.flush()  # Ensure output is displayed before input
    
    choice = input("\nYour choice (y/n/e): ").strip().lower()
    
    if choice == 'y':
        print("\n✓ Rule confirmed! Ready for execution.\n")
        return {
            "user_confirmed": True,
            "completed": True
        }
    elif choice == 'e':
        modifications = input("\nDescribe your modifications: ").strip()
        print("\n⚠️  Modification feature not yet implemented. Please confirm or cancel.\n")
        # TODO: Implement modification loop
        return {
            "user_confirmed": False,
            "user_modifications": modifications,
            "completed": True
        }
    else:
        print("\n✗ Rule cancelled.\n")
        return {
            "user_confirmed": False,
            "completed": True
        }


# ============================================================================
# CONDITIONAL EDGES
# ============================================================================

def should_ask_questions(state: RuleEnrichmentState) -> Literal["collect_answers", "build_rule"]:
    """Route based on whether we need to ask clarifying questions."""
    if state.missing_info and state.clarifying_questions:
        return "collect_answers"
    return "build_rule"


def should_continue_after_verification(state: RuleEnrichmentState) -> Literal["END"]:
    """Always end after verification."""
    return "END"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_rule_enrichment_graph() -> StateGraph:
    """Build the rule enrichment graph.
    
    Flow:
    START → parse_intent → identify_missing → generate_questions → 
    [if questions] → collect_answers → build_rule → human_verification → END
    [if no questions] → build_rule → human_verification → END
    """
    
    graph = StateGraph(RuleEnrichmentState)
    
    # Add nodes
    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("identify_missing", identify_missing_info_node)
    graph.add_node("generate_questions", generate_questions_node)
    graph.add_node("collect_answers", collect_answers_node)
    graph.add_node("build_rule", validate_and_build_rule_node)
    graph.add_node("human_verification", human_verification_node)
    
    # Add edges
    graph.set_entry_point("parse_intent")
    graph.add_edge("parse_intent", "identify_missing")
    graph.add_edge("identify_missing", "generate_questions")
    
    # Conditional: ask questions or skip to rule building
    graph.add_conditional_edges(
        "generate_questions",
        should_ask_questions,
        {
            "collect_answers": "collect_answers",
            "build_rule": "build_rule"
        }
    )
    
    graph.add_edge("collect_answers", "build_rule")
    graph.add_edge("build_rule", "human_verification")
    
    graph.add_conditional_edges(
        "human_verification",
        should_continue_after_verification,
        {"END": END}
    )
    
    return graph.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def enrich_rule(user_query: str) -> dict | None:
    """Main entry point to enrich a user query into a structured rule.
    
    Args:
        user_query: Natural language trading query
        
    Returns:
        Structured trading rule if confirmed, None if cancelled
    """
    graph = build_rule_enrichment_graph()
    
    initial_state = RuleEnrichmentState(user_query=user_query)
    
    try:
        final_state = graph.invoke(initial_state)
        
        if final_state.get("user_confirmed") and final_state.get("structured_rule"):
            return final_state["structured_rule"]
        else:
            return None
            
    except Exception as e:
        print(f"\n❌ Error during rule enrichment: {str(e)}")
        return None


if __name__ == "__main__":
    """Test the rule enrichment graph."""
    
    # Example 1: Vague query
    print("\n" + "="*70)
    print("Testing Rule Enrichment Graph")
    print("="*70)
    
    test_query = "buy ETH when RSI is low"
    
    print(f"\n🔍 Input Query: \"{test_query}\"")
    print("\n⏳ Processing...\n")
    
    rule = enrich_rule(test_query)
    
    if rule:
        print("\n✅ SUCCESS - Structured Rule Generated:")
        import json
        print(json.dumps(rule, indent=2))
    else:
        print("\n❌ Rule enrichment cancelled or failed.")
