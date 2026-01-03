"""ML evaluator - LLM-based validation of ML predictions."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from ...utils.llm_v2 import get_llm, LLMConfig
from ...utils.logger import get_logger
from ...utils.json_fixer import fix_json_string
from .schema import MLSubgraphState, MLEvaluation

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


def ml_evaluator(state: MLSubgraphState) -> MLSubgraphState:
    """Evaluate ML worker output using LLM.
    
    Single responsibility: Judge quality and reliability of ML predictions.
    Does NOT make trading decisions - only evaluates prediction quality.
    
    Uses LCEL: prompt | llm | parser
    
    Args:
        state: State with worker_output to evaluate
        
    Returns:
        Updated state with evaluation populated
    """
    try:
        if not state.worker_output:
            raise ValueError("No worker output to evaluate")
        
        logger.info(f"ML evaluator validating {state.symbol}")
        
        # Create parser with JSON fixing
        parser = ResilientPydanticParser(pydantic_object=MLEvaluation)
        
        # Create prompt
        system_message = """You are an ML prediction quality evaluator.

Your job is to assess the QUALITY and RELIABILITY of ML predictions.
You do NOT make trading decisions - only evaluate prediction quality.

Check for:
1. Prediction confidence levels
2. Prediction clarity and consistency
3. Model quality indicators

Provide:
- is_valid: whether predictions look reliable
- confidence: how confident you are (0.0-1.0)
- quality_score: overall prediction quality (0.0-1.0)
- issues: list any concerns about predictions
- summary: brief prediction summary
- recommendation: how to use these predictions

{format_instructions}"""

        human_message = """Symbol: {symbol}

ML Predictions:
- Direction: {predicted_direction} (confidence: {direction_confidence:.2f})
- Volatility: {predicted_volatility} (score: {volatility_score:.2f})
- Prediction Quality: {prediction_quality}

Evaluate these ML predictions."""

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
                    "predicted_direction": state.worker_output.predicted_direction,
                    "direction_confidence": state.worker_output.direction_confidence,
                    "predicted_volatility": state.worker_output.predicted_volatility,
                    "volatility_score": state.worker_output.volatility_score,
                    "prediction_quality": state.worker_output.prediction_quality,
                    "format_instructions": parser.get_format_instructions(),
                })
                break  # Success, exit retry loop
            except Exception as e:
                last_error = str(e)
                logger.warning(f"ML evaluator attempt {attempt + 1}/{max_retries} failed: {last_error[:200]}")
                if attempt < max_retries - 1:
                    # Update prompt with error feedback for next attempt
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_message),
                        ("human", human_message + f"\n\n[RETRY {attempt + 2}/{max_retries}] Previous attempt failed: {last_error[:300]}\nPlease provide valid JSON with ALL required fields."),
                    ])
                    chain = prompt | llm | parser
                else:
                    raise  # Re-raise on final attempt
        
        logger.info(
            f"ML evaluator completed: valid={evaluation.is_valid}, "
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
        
        return MLSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=state.worker_output,
            evaluation=evaluation,
            retry_count=new_retry_count,
            max_retries=state.max_retries,
            evaluator_feedback=evaluator_feedback,
            completed=evaluation.is_valid,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"ML evaluator error: {e}", exc_info=True)
        
        return MLSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=state.worker_output,
            evaluation=MLEvaluation(
                is_valid=False,
                confidence=0.0,
                quality_score=0.0,
                issues=[f"Evaluation failed: {str(e)}"],
                summary="Evaluation error",
                recommendation="Unable to evaluate - use predictions with caution",
            ),
            completed=True,
            error=f"Evaluator failed: {str(e)}",
        )
