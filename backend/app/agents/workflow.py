import time
import uuid
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from loguru import logger

from app.agents.state import AgentState
from app.agents.query_parser import QueryParserAgent
from app.agents.retriever import RetrieverAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.summarizer import SummarizerAgent
from app.agents.evaluator import EvaluatorAgent


class InsightBotWorkflow:
    def __init__(self):
        self.query_parser = QueryParserAgent()
        self.retriever = RetrieverAgent()
        self.analyzer = AnalyzerAgent()
        self.summarizer = SummarizerAgent()
        self.evaluator = EvaluatorAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_query", self._parse_query_node)
        workflow.add_node("retrieve_sources", self._retrieve_sources_node)
        workflow.add_node("analyze_sources", self._analyze_sources_node)
        workflow.add_node("create_summary", self._create_summary_node)
        workflow.add_node("evaluate_response", self._evaluate_response_node)
        
        # Add edges
        workflow.add_edge("parse_query", "retrieve_sources")
        workflow.add_edge("retrieve_sources", "analyze_sources")
        workflow.add_edge("analyze_sources", "create_summary")
        workflow.add_edge("create_summary", "evaluate_response")
        workflow.add_edge("evaluate_response", END)
        
        # Set entry point
        workflow.set_entry_point("parse_query")
        
        return workflow.compile()
    
    def _parse_query_node(self, state: AgentState) -> AgentState:
        """Parse query node wrapper"""
        start_time = time.time()
        try:
            result = self.query_parser.parse_query(state)
            execution_time = time.time() - start_time
            
            # Update execution time in the last step
            if "agent_steps" in result and result["agent_steps"]:
                result["agent_steps"][-1]["execution_time"] = execution_time
            
            return result
        except Exception as e:
            logger.error(f"Error in parse_query node: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Parse query node error: {str(e)}")
            return state
    
    def _retrieve_sources_node(self, state: AgentState) -> AgentState:
        """Retrieve sources node wrapper"""
        start_time = time.time()
        try:
            result = self.retriever.retrieve_sources(state)
            execution_time = time.time() - start_time
            
            # Update execution time in the last step
            if "agent_steps" in result and result["agent_steps"]:
                result["agent_steps"][-1]["execution_time"] = execution_time
            
            return result
        except Exception as e:
            logger.error(f"Error in retrieve_sources node: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Retrieve sources node error: {str(e)}")
            return state
    
    def _analyze_sources_node(self, state: AgentState) -> AgentState:
        """Analyze sources node wrapper"""
        start_time = time.time()
        try:
            result = self.analyzer.analyze_sources(state)
            execution_time = time.time() - start_time
            
            # Update execution time in the last step
            if "agent_steps" in result and result["agent_steps"]:
                result["agent_steps"][-1]["execution_time"] = execution_time
            
            return result
        except Exception as e:
            logger.error(f"Error in analyze_sources node: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Analyze sources node error: {str(e)}")
            return state
    
    def _create_summary_node(self, state: AgentState) -> AgentState:
        """Create summary node wrapper"""
        start_time = time.time()
        try:
            result = self.summarizer.create_summary(state)
            execution_time = time.time() - start_time
            
            # Update execution time in the last step
            if "agent_steps" in result and result["agent_steps"]:
                result["agent_steps"][-1]["execution_time"] = execution_time
            
            return result
        except Exception as e:
            logger.error(f"Error in create_summary node: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Create summary node error: {str(e)}")
            return state
    
    def _evaluate_response_node(self, state: AgentState) -> AgentState:
        """Evaluate response node wrapper"""
        start_time = time.time()
        try:
            result = self.evaluator.evaluate_response(state)
            execution_time = time.time() - start_time
            
            # Update execution time in the last step
            if "agent_steps" in result and result["agent_steps"]:
                result["agent_steps"][-1]["execution_time"] = execution_time
            
            return result
        except Exception as e:
            logger.error(f"Error in evaluate_response node: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Evaluate response node error: {str(e)}")
            return state
    
    def run(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Run the complete workflow"""
        start_time = time.time()
        
        # Initialize state
        initial_state = AgentState(
            original_query=query,
            session_id=session_id or str(uuid.uuid4()),
            parsed_query={},
            intent="",
            entities=[],
            query_type="general",
            retrieved_sources=[],
            retrieval_successful=False,
            analysis_result="",
            reasoning_steps=[],
            confidence_score=0.0,
            final_answer="",
            key_points=[],
            citations=[],
            evaluation_result=None,
            execution_time=0.0,
            agent_steps=[],
            errors=[]
        )
        
        try:
            # Run the workflow
            result = self.workflow.invoke(initial_state)
            
            # Calculate total execution time
            total_execution_time = time.time() - start_time
            result["execution_time"] = total_execution_time
            
            logger.info(f"Workflow completed in {total_execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error running workflow: {e}")
            
            # Return error state
            error_result = initial_state.copy()
            error_result["final_answer"] = f"I apologize, but I encountered an error processing your query: {str(e)}"
            error_result["execution_time"] = time.time() - start_time
            error_result["errors"] = [f"Workflow error: {str(e)}"]
            
            return error_result
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get workflow status and statistics"""
        return {
            "workflow_initialized": True,
            "agents": {
                "query_parser": "active",
                "retriever": "active", 
                "analyzer": "active",
                "summarizer": "active",
                "evaluator": "active"
            },
            "workflow_steps": [
                "parse_query",
                "retrieve_sources", 
                "analyze_sources",
                "create_summary",
                "evaluate_response"
            ]
        }


# Global workflow instance
workflow = InsightBotWorkflow()