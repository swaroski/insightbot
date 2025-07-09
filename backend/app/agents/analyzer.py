from typing import List, Dict, Any
from openai import OpenAI
from loguru import logger
from app.config import settings
from app.agents.state import AgentState
from app.models.schemas import Source


class AnalyzerAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def analyze_sources(self, state: AgentState) -> AgentState:
        """Analyze retrieved sources and generate insights"""
        try:
            query = state["original_query"]
            sources = state.get("retrieved_sources", [])
            parsed_query = state.get("parsed_query", {})
            
            if not sources:
                return self._handle_no_sources(state)
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(query, sources, parsed_query)
            
            # Perform analysis
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self._get_system_prompt(parsed_query)},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2
            )
            
            analysis_result = response.choices[0].message.content
            
            # Extract reasoning steps
            reasoning_steps = self._extract_reasoning_steps(analysis_result)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(sources, parsed_query)
            
            # Update state
            state["analysis_result"] = analysis_result
            state["reasoning_steps"] = reasoning_steps
            state["confidence_score"] = confidence_score
            
            # Add analysis step to execution trace
            if "agent_steps" not in state:
                state["agent_steps"] = []
            
            state["agent_steps"].append({
                "agent": "analyzer",
                "action": "analyze_sources",
                "input": {
                    "query": query,
                    "sources_count": len(sources),
                    "query_type": parsed_query.get("query_type", "general")
                },
                "output": {
                    "analysis_length": len(analysis_result),
                    "reasoning_steps": len(reasoning_steps),
                    "confidence_score": confidence_score
                },
                "status": "success"
            })
            
            logger.info(f"Analysis completed with confidence score: {confidence_score}")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing sources: {e}")
            
            # Fallback analysis
            state["analysis_result"] = self._generate_fallback_analysis(state)
            state["reasoning_steps"] = ["Analysis failed, providing basic response"]
            state["confidence_score"] = 0.3
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Analysis error: {str(e)}")
            
            return state
    
    def _create_analysis_prompt(self, query: str, sources: List[Source], parsed_query: dict) -> str:
        """Create the analysis prompt based on query and sources"""
        
        # Prepare sources context
        sources_context = "\n\n".join([
            f"Source {i+1} ({source.filename}):\n{source.content}"
            for i, source in enumerate(sources)
        ])
        
        query_type = parsed_query.get("query_type", "general")
        expected_answer_type = parsed_query.get("expected_answer_type", "explanation")
        
        prompt = f"""
        Based on the following sources, analyze and answer the user's question.
        
        User Question: {query}
        
        Query Type: {query_type}
        Expected Answer Type: {expected_answer_type}
        
        Available Sources:
        {sources_context}
        
        Please provide a comprehensive analysis that:
        1. Directly answers the user's question
        2. Uses information from the provided sources
        3. Shows clear reasoning steps
        4. Identifies any limitations or uncertainties
        5. Provides specific examples or data points when available
        
        If the sources don't contain sufficient information to fully answer the question, 
        clearly state what information is missing and what can be concluded from available data.
        """
        
        return prompt
    
    def _get_system_prompt(self, parsed_query: dict) -> str:
        """Get system prompt based on query type"""
        query_type = parsed_query.get("query_type", "general")
        
        base_prompt = """You are an expert analyst with deep knowledge across multiple domains. 
        You provide accurate, well-reasoned responses based on available information."""
        
        if query_type == "financial":
            return base_prompt + """ You specialize in financial analysis, including 
            company valuations, market trends, financial metrics, and investment insights."""
        elif query_type == "technical":
            return base_prompt + """ You specialize in technical analysis, including 
            technology trends, product specifications, implementation details, and technical comparisons."""
        elif query_type == "business":
            return base_prompt + """ You specialize in business analysis, including 
            strategy, operations, market analysis, and business model evaluation."""
        else:
            return base_prompt + """ You provide balanced, well-researched responses 
            across various domains with clear reasoning and evidence."""
    
    def _extract_reasoning_steps(self, analysis_result: str) -> List[str]:
        """Extract reasoning steps from analysis result"""
        steps = []
        
        # Look for numbered points or clear logical progression
        lines = analysis_result.split('\n')
        current_step = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new step (numbered, bulleted, or clear transition)
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('•', '-', '*')) or
                line.startswith(('First', 'Second', 'Next', 'Finally', 'Additionally'))):
                
                if current_step:
                    steps.append(current_step.strip())
                current_step = line
            else:
                current_step += " " + line
        
        if current_step:
            steps.append(current_step.strip())
        
        return steps[:10]  # Limit to 10 steps
    
    def _calculate_confidence_score(self, sources: List[Source], parsed_query: dict) -> float:
        """Calculate confidence score based on sources and query match"""
        if not sources:
            return 0.1
        
        # Base confidence from source relevance
        avg_relevance = sum(s.relevance_score for s in sources) / len(sources)
        confidence = min(avg_relevance, 1.0)
        
        # Adjust based on number of sources
        source_count_factor = min(len(sources) / 5, 1.0)
        confidence *= (0.7 + 0.3 * source_count_factor)
        
        # Adjust based on query specificity
        specificity = parsed_query.get("specificity", "medium")
        if specificity == "high":
            confidence *= 1.1
        elif specificity == "low":
            confidence *= 0.9
        
        return min(confidence, 1.0)
    
    def _handle_no_sources(self, state: AgentState) -> AgentState:
        """Handle case when no sources are available"""
        state["analysis_result"] = """
        I apologize, but I couldn't find any relevant sources in the knowledge base 
        to answer your question. This could be because:
        
        1. The information you're looking for hasn't been uploaded to the system yet
        2. The query might be too specific or use different terminology
        3. The relevant documents might not contain the specific information requested
        
        Please try rephrasing your question or consider uploading additional relevant documents.
        """
        state["reasoning_steps"] = ["No relevant sources found in knowledge base"]
        state["confidence_score"] = 0.1
        
        return state
    
    def _generate_fallback_analysis(self, state: AgentState) -> str:
        """Generate fallback analysis when main analysis fails"""
        query = state["original_query"]
        sources = state.get("retrieved_sources", [])
        
        if sources:
            return f"""
            I found {len(sources)} relevant sources for your question about: {query}
            
            However, I encountered an error during the detailed analysis. 
            The sources contain information that may be relevant to your query, 
            but I cannot provide a comprehensive analysis at this time.
            
            Please try rephrasing your question or contact support if the issue persists.
            """
        else:
            return """
            I apologize, but I couldn't find relevant sources to answer your question 
            and also encountered an error during processing. Please try rephrasing 
            your question or ensure that relevant documents have been uploaded to the system.
            """