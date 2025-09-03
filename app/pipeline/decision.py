"""
Decision module for determining action type based on question analysis.
"""

import json
import re
from typing import Dict, Any, Optional
from app.core.llm import get_gemini_client
from app.core.logging import get_logger

logger = get_logger()


class DecisionModule:
    """Determines whether to retrieve, compute, or both based on question analysis."""
    
    def __init__(self):
        self.llm = get_gemini_client()
        self.logger = logger
    
    async def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze question and determine action type.
        
        Args:
            question: User's question
            
        Returns:
            Dict with action and params
        """
        self.logger.simple("🔍 Analyzing question", question=question[:100])
        
        # Check for numerical data in question
        has_numerical_data = self._has_numerical_data(question)
        
        # Use LLM to analyze question type
        analysis = await self._llm_analyze_question(question, has_numerical_data)
        
        self.logger.simple("✅ Decision analysis completed", 
                          action=analysis.get("action"),
                          has_numerical=has_numerical_data)
        
        return analysis
    
    def _has_numerical_data(self, question: str) -> bool:
        """Check if question contains numerical data."""
        # Look for common geotechnical parameters
        numerical_patterns = [
            r'\b\d+\.?\d*\s*(kPa|kN/m²|kN/m2|m|mm|cm|degrees?|°)\b',  # Units
            r'\b\d+\.?\d*\s*(B|Df|gamma|γ|phi|φ|load|E|E_s)\b',      # Parameters
            r'\b\d+\.?\d*\s*(width|depth|thickness|diameter)\b',      # Dimensions
            r'\b\d+\.?\d*\s*(foundation|footing|pile|wall)\b',        # Structures
        ]
        
        for pattern in numerical_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return True
        
        return False
    
    async def _llm_analyze_question(self, question: str, has_numerical: bool) -> Dict[str, Any]:
        """Use LLM to analyze question and determine action."""
        
        # Check if API key is available
        if not self.llm.api_key:
            self.logger.warning("⚠️ Google API key not configured, using fallback analysis")
            return self._fallback_analysis(question, has_numerical)
        
        prompt = f"""
You are a geotechnical engineering expert. Analyze the question below and output only valid JSON.

Follow these rules:
- action: "retrieve", "compute", or "both"
- params: include any identified numerical parameters (B, Df, gamma, phi, load, E). Use null if not present.
- reasoning: brief explanation
- No extra text, no markdown, only JSON

Examples:

Question: "What is Terzaghi's bearing capacity equation?"
Contains numerical data: False
Expected JSON:
{{
  "action": "retrieve",
  "params": {{"B": null,"Df": null,"gamma": null,"phi": null,"load": null,"E": null}},
  "reasoning": "Theoretical question"
}}

Question: "Calculate settlement for load=100 kN and E=20000 kPa"
Contains numerical data: True
Expected JSON:
{{
  "action": "compute",
  "params": {{"B": null,"Df": null,"gamma": null,"phi": null,"load": 100,"E": 20000}},
  "reasoning": "Contains numerical data, calculation requested"
}}

Question: "{question}"
Contains numerical data: {has_numerical}
Expected JSON:
"""

        try:
            # Use async method properly
            response = await self.llm.agenerate(prompt)
            
            # Clean and extract JSON from response
            cleaned_response = self._extract_json_from_response(response)
            
            # Try to parse JSON response
            try:
                result = json.loads(cleaned_response)
                self.logger.simple("✅ LLM analysis successful", action=result.get("action"))
                return result
            except json.JSONDecodeError:
                # Try to extract action from text response
                extracted_action = self._extract_action_from_text(response)
                if extracted_action:
                    self.logger.simple("✅ Extracted action from text", action=extracted_action)
                    return self._create_result_from_action(extracted_action, question, has_numerical)
                
                # Fallback if LLM doesn't return valid JSON
                self.logger.warning("⚠️ LLM returned invalid JSON, using fallback")
                return self._fallback_analysis(question, has_numerical)
                
        except Exception as e:
            self.logger.error("❌ LLM analysis failed", error=str(e))
            return self._fallback_analysis(question, has_numerical)
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from LLM response."""
        # Remove markdown code blocks
        response = response.replace("```json", "").replace("```", "")
        
        # Find JSON object
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start != -1 and end > start:
            return response[start:end]
        
        return response.strip()
    
    def _extract_action_from_text(self, response: str) -> Optional[str]:
        """Extract action from text response."""
        response_lower = response.lower()
        
        if "retrieve" in response_lower and "compute" in response_lower:
            return "both"
        elif "retrieve" in response_lower:
            return "retrieve"
        elif "compute" in response_lower:
            return "compute"
        
        return None
    
    def _create_result_from_action(self, action: str, question: str, has_numerical: bool) -> Dict[str, Any]:
        """Create result from extracted action."""
        return {
            "action": action,
            "params": {
                "B": None,
                "Df": None,
                "gamma": None,
                "phi": None,
                "load": None,
                "E": None
            },
            "reasoning": f"Extracted from text: {action}"
        }
    
    def _fallback_analysis(self, question: str, has_numerical: bool) -> Dict[str, Any]:
        """Fallback analysis when LLM fails."""
        if has_numerical:
            action = "both"  # If has numbers, likely needs both theory and calculation
        else:
            action = "retrieve"  # Pure theoretical question
        
        return {
            "action": action,
            "params": {
                "B": None,
                "Df": None,
                "gamma": None,
                "phi": None,
                "load": None,
                "E": None
            },
            "reasoning": f"Fallback analysis: has_numerical={has_numerical}"
        }