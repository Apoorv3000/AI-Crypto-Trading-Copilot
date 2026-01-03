"""Risk evaluator - LLM-based validation of risk checks."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from ...utils.llm_v2 import get_llm, LLMConfig
from ...utils.logger import get_logger
from ...utils.json_fixer import fix_json_string
from .schema import RiskSubgraphState, RiskEvaluation

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


def risk_evaluator(state: RiskSubgraphState) -> RiskSubgraphState:
    """Evaluate risk worker output using LLM.
    
    Single responsibility: Judge quality and completeness of risk checks.
    Does NOT make trading decisions - only evaluates risk validation.
    
    Uses LCEL: prompt | llm | parser
    
    Args:
        state: State with worker_output to evaluate
        
    Returns:
        Updated state with evaluation populated
    """
    try:
        if not state.worker_output:
            raise ValueError("No worker output to evaluate")
        
        logger.info(f"Risk evaluator validating {state.symbol}")
        
        # Create parser with JSON fixing
        parser = ResilientPydanticParser(pydantic_object=RiskEvaluation)
        
        # Create prompt
        system_message = """You are a risk management quality evaluator.

Your job is to assess the COMPLETENESS and APPROPRIATENESS of risk checks.
You do NOT make trading decisions - only evaluate risk analysis quality.

Check for:
1. All necessary risk checks performed
2. Risk thresholds are appropriate
3. No critical risks missed

Provide:
- is_valid: whether risk analysis is complete
- confidence: how confident you are (0.0-1.0)
- quality_score: overall risk check quality (0.0-1.0)
- issues: list any missing checks or concerns
- summary: brief risk summary
- recommendation: risk management advice

{format_instructions}"""

        human_message = """Symbol: {symbol}
Action: {action} ({quantity} shares at ${price:.2f})

Risk Checks:
- Stop Loss: {stop_loss_check} - {stop_loss_message}
- Position Size: {position_size_check} - {position_size_message}
- Exposure: {exposure_check} - {exposure_message}

Overall: {all_checks_passed}
Risk Level: {risk_level}

Evaluate this risk analysis."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message),
        ])
        
        # Build LCEL chain
        llm = get_llm(**LLMConfig.EVALUATORS)  # Use configured evaluator LLM
        chain = prompt | llm | parser
        
        # Invoke with retry logic (up to 3 attempts)
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                evaluation = chain.invoke({
                    "symbol": state.symbol,
                    "action": state.proposed_action,
                    "quantity": state.proposed_quantity,
                    "price": state.current_price,
                    "stop_loss_check": state.worker_output.stop_loss_check,
                    "stop_loss_message": state.worker_output.stop_loss_message,
                    "position_size_check": state.worker_output.position_size_check,
                    "position_size_message": state.worker_output.position_size_message,
                    "exposure_check": state.worker_output.exposure_check,
                    "exposure_message": state.worker_output.exposure_message,
                    "all_checks_passed": state.worker_output.all_checks_passed,
                    "risk_level": state.worker_output.risk_level,
                    "format_instructions": parser.get_format_instructions(),
                })
                break  # Success, exit retry loop
            except Exception as e:
                last_error = str(e).replace("{", "{{").replace("}", "}}")  # Escape braces for f-string
                logger.warning(f"Risk evaluator attempt {attempt + 1}/{max_retries} failed: {last_error[:200]}")
                if attempt < max_retries - 1:
                    # Update prompt with error feedback for next attempt
                    retry_message = f"\n\n[RETRY {attempt + 2}/{max_retries}] Previous attempt failed: {last_error[:300]}\nPlease provide valid JSON with ALL required fields."
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_message),
                        ("human", human_message + retry_message),
                    ])
                    chain = prompt | llm | parser
                else:
                    raise  # Re-raise on final attempt
        
        logger.info(
            f"Risk evaluator completed: valid={evaluation.is_valid}, "
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
        
        return RiskSubgraphState(
            symbol=state.symbol,
            current_price=state.current_price,
            proposed_action=state.proposed_action,
            proposed_quantity=state.proposed_quantity,
            stop_loss=state.stop_loss,
            take_profit=state.take_profit,
            worker_output=state.worker_output,
            evaluation=evaluation,
            retry_count=new_retry_count,
            max_retries=state.max_retries,
            evaluator_feedback=evaluator_feedback,
            completed=evaluation.is_valid,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Risk evaluator error: {e}", exc_info=True)
        
        return RiskSubgraphState(
            symbol=state.symbol,
            current_price=state.current_price,
            proposed_action=state.proposed_action,
            proposed_quantity=state.proposed_quantity,
            stop_loss=state.stop_loss,
            take_profit=state.take_profit,
            worker_output=state.worker_output,
            evaluation=RiskEvaluation(
                is_valid=False,
                confidence=0.0,
                quality_score=0.0,
                issues=[f"Evaluation failed: {str(e)}"],
                summary="Evaluation error",
                recommendation="Unable to evaluate - proceed with extreme caution",
            ),
            completed=True,
            error=f"Evaluator failed: {str(e)}",
        )
