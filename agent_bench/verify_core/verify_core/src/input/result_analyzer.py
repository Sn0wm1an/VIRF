#!/usr/bin/env python3
"""
Result analysis module
Responsible for analysis and formatting of safety detection results
"""

from typing import Dict, List, Any
from datetime import datetime
from .prompt_formatter import PromptFormatter


class ResultAnalyzer:
    """Result analyzer"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize result analyzer
        
        Args:
            verbose: Whether to output detailed logs
        """
        self.verbose = verbose
        self.prompt_formatter = PromptFormatter(verbose=verbose)
    
    def analyze_results_robust(self, results: Dict[str, Any], error_messages: List[str]) -> Dict[str, Any]:
        """Robust analysis and processing of results"""
        timestamp = datetime.now().isoformat()
        
        # If no results, return default SAFE
        if not results:
            return {
                "status": "SAFE",
                "message": f"WARNING: {len(warnings)} warnings detected, no results to analyze, defaulting to SAFE",
                "timestamp": timestamp,
                "errors_logged": error_messages if error_messages else None
            }
        
        # Check for safety violations
        violations = []
        warnings = []
        unknown_materials = []  # New: unknown material dangers
        
        try:
            # Check for UnknownMaterial related dangers
            unknown_materials.extend(self._extract_unknown_material_dangers(results))
            
            # Extract security-related information from results
            if "safety_violations" in results:
                violations.extend(results["safety_violations"])
            
            if "warnings" in results:
                warnings.extend(results["warnings"])
            
            # Check safety status of each step
            if "steps" in results:
                for step in results["steps"]:
                    if "safety_issues" in step:
                        violations.extend(step["safety_issues"])
                    if "warnings" in step:
                        warnings.extend(step["warnings"])
                        
            # Try to find danger information from other fields in result
            if "hazards" in results and results["hazards"]:
                violations.extend(results["hazards"])
                
            # Check for violated_plan_id or similar fields
            if "violated_plan_id" in results and results["violated_plan_id"]:
                violations.append(f"Plan violation: {results['violated_plan_id']}")
                
        except Exception as e:
            # Error extracting safety information, log but continue
            extract_error = f"Error extracting safety information: {str(e)}"
            error_messages.append(extract_error)
            if self.verbose:
                print(f"[ResultAnalyzer] {extract_error}")
        
        # Determine status based on found issues
        base_result = {
            "timestamp": timestamp,
            "details": results,
            "errors_logged": error_messages if error_messages else None
        }
        
        # Prioritize checking UnknownMaterial dangers - return UNKNOWN status
        if unknown_materials:
            return {
                "status": "UNKNOWN",
                "unknown_materials": unknown_materials,
                "violations": violations,
                "warnings": warnings,
                "message": f"Unknown material dangers detected: {len(unknown_materials)} issues",
                **base_result
            }
        elif violations:
            # Extract dangerous_steps information for formatting prompts
            dangerous_steps = results.get("dangerous_steps", [])
            
            # **Check original result status and maintain**
            result_status = results.get("status", "UNSAFE")  # Get status from original results
            if result_status == "UNKNOWN":
                # If original result status is UNKNOWN, maintain UNKNOWN status
                return {
                    "status": "UNKNOWN",
                    "violations": violations,
                    "warnings": warnings,
                    "dangerous_steps": dangerous_steps,
                    "message": f"Unknown material dangers detected requiring confirmation",
                    **base_result
                }
            elif result_status == "WARNING":
                # If original result status is WARNING, maintain WARNING status
                return {
                    "status": "WARNING",
                    "violations": violations,
                    "warnings": warnings,
                    "dangerous_steps": dangerous_steps,
                    "message": f"Logical inconsistency warnings detected: {len(violations)} issues",
                    **base_result
                }
            
            # If dangerous_steps is empty but has violations, build basic dangerous step structure
            if not dangerous_steps and violations:
                # Build basic dangerous steps from violation information
                constructed_step = {
                    "step_number": "unknown",
                    "action_applied": "unknown action",
                    "hazards": []
                }
                
                # Convert violations to hazard format
                for violation in violations:
                    hazard = {
                        "feedback_details": {
                            "action_info": "unknown action",
                            "violated_rule": {
                                "id": "Generic_Safety_Violation",
                                "warning": str(violation),
                                "danger_level": "Unknown",
                                "reason": str(violation)
                            },
                            "causal_chain": {
                                "message": f"WARNING: {len(violations)} issues detected",
                                "related_objects": []
                            },
                            "suggestion_from_ontology": "Please review the action sequence and modify to avoid safety violations."
                        }
                    }
                    constructed_step["hazards"].append(hazard)
                
                dangerous_steps = [constructed_step]
            
            return {
                "status": "UNSAFE",
                "violations": violations,
                "warnings": warnings,
                "dangerous_steps": dangerous_steps,  # Add dangerous_steps field
                **base_result
            }
        elif warnings:
            return {
                "status": "WARNING",
                "warnings": warnings,
                **base_result
            }
        else:
            return {
                "status": "SAFE",
                "message": f"UNSAFE: {len(violations)} safety violations detected",
                **base_result
            }
    
    def _extract_unknown_material_dangers(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract UnknownMaterial related dangers
        
        Args:
            results: Safety detection results
            
        Returns:
            List of unknown material dangers
        """
        unknown_dangers = []
        
        try:
            # Check if there are UnknownMaterial dangers in dangerous_steps
            if "dangerous_steps" in results:
                for step in results["dangerous_steps"]:
                    if "hazards" in step:
                        for hazard in step["hazards"]:
                            # Check danger type
                            danger_type = hazard.get("type", "")
                            danger_class = hazard.get("danger_class", "")
                            
                            # Check if it's UnknownMaterial related danger
                            if (self._is_unknown_material_danger(danger_type) or 
                                self._is_unknown_material_danger(danger_class) or
                                "UnknownMaterial" in str(hazard)):
                                
                                unknown_dangers.append({
                                    "step": step.get("step_number", "unknown"),
                                    "action": step.get("action_applied", "unknown"),
                                    "hazard": hazard
                                })
            
            # Check direct hazards field
            if "hazards" in results:
                for hazard in results["hazards"]:
                    if "UnknownMaterial" in str(hazard):
                        unknown_dangers.append(hazard)
                        
        except Exception as e:
            if self.verbose:
                print(f"[ResultAnalyzer] Error extracting UnknownMaterial dangers: {str(e)}")
        
        return unknown_dangers
    
    def _is_unknown_material_danger(self, danger_identifier: str) -> bool:
        """
        Check if danger identifier is UnknownMaterial related
        
        Args:
            danger_identifier: Danger identifier
            
        Returns:
            Whether it's UnknownMaterial danger
        """
        if not danger_identifier:
            return False
            
        # Look for specific UnknownMaterial danger identifiers
        unknown_material_patterns = [
            "UnknownMaterial",
            "MicrowaveContainsUnknownMaterialDanger",
            "danger:UnknownMaterial",
            "unknown_material"
        ]
        
        return any(pattern.lower() in danger_identifier.lower() 
                  for pattern in unknown_material_patterns)
    
    def format_safety_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format safety analysis results into prompts
        
        Args:
            analysis_result: Analysis results
            
        Returns:
            Formatted prompt
        """
        return self.prompt_formatter.format_safety_prompt(analysis_result)
    
    def format_simple_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format simple prompts
        
        Args:
            analysis_result: Analysis results
            
        Returns:
            Simple format prompt
        """
        return self.prompt_formatter.format_simple_prompt(analysis_result)
    
    def format_json_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format JSON prompts
        
        Args:
            analysis_result: Analysis results
            
        Returns:
            JSON format prompt
        """
        return self.prompt_formatter.format_json_prompt(analysis_result)
