import re
import json
from typing import Dict, Any, List
from openai import OpenAI
from loguru import logger
from app.config import settings
from app.agents.state import AgentState


class QueryParserAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def parse_query(self, state: AgentState) -> AgentState:
        """Parse the user query to extract intent, entities, and query type"""
        try:
            query = state["original_query"]
            
            # Create prompt for query parsing
            prompt = f"""
            Analyze the following user query and extract:
            1. Intent: What is the user trying to accomplish?
            2. Entities: Key terms, company names, metrics, dates, etc.
            3. Query type: financial, technical, business, or general
            4. Specificity: How specific is the query (high, medium, low)
            5. Expected answer type: comparison, explanation, data, analysis, etc.

            Query: "{query}"

            Respond with a JSON object containing:
            {{
                "intent": "brief description of user intent",
                "entities": ["entity1", "entity2", ...],
                "query_type": "financial|technical|business|general",
                "specificity": "high|medium|low",
                "expected_answer_type": "comparison|explanation|data|analysis|summary",
                "key_topics": ["topic1", "topic2", ...],
                "requires_calculations": true|false,
                "requires_comparisons": true|false,
                "time_sensitivity": "current|historical|future|none"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert query analyzer. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Parse the response
            parsed_result = json.loads(response.choices[0].message.content)
            
            # Update state
            state["parsed_query"] = parsed_result
            state["intent"] = parsed_result["intent"]
            state["entities"] = parsed_result["entities"]
            state["query_type"] = parsed_result["query_type"]
            
            # Add parsing step to execution trace
            if "agent_steps" not in state:
                state["agent_steps"] = []
            
            state["agent_steps"].append({
                "agent": "query_parser",
                "action": "parse_query",
                "input": {"query": query},
                "output": parsed_result,
                "status": "success"
            })
            
            logger.info(f"Query parsed successfully: {parsed_result['intent']}")
            return state
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            
            # Fallback parsing
            state["parsed_query"] = {
                "intent": "Answer user question",
                "entities": self._extract_entities_fallback(query),
                "query_type": "general",
                "specificity": "medium",
                "expected_answer_type": "explanation"
            }
            state["intent"] = "Answer user question"
            state["entities"] = self._extract_entities_fallback(query)
            state["query_type"] = "general"
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Query parsing error: {str(e)}")
            
            return state
    
    def _extract_entities_fallback(self, query: str) -> List[str]:
        """Fallback entity extraction using regex"""
        entities = []
        
        # Common financial entities
        financial_patterns = [
            r'\b(TSLA|NVDA|AAPL|GOOGL|MSFT|AMZN|META)\b',  # Stock symbols
            r'\b\d{4}\b',  # Years
            r'\b\$\d+\.?\d*[MBK]?\b',  # Dollar amounts
            r'\b\d+\.?\d*%\b',  # Percentages
        ]
        
        for pattern in financial_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Extract capitalized words (potential company names)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', query)
        entities.extend(capitalized_words[:5])  # Limit to 5
        
        return list(set(entities))  # Remove duplicates