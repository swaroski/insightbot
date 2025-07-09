from typing import List
from openai import OpenAI
from loguru import logger
from app.config import settings
from app.agents.state import AgentState
from app.models.schemas import Source


class SummarizerAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def create_summary(self, state: AgentState) -> AgentState:
        """Create a final summary with key points and citations"""
        try:
            query = state["original_query"]
            analysis_result = state.get("analysis_result", "")
            sources = state.get("retrieved_sources", [])
            parsed_query = state.get("parsed_query", {})
            
            # Create summary prompt
            summary_prompt = self._create_summary_prompt(query, analysis_result, sources, parsed_query)
            
            # Generate summary
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.1
            )
            
            final_answer = response.choices[0].message.content
            
            # Extract key points
            key_points = self._extract_key_points(final_answer)
            
            # Create citations
            citations = self._create_citations(sources)
            
            # Update state
            state["final_answer"] = final_answer
            state["key_points"] = key_points
            state["citations"] = citations
            
            # Add summary step to execution trace
            if "agent_steps" not in state:
                state["agent_steps"] = []
            
            state["agent_steps"].append({
                "agent": "summarizer",
                "action": "create_summary",
                "input": {
                    "query": query,
                    "analysis_length": len(analysis_result),
                    "sources_count": len(sources)
                },
                "output": {
                    "summary_length": len(final_answer),
                    "key_points_count": len(key_points),
                    "citations_count": len(citations)
                },
                "status": "success"
            })
            
            logger.info(f"Summary created with {len(key_points)} key points and {len(citations)} citations")
            return state
            
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            
            # Fallback summary
            state["final_answer"] = self._create_fallback_summary(state)
            state["key_points"] = self._extract_key_points_fallback(state)
            state["citations"] = self._create_citations(state.get("retrieved_sources", []))
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Summary error: {str(e)}")
            
            return state
    
    def _create_summary_prompt(self, query: str, analysis_result: str, sources: List[Source], parsed_query: dict) -> str:
        """Create the summary prompt"""
        
        expected_answer_type = parsed_query.get("expected_answer_type", "explanation")
        
        prompt = f"""
        Based on the following analysis, create a clear, concise final answer to the user's question.
        
        Original Question: {query}
        Expected Answer Type: {expected_answer_type}
        
        Analysis Result:
        {analysis_result}
        
        Please provide a final answer that:
        1. Directly addresses the user's question
        2. Is well-structured and easy to understand
        3. Includes the most important insights from the analysis
        4. Maintains accuracy while being concise
        5. Acknowledges any limitations or uncertainties
        
        Format your response as a clear, professional answer that would be suitable 
        for a business or technical audience.
        """
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for summarization"""
        return """You are an expert at creating clear, concise summaries that capture 
        the essential information while being easy to understand. Your summaries are 
        well-structured, accurate, and professional."""
    
    def _extract_key_points(self, final_answer: str) -> List[str]:
        """Extract key points from the final answer"""
        key_points = []
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in final_answer.split('\n') if p.strip()]
        
        # Look for bullet points or numbered items
        for paragraph in paragraphs:
            if paragraph.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                # This is already a key point
                key_points.append(paragraph)
            elif len(paragraph) > 20 and len(paragraph) < 200:
                # This could be a key point if it's a reasonable length
                # Check if it contains important keywords
                if any(keyword in paragraph.lower() for keyword in 
                       ['increase', 'decrease', 'growth', 'decline', 'important', 
                        'significant', 'key', 'main', 'primary', 'result', 'conclusion']):
                    key_points.append(paragraph)
        
        # If no key points found, create them from the first few sentences
        if not key_points:
            sentences = final_answer.split('.')
            key_points = [s.strip() + '.' for s in sentences[:3] if len(s.strip()) > 10]
        
        return key_points[:5]  # Limit to 5 key points
    
    def _create_citations(self, sources: List[Source]) -> List[str]:
        """Create citations from sources"""
        citations = []
        
        for i, source in enumerate(sources, 1):
            citation = f"[{i}] {source.filename}"
            if source.page is not None:
                citation += f" (chunk {source.page + 1})"
            citation += f" - Relevance: {source.relevance_score:.2f}"
            citations.append(citation)
        
        return citations
    
    def _create_fallback_summary(self, state: AgentState) -> str:
        """Create fallback summary when main summarization fails"""
        query = state["original_query"]
        analysis_result = state.get("analysis_result", "")
        
        if analysis_result:
            return f"""
            Based on the available information, here's what I found regarding your question: {query}
            
            {analysis_result[:1000]}...
            
            Note: This response was generated using fallback processing due to a system error.
            """
        else:
            return f"""
            I apologize, but I encountered an error while processing your question: {query}
            
            I was unable to generate a complete analysis at this time. 
            Please try rephrasing your question or contact support if the issue persists.
            """
    
    def _extract_key_points_fallback(self, state: AgentState) -> List[str]:
        """Extract key points using fallback method"""
        analysis_result = state.get("analysis_result", "")
        
        if analysis_result:
            # Simple extraction based on sentence length and position
            sentences = analysis_result.split('.')
            key_points = []
            
            for sentence in sentences[:5]:
                sentence = sentence.strip()
                if 20 <= len(sentence) <= 150:
                    key_points.append(sentence + '.')
            
            return key_points
        else:
            return ["Unable to extract key points due to processing error"]