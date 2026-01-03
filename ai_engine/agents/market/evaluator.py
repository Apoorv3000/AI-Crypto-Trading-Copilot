"""Market evaluator - LLM-based validation of market analysis."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from ...utils.llm_v2 import get_llm, LLMConfig
from ...utils.logger import get_logger
from ...utils.json_fixer import fix_json_string
from .schema import MarketSubgraphState, MarketEvaluation

logger = get_logger(__name__)


class ResilientPydanticParser(PydanticOutputParser):
    """Pydantic parser that fixes common JSON issues before parsing."""
    
    def parse(self, text: str):
        """Parse with JSON fixing."""
        try:
            # Try normal parsing first
            return super().parse(text)
        except OutputParserException as e:
            # Try fixing JSON
            try:
                fixed_text = fix_json_string(text)
                return super().parse(fixed_text)
            except Exception:
                # Re-raise original error if fix didn't work
                raise e


def market_evaluator(state: MarketSubgraphState) -> MarketSubgraphState:
    """Evaluate market worker output using LLM.
    
    Single responsibility: Judge quality and confidence of market analysis.
    Does NOT make trading decisions - only evaluates data quality.
    
    Uses LCEL: prompt | llm | parser
    
    Args:
        state: State with worker_output to evaluate
        
    Returns:
        Updated state with evaluation populated
    """
    try:
        if not state.worker_output:
            raise ValueError("No worker output to evaluate")
        
        logger.info(f"Market evaluator validating {state.symbol}")
        
        # Create parser with JSON fixing
        parser = ResilientPydanticParser(pydantic_object=MarketEvaluation)
        
        # Create prompt
        system_message = """You are a technical analysis quality evaluator.

Your job is to assess the QUALITY and CONSISTENCY of market indicator data.
You do NOT make trading decisions - only evaluate data quality.

Check for:
1. Indicator consistency (do RSI, EMA, volume align?)
2. Data quality (are values reasonable?)
3. Signal clarity (are signals contradictory?)

Provide:
- is_valid: whether data looks correct
- confidence: how confident you are (0.0-1.0)
- quality_score: overall data quality (0.0-1.0)
- issues: list any problems or inconsistencies
- summary: brief market condition summary
- recommendation: what this data suggests (NOT a trading decision)

{format_instructions}"""

        human_message = """Symbol: {symbol}

Market Indicators:
- RSI: {rsi:.1f} ({rsi_signal})
- EMA: Short={ema_short:.2f}, Long={ema_long:.2f} ({ema_signal})
- Volume: {volume_ratio:.2f}x average ({volume_signal})
- Trend: {trend_direction} (strength: {trend_strength:.2f})

Evaluate this market analysis."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message),
        ])
        
        # Build LCEL chain with retry
        llm = get_llm(**LLMConfig.EVALUATORS)  # Use configured evaluator LLM
        chain = prompt | llm | parser
        
        # Invoke with retry logic (up to 3 attempts)
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                evaluation = chain.invoke({
                    "symbol": state.symbol,
                    "rsi": state.worker_output.rsi,
                    "rsi_signal": state.worker_output.rsi_signal,
                    "ema_short": state.worker_output.ema_short,
                    "ema_long": state.worker_output.ema_long,
                    "ema_signal": state.worker_output.ema_signal,
                    "volume_ratio": state.worker_output.volume_ratio,
                    "volume_signal": state.worker_output.volume_signal,
                    "trend_direction": state.worker_output.trend_direction,
                    "trend_strength": state.worker_output.trend_strength,
                    "format_instructions": parser.get_format_instructions(),
                })
                break  # Success, exit retry loop
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Market evaluator attempt {attempt + 1}/{max_retries} failed: {last_error}")
                if attempt < max_retries - 1:
                    # Add error feedback to prompt for retry
                    human_message += f"\n\n[Previous attempt failed with error: {last_error}. Please provide valid JSON with all required fields.]"
        
        logger.info(
            f"Market evaluator completed: valid={evaluation.is_valid}, "
            f"confidence={evaluation.confidence:.2f}, quality={evaluation.quality_score:.2f}"
        )
        
        # Prepare feedback for worker retry if validation failed
        evaluator_feedback = None
        new_retry_count = state.retry_count
        
        if not evaluation.is_valid:
            evaluator_feedback = (
                f"Validation failed (confidence={evaluation.confidence:.2f}, "
                f"quality={evaluation.quality_score:.2f}). Issues: {', '.join(evaluation.issues)}"
            )
            new_retry_count = state.retry_count + 1
        
        return MarketSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=state.worker_output,
            evaluation=evaluation,
            retry_count=new_retry_count,
            max_retries=state.max_retries,
            evaluator_feedback=evaluator_feedback,
            completed=evaluation.is_valid,  # Only complete if validation passed
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Market evaluator error: {e}", exc_info=True)
        
        # Return with default evaluation on error
        return MarketSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=state.worker_output,
            evaluation=MarketEvaluation(
                is_valid=False,
                confidence=0.0,
                quality_score=0.0,
                issues=[f"Evaluation failed: {str(e)}"],
                summary="Evaluation error",
                recommendation="Unable to evaluate - treat with caution",
            ),
            completed=True,
            error=f"Evaluator failed: {str(e)}",
        )
