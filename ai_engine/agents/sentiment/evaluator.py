"""Sentiment evaluator - LLM-based validation of sentiment analysis."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from ...utils.llm_v2 import get_llm, LLMConfig
from ...utils.logger import get_logger
from ...utils.json_fixer import fix_json_string
from .schema import SentimentSubgraphState, SentimentEvaluation

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


def sentiment_evaluator(state: SentimentSubgraphState) -> SentimentSubgraphState:
    """Evaluate sentiment worker output using LLM.
    
    Single responsibility: Judge quality and confidence of sentiment data.
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
        
        logger.info(f"Sentiment evaluator validating {state.symbol}")
        
        # Create parser with JSON fixing
        parser = ResilientPydanticParser(pydantic_object=SentimentEvaluation)
        
        # Create prompt
        system_message = """You are a sentiment analysis quality evaluator.

Your job is to assess the QUALITY and RELIABILITY of sentiment data.
You do NOT make trading decisions - only evaluate data quality.

Check for:
1. Data source reliability (volume of mentions/articles)
2. Sentiment consistency (do sources agree?)
3. Data recency and relevance

Provide:
- is_valid: whether data looks reliable
- confidence: how confident you are (0.0-1.0)
- quality_score: overall data quality (0.0-1.0)
- issues: list any problems or concerns
- summary: brief sentiment summary
- recommendation: what this sentiment suggests

{format_instructions}"""

        human_message = """Symbol: {symbol}

Sentiment Data:
- Social: {social_sentiment:.2f} ({social_volume} mentions)
- News: {news_sentiment:.2f} ({news_count} articles)
- Market: {market_sentiment:.2f}
- Overall: {overall_sentiment:.2f} ({sentiment_signal})

Evaluate this sentiment analysis."""

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
                    "social_sentiment": state.worker_output.social_sentiment,
                    "social_volume": state.worker_output.social_volume,
                    "news_sentiment": state.worker_output.news_sentiment,
                    "news_count": state.worker_output.news_count,
                    "market_sentiment": state.worker_output.market_sentiment,
                    "overall_sentiment": state.worker_output.overall_sentiment,
                    "sentiment_signal": state.worker_output.sentiment_signal,
                    "format_instructions": parser.get_format_instructions(),
                })
                break  # Success, exit retry loop
            except Exception as e:
                last_error = str(e).replace("{", "{{").replace("}", "}}")  # Escape braces for f-string
                logger.warning(f"Sentiment evaluator attempt {attempt + 1}/{max_retries} failed: {last_error[:200]}")
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
            f"Sentiment evaluator completed: valid={evaluation.is_valid}, "
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
        
        return SentimentSubgraphState(
            symbol=state.symbol,
            worker_output=state.worker_output,
            evaluation=evaluation,
            retry_count=new_retry_count,
            max_retries=state.max_retries,
            evaluator_feedback=evaluator_feedback,
            completed=evaluation.is_valid,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Sentiment evaluator error: {e}", exc_info=True)
        
        return SentimentSubgraphState(
            symbol=state.symbol,
            worker_output=state.worker_output,
            evaluation=SentimentEvaluation(
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
