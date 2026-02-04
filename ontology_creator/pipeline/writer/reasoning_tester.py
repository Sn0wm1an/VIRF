#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reasoning Tester - responsible for ontological consistency inference validation
"""

from typing import Dict, Any
from owlready2 import sync_reasoner_pellet


class ReasoningTester:
    """Reasoning Tester - responsible for ontological consistency inference validation"""
    
    def __init__(self, world, ontologies: Dict[str, Any]):
        """
        Initialize reasoning tester
        
        Args:
            world: owlready2 World instance
            ontologies: ontological objects dictionary
        """
        self.world = world
        self.ontologies = ontologies
    
    def run_reasoning_test(self, debug: bool = False) -> Dict[str, Any]:
        """Run owlready2 inference consistency test"""
        result = {
            "operation": "owlready2_reasoning_test",
            "status": "completed",
            "consistency": False
        }
        
        try:
            if debug:
                print(f"\n🤖 [DEBUG] Run Pellet inference test")
            
            # Use sync_reasoner to run inference
            with self.world:
                sync_reasoner_pellet(
                    self.world, 
                    infer_property_values=True, 
                    infer_data_property_values=True
                )
            
            result["consistency"] = True
            result["message"] = "Inference test passed, ontological consistency validation successful"
            result["ontologies_tested"] = len(self.ontologies)
            
            if debug:
                print(f"✅ [DEBUG] Inference test passed, ontological consistency validation successful")
                
        except Exception as e:
            result["status"] = "failed"
            result["consistency"] = False
            result["error"] = str(e)
            result["message"] = f"Pellet inference machine detected inconsistency: {e}"
            
            if debug:
                print(f"❌ [DEBUG] Inference test failed: {e}")
        
        return result
