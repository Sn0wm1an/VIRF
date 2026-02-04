#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refactored ontology writer - using modular architecture
Uses separated functional modules to improve code maintainability
"""

import os
import json
import datetime as dt
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import modular components
from .writer import (
    BaseOntologyWriter, ClassCreator, RuleCreator, 
    ManchesterParser, OWLXMLGenerator, FileManager, ReasoningTester
)


class ModularOntologyWriter(BaseOntologyWriter):
    """Modular ontology writer - using component-based design"""
    
    def __init__(self, ontology_base_path: str = "ontology"):
        """
        Initialize modular writer
        
        Args:
            ontology_base_path: Ontology file root directory path
        """
        super().__init__(ontology_base_path)
        
        # Initialize functional modules
        self.class_creator = ClassCreator(ontology_base_path)
        self.rule_creator = RuleCreator(ontology_base_path)
        self.manchester_parser = ManchesterParser(self)
        self.owl_generator = OWLXMLGenerator()
        self.file_manager = FileManager(self.ontology_base_path)
        self.reasoning_tester = None  # Lazy initialization
    
    def write_analysis_to_ontology(self, analysis_file: str, debug: bool = False) -> Dict[str, Any]:
        """
        Write hierarchy analysis results to ontology using modular components
        
        Args:
            analysis_file: Hierarchy analysis JSON file path
            debug: Debug mode
            
        Returns:
            Write result report
        """
        if debug:
            print(f"\n🚀 [DEBUG] Modular ontology writing process started")
            print(f"📁 [DEBUG] Analysis file: {analysis_file}")
        
        # 1. Backup ontology files
        self.backup_ontology(debug)
        
        # 2. Load analysis data
        analysis_data = self.load_analysis_data(analysis_file, debug)
        if not analysis_data:
            return {"status": "failed", "error": "Unable to load analysis data"}
        
        # 3. Initialize result structure
        write_results = {
            "status": "completed",
            "generated_at": dt.datetime.now().isoformat(),
            "backup_created": True,
            "writes_performed": [],
            "reasoning_test": {},
            "summary": {},
            "analysis_data": analysis_data
        }
        
        try:
            # 4. Load existing ontologies to owlready2 World
            self.load_ontologies_to_world(debug)
            
            # Synchronize ontology mappings to each module
            self._sync_ontologies_to_modules()
            
            # 5. Use class creator to create new classes
            classes_result = self.class_creator.create_new_classes(analysis_data, debug)
            write_results["writes_performed"].append(classes_result)
            
            # 6. Use rule creator to create safety rules
            rules_result = self.rule_creator.create_safety_rules(analysis_data, debug)
            write_results["writes_performed"].append(rules_result)
            
            # 7. Use file manager to save ontology files
            save_result = self.file_manager.save_ontologies(
                self.class_creator.new_classes_xml,
                self.rule_creator.new_rules_xml,
                debug
            )
            write_results["writes_performed"].append(save_result)
            
            # 8. Initialize and run reasoning tester
            self.reasoning_tester = ReasoningTester(self.world, self.ontologies)
            reasoning_result = self.reasoning_tester.run_reasoning_test(debug)
            write_results["reasoning_test"] = reasoning_result
            
            # 9. Generate write summary
            write_results["summary"] = self._generate_summary(write_results)
            
        except Exception as e:
            write_results["status"] = "failed"
            write_results["error"] = str(e)
            if debug:
                print(f"❌ [DEBUG] Modular writing process error: {e}")
                import traceback
                traceback.print_exc()
        
        return write_results
    
    def _sync_ontologies_to_modules(self):
        """Synchronize ontology mappings to each functional module"""
        # Synchronize to class creator
        self.class_creator.world = self.world
        self.class_creator.ontologies = self.ontologies
        self.class_creator.loaded_classes = self.loaded_classes
        self.class_creator.loaded_properties = self.loaded_properties
        
        # Synchronize to rule creator
        self.rule_creator.world = self.world
        self.rule_creator.ontologies = self.ontologies
        self.rule_creator.loaded_classes = self.loaded_classes
        self.rule_creator.loaded_properties = self.loaded_properties
    
    def _generate_summary(self, write_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate write summary"""
        total_classes = 0
        total_rules = 0
        
        for op in write_results.get("writes_performed", []):
            if op.get("operation") == "create_new_classes_owlready2":
                total_classes += len(op.get("classes_created", []))
            elif op.get("operation") == "create_safety_rules_owlready2":
                total_rules += len(op.get("rules_created", []))
        
        return {
            "total_classes_written": total_classes,
            "total_rules_written": total_rules,
            "files_modified": len([
                op for op in write_results.get("writes_performed", [])
                if op.get("status") == "completed"
            ]),
            "reasoning_passed": write_results.get("reasoning_test", {}).get("consistency", False)
        }
    
    def write_rules_to_file(self, rules: List[Dict[str, Any]], target_file: str = None) -> bool:
        """Convenience method for writing safety rules to file"""
        return self.file_manager.write_rules_to_rag_kitchen(rules, debug=True)


def write_ontology_from_analysis(analysis_file: str, debug: bool = False) -> Dict[str, Any]:
    """
    Convenience function for writing ontology from hierarchy analysis results (modular version)
    
    Args:
        analysis_file: Hierarchy analysis JSON file path
        debug: Debug mode
        
    Returns:
        Write result report
    """
    writer = ModularOntologyWriter()
    return writer.write_analysis_to_ontology(analysis_file, debug)


if __name__ == "__main__":
    # Test case
    test_file = "test_output/hierarchy_analysis_20250901_025837.json"
    if os.path.exists(test_file):
        result = write_ontology_from_analysis(test_file, debug=True)
        print(f"\n📋 Write result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"Test file does not exist: {test_file}")
