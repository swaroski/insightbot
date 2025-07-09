import json
from typing import Dict, Any
from openai import OpenAI
from loguru import logger
from app.config import settings
from app.agents.state import AgentState
from app.models.schemas import EvaluationResult, Source


class EvaluatorAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def evaluate_response(self, state: AgentState) -> AgentState:
        """Evaluate the quality of the generated response"""
        try:
            query = state["original_query"]
            final_answer = state.get("final_answer", "")
            sources = state.get("retrieved_sources", [])
            confidence_score = state.get("confidence_score", 0.5)
            
            # Create evaluation prompt
            evaluation_prompt = self._create_evaluation_prompt(query, final_answer, sources)
            
            # Perform evaluation
            response = self.client.chat.completions.create(
                model=settings.evaluation_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1
            )
            
            # Parse evaluation result
            evaluation_data = json.loads(response.choices[0].message.content)
            
            # Create evaluation result
            evaluation_result = EvaluationResult(
                score=evaluation_data["overall_score"],
                rationale=evaluation_data["rationale"],
                criteria=evaluation_data["criteria"]
            )
            
            # Update state
            state["evaluation_result"] = evaluation_result
            
            # Add evaluation step to execution trace
            if "agent_steps" not in state:
                state["agent_steps"] = []
            
            state["agent_steps"].append({
                "agent": "evaluator",
                "action": "evaluate_response",
                "input": {
                    "query": query,
                    "answer_length": len(final_answer),
                    "sources_count": len(sources),
                    "confidence_score": confidence_score
                },
                "output": {
                    "evaluation_score": evaluation_result.score,
                    "criteria_scores": evaluation_result.criteria
                },
                "status": "success"
            })
            
            logger.info(f"Response evaluated with score: {evaluation_result.score}")
            return state
            
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            
            # Fallback evaluation
            fallback_score = self._calculate_fallback_score(state)
            state["evaluation_result"] = EvaluationResult(
                score=fallback_score,
                rationale="Evaluation failed, using fallback scoring based on available metrics",
                criteria={
                    "accuracy": fallback_score,
                    "completeness": fallback_score,
                    "relevance": fallback_score,
                    "clarity": fallback_score,
                    "coherence": fallback_score
                }
            )
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Evaluation error: {str(e)}")
            
            return state
    
    def _create_evaluation_prompt(self, query: str, answer: str, sources: list) -> str:
        """Create evaluation prompt"""
        
        sources_info = f"Based on {len(sources)} sources" if sources else "No sources available"
        
        prompt = f"""
        Evaluate the quality of the following answer to a user question.
        
        User Question: {query}
        
        Generated Answer: {answer}
        
        Sources Used: {sources_info}
        
        Please evaluate the answer on the following criteria (score 1-5 for each):
        
        1. Accuracy: How factually correct is the answer?
        2. Completeness: Does the answer fully address the question?
        3. Relevance: How well does the answer relate to the question?
        4. Clarity: Is the answer clear and easy to understand?
        5. Coherence: Is the answer well-structured and logical?
        
        Provide your evaluation as a JSON object with the following structure:
        {{
            "overall_score": <float between 1-5>,
            "rationale": "Brief explanation of the overall assessment",
            "criteria": {{
                "accuracy": <float between 1-5>,
                "completeness": <float between 1-5>,
                "relevance": <float between 1-5>,
                "clarity": <float between 1-5>,
                "coherence": <float between 1-5>
            }},
            "strengths": ["strength1", "strength2", ...],
            "weaknesses": ["weakness1", "weakness2", ...],
            "suggestions": ["suggestion1", "suggestion2", ...]
        }}
        
        Be objective and constructive in your evaluation.
        """
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for evaluation"""
        return """You are an expert evaluator of AI-generated responses. You provide 
        objective, balanced assessments based on accuracy, completeness, relevance, 
        clarity, and coherence. Your evaluations are fair and constructive, helping 
        to improve response quality. Always respond with valid JSON."""
    
    def _calculate_fallback_score(self, state: AgentState) -> float:
        """Calculate fallback score based on available metrics"""
        base_score = 3.0  # Neutral starting point
        
        # Adjust based on confidence score
        confidence_score = state.get("confidence_score", 0.5)
        base_score += (confidence_score - 0.5) * 2  # Scale confidence impact
        
        # Adjust based on sources
        sources = state.get("retrieved_sources", [])
        if sources:
            avg_relevance = sum(s.relevance_score for s in sources) / len(sources)
            base_score += (avg_relevance - 0.7) * 2  # Scale relevance impact
        else:
            base_score -= 1.0  # Penalty for no sources
        
        # Adjust based on answer length (reasonable length is good)
        final_answer = state.get("final_answer", "")
        if final_answer:
            answer_length = len(final_answer)
            if 100 <= answer_length <= 2000:
                base_score += 0.2
            elif answer_length < 50:
                base_score -= 0.5
            elif answer_length > 3000:
                base_score -= 0.3
        
        # Adjust based on errors
        errors = state.get("errors", [])
        if errors:
            base_score -= 0.2 * len(errors)
        
        # Ensure score is within bounds
        return max(1.0, min(5.0, base_score))
    
    def evaluate_standalone(self, query: str, answer: str, sources: list) -> EvaluationResult:
        """Standalone evaluation method for re-evaluation"""
        try:
            evaluation_prompt = self._create_evaluation_prompt(query, answer, sources)
            
            response = self.client.chat.completions.create(
                model=settings.evaluation_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1
            )
            
            evaluation_data = json.loads(response.choices[0].message.content)
            
            return EvaluationResult(
                score=evaluation_data["overall_score"],
                rationale=evaluation_data["rationale"],
                criteria=evaluation_data["criteria"]
            )
            
        except Exception as e:
            logger.error(f"Error in standalone evaluation: {e}")
            return EvaluationResult(
                score=2.5,
                rationale="Standalone evaluation failed",
                criteria={
                    "accuracy": 2.5,
                    "completeness": 2.5,
                    "relevance": 2.5,
                    "clarity": 2.5,
                    "coherence": 2.5
                }
            )