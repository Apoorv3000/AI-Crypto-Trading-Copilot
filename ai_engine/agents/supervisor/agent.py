"""Supervisor agent for generating execution plans.

The supervisor analyzes user requests and generates:
- Trading rules extracted from natural language
- Execution plan for which subgraphs to invoke
- Initial context setup

Uses LCEL: prompt | llm | parser
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from ...context.schema import DecisionContext
from ...utils.llm_v2 import get_llm, LLMConfig
from ...utils.logger import get_logger
from ...utils.json_fixer import fix_json_string

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


class SupervisorPlan(BaseModel):
    """Supervisor's execution plan."""
    
    trading_rules: list[str] = Field(
        description="Extracted trading rules from user request"
    )
    required_subgraphs: list[str] = Field(
        description="Which subgraphs are needed (market, ml, sentiment, risk)"
    )
    execution_strategy: str = Field(
        description="How to orchestrate the subgraphs"
    )
    reasoning: str = Field(
        description="Why this plan was chosen"
    )


def supervisor_agent(context: DecisionContext) -> DecisionContext:
    """Generate execution plan from user request.
    
    This is the top-level orchestrator that:
    1. Analyzes the user's request
    2. Extracts trading rules
    3. Generates an execution plan
    
    Args:
        context: Current decision context
        
    Returns:
        Updated context with supervisor_plan
    """
    logger.info(f"Supervisor analyzing request for {context.symbol}")
    
    try:
        # Create parser with JSON fixing
        parser = ResilientPydanticParser(pydantic_object=SupervisorPlan)
        
        # Create prompt
        system_message = """You are a trading strategy supervisor.

Your job is to analyze user requests and create an execution plan.

Extract:
1. Trading rules (e.g., "only buy if confidence > 70%", "respect 2% stop loss")
2. Required analysis (technical, sentiment, ML predictions, risk checks)
3. Execution strategy (which subgraphs to run, in what order)

Available subgraphs:
- market: Technical analysis (RSI, EMA, volume trends)
- ml: Machine learning predictions (direction, volatility)
- sentiment: Social sentiment (Twitter, Reddit, news)
- risk: Risk validation (position size, stop loss, exposure)

Guidelines:
- For simple questions ("what do you think about ETH?"), use all subgraphs
- For specific questions ("check ETH technical"), focus on relevant subgraphs
- Always include risk subgraph if considering trades
- Extract explicit and implicit rules from user's language

{format_instructions}"""

        human_message = """User Request: {user_request}

Symbol: {symbol}
Request ID: {request_id}
{enriched_rules_section}

Analyze this request and create an execution plan."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message),
        ])
        
        # Build enriched rules section if available
        enriched_rules_section = ""
        if context.trading_rules:
            rules_text = "\n".join(f"  {i+1}. {rule}" for i, rule in enumerate(context.trading_rules))
            enriched_rules_section = f"\n\nEnriched Trading Rules (from rule enrichment graph):\nThese are structured rules created by the user. Use them to guide your analysis:\n{rules_text}"
        
        # Build LCEL chain
        llm = get_llm(**LLMConfig.SUPERVISOR)
        chain = prompt | llm | parser
        
        # Invoke
        plan = chain.invoke({
            "user_request": context.user_request or f"Analyze {context.symbol}",
            "symbol": context.symbol,
            "request_id": context.request_id,
            "enriched_rules_section": enriched_rules_section,
            "format_instructions": parser.get_format_instructions(),
        })
        
        # Update context
        context.supervisor_plan = plan.model_dump()
        context.trading_rules = plan.trading_rules
        
        logger.info(
            f"Supervisor plan created: {len(plan.required_subgraphs)} subgraphs, "
            f"{len(plan.trading_rules)} rules"
        )
        logger.debug(f"Plan: {plan.reasoning}")
        
    except Exception as e:
        logger.error(f"Supervisor error: {e}", exc_info=True)
        # Fallback plan
        context.supervisor_plan = {
            "trading_rules": ["Use all available data"],
            "required_subgraphs": ["market", "ml", "sentiment", "risk"],
            "execution_strategy": "Run all subgraphs in parallel where possible",
            "reasoning": f"Error in supervisor, using default plan: {str(e)}",
        }
        context.trading_rules = ["Use all available data"]
    
    return context
