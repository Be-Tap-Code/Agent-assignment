"""

Synthesis module for generating final answers using LLM.
"""

from typing import List, Dict, Any, Optional
from app.core.llm import get_gemini_client
from app.core.logging import get_logger

logger = get_logger()


class SynthesisModule:
    """Generates final answers by synthesizing retrieval and computation results."""
    
    def __init__(self):
        self.llm = get_gemini_client()
        self.logger = logger
    
    async def synthesize_answer(
        self, 
        question: str, 
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        compute_results: Optional[Dict[str, Any]] = None,
        task: str = "retrieve"
    ) -> Dict[str, Any]:
        """
        Synthesize final answer from question, retrieval, and computation results.
        
        Args:
            question: Original user question
            retrieval_results: Knowledge base search results
            compute_results: Calculation results
            task: Task type ("retrieve", "compute", "both")
            
        Returns:
            Dict with answer and citations
        """
        self.logger.simple("📝 Synthesizing final answer", 
                          question=question[:100],
                          task=task,
                          has_retrieval=bool(retrieval_results),
                          has_compute=bool(compute_results))
        
        # Build context for LLM
        context = self._build_context(question, retrieval_results, compute_results, task)
        
        # Generate answer using LLM
        answer = await self._generate_answer(context, task)
        
        # Extract citations
        citations = self._extract_citations(retrieval_results)
        
        self.logger.simple("✅ Answer synthesis completed", 
                          answer_length=len(answer),
                          citations_count=len(citations))
        
        return {
            "answer": answer,
            "citations": citations
        }
    
    def _build_context(
        self, 
        question: str, 
        retrieval_results: Optional[List[Dict[str, Any]]],
        compute_results: Optional[Dict[str, Any]],
        task: str = "retrieve"
    ) -> str:
        """Build context string for LLM based on task type."""
        context_parts = [f"Question: {question}\n"]
        
        # Add task-specific context based on task type
        if task == "compute":
            context_parts.append("TASK: Focus on calculation results.")
            context_parts.append("")
        elif task == "both":
            context_parts.append("TASK: Use both knowledge base and calculation results.")
            context_parts.append("")
        
        # Add retrieval context (for retrieve and both tasks)
        if retrieval_results and task in ["retrieve", "both"]:
            context_parts.append("Relevant Knowledge Base Information:")
            
            # Prioritize chunks containing formulas for compute-related questions
            if task in ["compute", "both"]:
                prioritized_results = self._prioritize_chunks_with_formula(retrieval_results)
            else:
                prioritized_results = retrieval_results
            
            for i, result in enumerate(prioritized_results[:2], 1):  # Top 2 results
                content = result.get("content", "")
                # Don't truncate if it contains formulas
                if "q_ult" in content or "=" in content or "formula" in content.lower():
                    # Keep full content for formula chunks
                    pass
                else:
                    content = content[:500]  # Limit content length for non-formula chunks
                
                source = result.get("source", "unknown")
                chunk_id = result.get("chunk_id", "")
                context_parts.append(f"{i}. From {source} (chunk_id: {chunk_id}): {content}")
            context_parts.append("")
        
        # Add computation context (for compute and both tasks)
        if compute_results and task in ["compute", "both"]:
            context_parts.append("Calculation Results:")
            calc_type = compute_results.get("type", "unknown")
            result_data = compute_results.get("result", {})
            
            if calc_type == "terzaghi":
                context_parts.append(f"Terzaghi Bearing Capacity: {result_data.get('result', 0):.2f} kPa")
                context_parts.append(f"Formula: {result_data.get('formula', 'q_ult = γ*Df*Nq + 0.5*γ*B*Nr')}")
                context_parts.append(f"Factors: Nq={result_data.get('factors', {}).get('Nq', 0):.2f}, Nr={result_data.get('factors', {}).get('Nr', 0):.2f}")
            elif calc_type == "settlement":
                context_parts.append(f"Settlement: {result_data.get('settlement', 0):.3f} mm")
                context_parts.append(f"Formula: {result_data.get('formula', 'settlement = (load * width) / (E * width) * 1000')}")
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _prioritize_chunks_with_formula(self, retrieval_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize chunks containing formulas (q_ult, equations)."""
        formula_chunks = []
        other_chunks = []
        
        for result in retrieval_results:
            content = result.get("content", "").lower()
            if "q_ult" in content or "=" in content or "equation" in content:
                formula_chunks.append(result)
            else:
                other_chunks.append(result)
        
        # Return formula chunks first, then others
        return formula_chunks + other_chunks
    
    async def _generate_answer(self, context: str, task: str = "retrieve") -> str:
        """Generate answer using LLM."""
        
        # Check if API key is available
        if not self.llm.api_key:
            self.logger.warning("⚠️ Google API key not configured, using fallback answer")
            return self._fallback_answer(context, task)
        
        # Build task-specific prompt
        if task == "retrieve":
            task_instructions = """
Instructions:
- Answer based on knowledge base information only
- Keep response concise (under 150 words)
- Use simple, clear language
- No prefixes like "Answer:" or "Based on"
"""
        elif task == "compute":
            task_instructions = """
Instructions:
- Focus on the calculation result and key formula
- Keep response concise (under 150 words)
- Show the main result and what it means
- No prefixes like "Answer:" or "Based on"
"""
        elif task == "both":
            task_instructions = """
Instructions:
- Combine knowledge base info with calculation results
- Keep response concise (under 150 words)
- Focus on practical application
- No prefixes like "Answer:" or "Based on"
"""
        else:
            task_instructions = """
Instructions:
- Answer directly and clearly
- Keep response concise (under 150 words)
- Use simple language
- No prefixes like "Answer:" or "Based on"
"""

        prompt = f"""
You are a geotechnical engineering expert. Answer the question concisely.

{context}

{task_instructions}

Answer:
"""

        try:
            # Use async method properly
            answer = await self.llm.agenerate(prompt)
            
            # Clean up the answer
            answer = answer.strip()
            if answer.startswith("Answer:"):
                answer = answer[7:].strip()
            
            self.logger.simple("✅ LLM answer generation successful", answer_length=len(answer))
            return answer
            
        except Exception as e:
            self.logger.error("❌ Answer generation failed", error=str(e))
            return self._fallback_answer(context, task)
    
    def _fallback_answer(self, context: str, task: str = "retrieve") -> str:
        """Generate fallback answer when LLM is not available."""
        # Extract question from context
        lines = context.split('\n')
        question = ""
        for line in lines:
            if line.startswith("Question:"):
                question = line.replace("Question:", "").strip()
                break
        
        # Task-specific fallback answers
        if task == "compute":
            # For compute tasks, try to extract calculation info from context
            if "Settlement:" in context:
                return "The settlement has been calculated using the elastic settlement formula. The result shows the expected vertical deformation under the applied load."
            elif "Terzaghi Bearing Capacity:" in context:
                return "The ultimate bearing capacity has been calculated using Terzaghi's equation. This represents the maximum load the foundation can support."
            else:
                return "A calculation has been performed based on the provided parameters. The results show the calculated values for your specific case."
        elif task == "retrieve":
            # For retrieve tasks, provide general information
            if "CPT" in question.upper():
                return "CPT (Cone Penetration Test) is a geotechnical investigation method that determines soil properties by pushing a cone-shaped probe into the ground and measuring resistance."
            elif "bearing capacity" in question.lower():
                return "Bearing capacity is the maximum load a foundation can support without failure. It depends on soil properties, foundation geometry, and loading conditions."
            elif "settlement" in question.lower():
                return "Settlement is the vertical deformation of soil under applied loads. It can be immediate (elastic) or long-term (consolidation)."
            else:
                return "This is a geotechnical engineering question. Please provide more specific details about your inquiry."
        else:  # both or other tasks
            return "This question involves both theoretical knowledge and practical calculations in geotechnical engineering."
    
    def _extract_citations(self, retrieval_results: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract chunk-level citations from retrieval results."""
        if not retrieval_results:
            return []
        
        citations = []
        for result in retrieval_results:
            source = result.get("source", "")
            chunk_id = result.get("chunk_id", "")
            confidence = result.get("confidence", 0.0)
            
            if source and source != "unknown" and chunk_id:
                citations.append({
                    "source": f"{source}.md",
                    "confidence": confidence,
                    "chunk_id": chunk_id
                })
        
        return citations
