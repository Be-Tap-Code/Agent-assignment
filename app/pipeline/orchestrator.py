"""
Pipeline orchestrator for coordinating the complete Q&A workflow.
"""

from typing import Dict, Any, Optional
from app.pipeline.decision import DecisionModule
from app.pipeline.retriever import RetrieverModule
from app.pipeline.compute import ComputeModule
from app.pipeline.synthesis import SynthesisModule
from app.core.logging import get_logger

logger = get_logger()


class PipelineOrchestrator:
    """Orchestrates the complete Q&A pipeline workflow."""
    
    def __init__(self):
        self.decision = DecisionModule()
        self.retriever = RetrieverModule()
        self.compute = ComputeModule()
        self.synthesis = SynthesisModule()
        self.logger = logger
    
    async def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process a question through the complete pipeline.
        
        Args:
            question: User's question
            
        Returns:
            Dict with answer and sources
        """
        self.logger.simple("🚀 Starting pipeline processing", question=question[:100])
        
        try:
            # Step 1: Decision analysis
            self.logger.simple("📋 Step 1: Decision Analysis")
            decision_result = await self.decision.analyze_question(question)
            action = decision_result.get("action", "retrieve")
            params = decision_result.get("params", {})
            
            self.logger.simple("✅ Decision completed", 
                              action=action,
                              params=params)
            
            # Step 2: Execute based on action
            retrieval_results = None
            compute_results = None
            
            if action in ["retrieve", "both"]:
                self.logger.simple("📚 Step 2a: Knowledge Retrieval")
                retrieval_results = self.retriever.search_knowledge(question, top_k=3)
                self.logger.simple("✅ Retrieval completed", 
                                  results_count=len(retrieval_results))
            
            if action in ["compute", "both"]:
                self.logger.simple("🧮 Step 2b: Calculation")
                compute_results = self.compute.perform_calculation(action, params)
                self.logger.simple("✅ Calculation completed", 
                                  has_results=bool(compute_results))
            
            # Step 3: Synthesis
            self.logger.simple("📝 Step 3: Answer Synthesis")
            synthesis_result = await self.synthesis.synthesize_answer(
                question, retrieval_results, compute_results, action
            )
            
            # Step 4: Format final response
            final_response = {
                "answer": synthesis_result.get("answer", ""),
                "citations": synthesis_result.get("citations", []),
                "action_taken": action,
                "has_calculation": bool(compute_results),
                "retrieval_count": len(retrieval_results) if retrieval_results else 0
            }
            
            self.logger.simple("🎉 Pipeline processing completed", 
                              answer_length=len(final_response["answer"]),
                              citations_count=len(final_response["citations"]))
            
            return final_response
            
        except Exception as e:
            self.logger.error("❌ Pipeline processing failed", error=str(e))
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "citations": [],
                "action_taken": "error",
                "has_calculation": False,
                "retrieval_count": 0
            }