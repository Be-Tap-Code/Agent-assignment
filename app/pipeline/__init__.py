"""
Pipeline module for geotechnical Q&A processing.

This module implements a clean pipeline architecture:
1. Decision: Determine action (retrieve/compute/both)
2. Retriever: Search knowledge base
3. Compute: Perform calculations if needed
4. Synthesis: Generate final answer
"""

# Import modules only when needed to avoid circular imports
# from .decision import DecisionModule
# from .retriever import RetrieverModule
# from .compute import ComputeModule
# from .synthesis import SynthesisModule

__all__ = [
    "DecisionModule",
    "RetrieverModule", 
    "ComputeModule",
    "SynthesisModule"
]
