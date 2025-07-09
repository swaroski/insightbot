from typing import List
from loguru import logger
from app.agents.state import AgentState
from app.services.vector_store import vector_store
from app.models.schemas import Source


class RetrieverAgent:
    def __init__(self):
        self.max_sources = 10
        self.min_relevance_score = 0.7
    
    def retrieve_sources(self, state: AgentState) -> AgentState:
        """Retrieve relevant sources from the vector store"""
        try:
            query = state["original_query"]
            parsed_query = state.get("parsed_query", {})
            
            # Determine number of sources to retrieve based on query complexity
            k = self._determine_retrieval_count(parsed_query)
            
            # Perform vector search
            sources = vector_store.search(
                query=query,
                k=k,
                score_threshold=self.min_relevance_score
            )
            
            # Filter and rank sources
            filtered_sources = self._filter_and_rank_sources(sources, parsed_query)
            
            # Update state
            state["retrieved_sources"] = filtered_sources
            state["retrieval_successful"] = len(filtered_sources) > 0
            
            # Add retrieval step to execution trace
            if "agent_steps" not in state:
                state["agent_steps"] = []
            
            state["agent_steps"].append({
                "agent": "retriever",
                "action": "retrieve_sources",
                "input": {
                    "query": query,
                    "k": k,
                    "score_threshold": self.min_relevance_score
                },
                "output": {
                    "sources_found": len(filtered_sources),
                    "avg_relevance_score": sum(s.relevance_score for s in filtered_sources) / len(filtered_sources) if filtered_sources else 0
                },
                "status": "success"
            })
            
            logger.info(f"Retrieved {len(filtered_sources)} relevant sources")
            return state
            
        except Exception as e:
            logger.error(f"Error retrieving sources: {e}")
            
            # Set empty sources on error
            state["retrieved_sources"] = []
            state["retrieval_successful"] = False
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Retrieval error: {str(e)}")
            
            return state
    
    def _determine_retrieval_count(self, parsed_query: dict) -> int:
        """Determine how many sources to retrieve based on query complexity"""
        base_count = 5
        
        # Adjust based on query specificity
        specificity = parsed_query.get("specificity", "medium")
        if specificity == "high":
            base_count = 3
        elif specificity == "low":
            base_count = 8
        
        # Adjust based on expected answer type
        answer_type = parsed_query.get("expected_answer_type", "explanation")
        if answer_type == "comparison":
            base_count += 3
        elif answer_type == "analysis":
            base_count += 2
        
        return min(base_count, self.max_sources)
    
    def _filter_and_rank_sources(self, sources: List[Source], parsed_query: dict) -> List[Source]:
        """Filter and rank sources based on query requirements"""
        if not sources:
            return []
        
        # Filter out sources below minimum relevance
        filtered_sources = [s for s in sources if s.relevance_score >= self.min_relevance_score]
        
        # Boost relevance for sources containing key entities
        entities = parsed_query.get("entities", [])
        if entities:
            for source in filtered_sources:
                entity_count = sum(1 for entity in entities if entity.lower() in source.content.lower())
                if entity_count > 0:
                    source.relevance_score += 0.1 * entity_count
        
        # Sort by relevance score
        filtered_sources.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Remove duplicates based on content similarity
        unique_sources = self._remove_duplicate_sources(filtered_sources)
        
        return unique_sources[:self.max_sources]
    
    def _remove_duplicate_sources(self, sources: List[Source]) -> List[Source]:
        """Remove sources with very similar content"""
        unique_sources = []
        
        for source in sources:
            is_duplicate = False
            for existing in unique_sources:
                # Simple similarity check - could be improved with more sophisticated methods
                if self._content_similarity(source.content, existing.content) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sources.append(source)
        
        return unique_sources
    
    def _content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple content similarity"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)