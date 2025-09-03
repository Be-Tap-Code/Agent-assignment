#!/usr/bin/env python3
"""Evaluation script for Geotech Q&A Service."""

import json
import os
import sys
import asyncio
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.pipeline.orchestrator import PipelineOrchestrator
from app.api.models import AskRequest
import re


class EvaluationMetrics:
    """Evaluation metrics for Q&A system."""
    
    def __init__(self):
        self.total_questions = 0
        self.hit_at_1 = 0
        self.hit_at_3 = 0
        self.total_keyword_overlap = 0.0
        self.citation_matches = 0
        self.total_confidence_score = 0.0
        self.results = []
    
    def add_result(self, question: str, expected_answer: str, expected_citations: List[Dict], 
                   actual_answer: str, actual_citations: List[Dict], confidence_scores: List[float]):
        """Add evaluation result for a question."""
        self.total_questions += 1
        
        # Calculate hit@k for citations
        hit_at_1, hit_at_3 = self._calculate_hit_at_k(expected_citations, actual_citations)
        self.hit_at_1 += hit_at_1
        self.hit_at_3 += hit_at_3
        
        # Calculate keyword overlap ratio
        keyword_overlap_ratio = self._calculate_keyword_overlap(expected_answer, actual_answer)
        self.total_keyword_overlap += keyword_overlap_ratio
        
        # Calculate citation match
        citation_match = self._calculate_citation_match(expected_citations, actual_citations)
        self.citation_matches += citation_match
        
        # Add confidence scores
        if confidence_scores and len(confidence_scores) > 0:
            self.total_confidence_score += sum(confidence_scores) / len(confidence_scores)
        
        # Store detailed result
        result = {
            "question": question,
            "expected_answer": expected_answer,
            "actual_answer": actual_answer,
            "expected_citations": expected_citations,
            "actual_citations": actual_citations,
            "hit_at_1": hit_at_1,
            "hit_at_3": hit_at_3,
            "keyword_overlap_ratio": keyword_overlap_ratio,
            "citation_match": citation_match,
            "confidence_scores": confidence_scores,
            "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores and len(confidence_scores) > 0 else 0.0
        }
        self.results.append(result)
    
    def _calculate_hit_at_k(self, expected_citations: List[Dict], actual_citations: List[Dict]) -> Tuple[int, int]:
        """Calculate hit@k for citations (top-1 and top-3 only)."""
        # Special case: if expected citations is empty or all sources are empty, always return 1 (perfect match)
        if not expected_citations or len(expected_citations) == 0:
            return 1, 1
        
        # Check if all expected sources are empty strings
        expected_sources = {citation["source"] for citation in expected_citations}
        if all(source == "" for source in expected_sources):
            return 1, 1
        
        actual_sources = [citation.get("source", "") for citation in actual_citations]
        
        hit_at_1 = 1 if any(source in expected_sources for source in actual_sources[:1]) else 0
        hit_at_3 = 1 if any(source in expected_sources for source in actual_sources[:3]) else 0
        
        return hit_at_1, hit_at_3
    
    def _calculate_keyword_overlap(self, expected_answer: str, actual_answer: str) -> float:
        """Calculate keyword overlap ratio."""
        # Normalize text
        expected_words = set(re.findall(r'\b\w+\b', expected_answer.lower()))
        actual_words = set(re.findall(r'\b\w+\b', actual_answer.lower()))
        
        if len(expected_words) == 0:
            return 0.0
        
        # Calculate keyword overlap ratio: how many expected keywords appear in actual answer
        intersection = expected_words.intersection(actual_words)
        keyword_overlap_ratio = len(intersection) / len(expected_words)
        
        return keyword_overlap_ratio
    
    def _calculate_citation_match(self, expected_citations: List[Dict], actual_citations: List[Dict]) -> int:
        """Calculate citation match based on source overlap."""
        # Special case: if expected citations is empty, always return 1 (perfect match)
        if not expected_citations or len(expected_citations) == 0:
            return 1
        
        # Check if all expected sources are empty strings
        expected_sources = {citation["source"] for citation in expected_citations}
        if all(source == "" for source in expected_sources):
            return 1
            
        actual_sources = {citation.get("source", "") for citation in actual_citations}
        
        # Check if any expected source appears in actual citations
        return 1 if expected_sources.intersection(actual_sources) else 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get evaluation summary."""
        if self.total_questions == 0:
            return {"error": "No questions evaluated"}
        
        # Calculate average confidence only for questions with confidence scores
        questions_with_confidence = sum(1 for result in self.results if result.get('confidence_scores') and len(result.get('confidence_scores', [])) > 0)
        avg_confidence = self.total_confidence_score / questions_with_confidence if questions_with_confidence > 0 else 0.0
        
        return {
            "total_questions": self.total_questions,
            "hit_at_1": self.hit_at_1 / self.total_questions,
            "hit_at_3": self.hit_at_3 / self.total_questions,
            "average_keyword_overlap": self.total_keyword_overlap / self.total_questions,
            "citation_match_rate": self.citation_matches / self.total_questions,
            "average_confidence": avg_confidence,
            "questions_with_confidence": questions_with_confidence,
            "detailed_results": self.results
        }


class SystemEvaluator:
    """System evaluator for Q&A service."""
    
    def __init__(self, test_dataset_path: str = None):
        """Initialize evaluator with test dataset."""
        if test_dataset_path is None:
            test_dataset_path = os.path.join(os.path.dirname(__file__), "test_qa.json")
        
        self.test_dataset_path = test_dataset_path
        self.test_dataset = self._load_test_dataset()
        self.metrics = EvaluationMetrics()
    
    def _load_test_dataset(self) -> List[Dict[str, Any]]:
        """Load test dataset from JSON file."""
        try:
            with open(self.test_dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            print(f"✅ Loaded {len(dataset)} test questions from {self.test_dataset_path}")
            return dataset
        except FileNotFoundError:
            print(f"❌ Test dataset not found: {self.test_dataset_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in test dataset: {e}")
            return []
    
    async def evaluate_system(self, orchestrator: PipelineOrchestrator = None) -> Dict[str, Any]:
        """Evaluate the system using test dataset."""
        if not self.test_dataset:
            return {"error": "No test dataset available"}
        
        if orchestrator is None:
            orchestrator = PipelineOrchestrator()
        
        print(f"🚀 Starting evaluation with {len(self.test_dataset)} questions...")
        print("=" * 80)
        
        for i, test_item in enumerate(self.test_dataset, 1):
            print(f"\n📋 Question {i}/{len(self.test_dataset)}")
            print(f"Q: {test_item['question']}")
            
            try:
                # Process question through system
                result = await orchestrator.process_question(test_item['question'])
                
                # Extract results
                actual_answer = result.get('answer', '')
                actual_citations = result.get('citations', [])
                
                # Extract confidence scores from actual citations
                confidence_scores = [citation.get('confidence', 0.0) for citation in actual_citations]
                
                # Add to metrics
                self.metrics.add_result(
                    question=test_item['question'],
                    expected_answer=test_item['expected_answer'],
                    expected_citations=test_item['expected_citations'],
                    actual_answer=actual_answer,
                    actual_citations=actual_citations,
                    confidence_scores=confidence_scores
                )
                
                # Print results
                print(f"A: {actual_answer[:100]}{'...' if len(actual_answer) > 100 else ''}")
                print(f"Citations: {[c.get('source', 'unknown') for c in actual_citations]}")
                print(f"Confidence: {confidence_scores}")
                
                # Calculate and print metrics for this question
                hit_at_1 = self.metrics.results[-1]['hit_at_1']
                hit_at_3 = self.metrics.results[-1]['hit_at_3']
                keyword_overlap = self.metrics.results[-1]['keyword_overlap_ratio']
                citation_match = self.metrics.results[-1]['citation_match']
                
                print(f"Hit@1: {hit_at_1}, Hit@3: {hit_at_3}, Keyword Overlap: {keyword_overlap:.3f}, Citation Match: {citation_match}")
                
            except Exception as e:
                print(f"❌ Error processing question: {e}")
                # Add failed result with empty confidence scores
                self.metrics.add_result(
                    question=test_item['question'],
                    expected_answer=test_item['expected_answer'],
                    expected_citations=test_item['expected_citations'],
                    actual_answer="",
                    actual_citations=[],
                    confidence_scores=[0.0]  # Use 0.0 for failed cases
                )
        
        return self.metrics.get_summary()
    
    def print_evaluation_report(self, summary: Dict[str, Any]):
        """Print detailed evaluation report."""
        print("\n" + "=" * 80)
        print("📊 EVALUATION REPORT")
        print("=" * 80)
        
        if "error" in summary:
            print(f"❌ {summary['error']}")
            return
        
        print(f"📈 Total Questions: {summary['total_questions']}")
        print(f"🎯 Hit@1: {summary['hit_at_1']:.3f} ({summary['hit_at_1']*100:.1f}%)")
        print(f"🎯 Hit@3: {summary['hit_at_3']:.3f} ({summary['hit_at_3']*100:.1f}%)")
        print(f"🔤 Average Keyword Overlap: {summary['average_keyword_overlap']:.3f} ({summary['average_keyword_overlap']*100:.1f}%)")
        print(f"📚 Citation Match Rate: {summary['citation_match_rate']:.3f} ({summary['citation_match_rate']*100:.1f}%)")
        print(f"🎲 Average Confidence: {summary['average_confidence']:.3f}")
        print(f"📊 Questions with Confidence: {summary.get('questions_with_confidence', 0)}/{summary['total_questions']}")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 80)
        
        for i, result in enumerate(summary['detailed_results'], 1):
            print(f"\n{i}. {result['question']}")
            print(f"   Hit@1: {result['hit_at_1']}, Hit@3: {result['hit_at_3']}, Citation: {result['citation_match']}")
            print(f"   Keyword Overlap: {result['keyword_overlap_ratio']:.3f}, Confidence: {result['avg_confidence']:.3f}")
            
            if result['actual_citations']:
                print(f"   Retrieved: {[c.get('source', 'unknown') for c in result['actual_citations']]}")
            if result['expected_citations']:
                print(f"   Expected: {[c['source'] for c in result['expected_citations']]}")
    
    def save_evaluation_report(self, summary: Dict[str, Any], output_path: str = None):
        """Save evaluation report to JSON file."""
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), "evaluation_report.json")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"💾 Evaluation report saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")


async def main():
    """Main evaluation function."""
    print("🔬 Geotech Q&A Service Evaluation")
    print("=" * 80)
    
    # Initialize evaluator
    evaluator = SystemEvaluator()
    
    if not evaluator.test_dataset:
        print("❌ No test dataset available. Exiting.")
        return 1
    
    # Run evaluation
    summary = await evaluator.evaluate_system()
    
    # Print report
    evaluator.print_evaluation_report(summary)
    
    # Save report
    evaluator.save_evaluation_report(summary)
    
    # Return success/failure based on metrics
    if summary.get('hit_at_1', 0) > 0.5 and summary.get('average_keyword_overlap', 0) > 0.4:
        print("\n🎉 Evaluation completed successfully!")
        return 0
    else:
        print("\n⚠️ Evaluation completed with low scores. Consider improving the system.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
