#!/usr/bin/env python3
"""
Prompt formatting module
Responsible for formatting safety analysis results into different types of prompts
"""

from typing import Dict, List, Any, Optional


class PromptFormatter:
    """Prompt formatter"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize prompt formatter
        
        Args:
            verbose: Whether to output detailed logs
        """
        self.verbose = verbose
    
    def format_safety_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format safety prompts based on analysis results
        
        Args:
            analysis_result: Safety analysis results
            
        Returns:
            Formatted prompt
        """
        status = analysis_result.get("status", "SAFE")
        
        if status == "SAFE":
            return ""
        elif status == "UNSAFE":
            return self.format_unsafe_prompt(analysis_result)
        elif status == "WARNING":
            return self.format_warning_prompt(analysis_result)
        elif status == "UNKNOWN":
            return self.format_unknown_prompt(analysis_result)
        else:
            return ""
    
    def format_unsafe_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format prompts for UNSAFE status
        
        Args:
            analysis_result: Safety analysis results containing UNSAFE status
            
        Returns:
            Formatted UNSAFE prompt
        """
        # Extract dangerous step information
        dangerous_steps = analysis_result.get("dangerous_steps", [])
        
        if not dangerous_steps:
            return "Safety violation detected but no specific dangerous steps identified."
        
        # Process first dangerous step
        main_danger = dangerous_steps[0]
        step_number = main_danger.get("step_number", "unknown")
        action_applied = main_danger.get("action_applied", "unknown action")
        
        # Get detailed information of first hazard
        hazards = main_danger.get("hazards", [])
        if not hazards:
            return f"Dangerous step {step_number} detected but no hazard details available."
        
        main_hazard = hazards[0]
        details = main_hazard.get("feedback_details", {})
        
        # Extract information from each part
        action_info = details.get("action_info", "unknown action")
        violated_rule = details.get("violated_rule", {})
        causal_chain = details.get("causal_chain", {})
        suggestion = details.get("suggestion_from_ontology")
        
        rule_id = violated_rule.get("id", "Unknown Rule")
        rule_warning = violated_rule.get("warning", "No warning available")
        danger_level = violated_rule.get("danger_level", "Unknown")
        trigger_reason = violated_rule.get("reason", "No reason provided")
        
        causal_message = causal_chain.get("message", "No causal explanation available")
        related_objects = causal_chain.get("related_objects", [])
        
        # Build formatted prompt
        formatted_prompt = f"""ATTENTION: Your previous plan has failed a safety verification.
---------------------------------------------------------------------
DIAGNOSTIC REPORT
---------------------------------------------------------------------

[FAILURE ANALYSIS]
The plan was rejected at STEP {step_number} during the simulation of the action '{action_info}'.

[VIOLATED SAFETY RULE]
Rule ID: {rule_id}
Danger Level: {danger_level}
Safety Warning: {rule_warning}

[CAUSAL EXPLANATION]
The logical reason for this failure is: {trigger_reason}
System Analysis: {causal_message}"""

        # Add related object information (if available)
        if related_objects:
            objects_str = ", ".join(related_objects)
            formatted_prompt += f"""

[INVOLVED OBJECTS]
The following objects are involved in this safety violation: {objects_str}"""

        # Add suggestions (if available)
        if suggestion:
            formatted_prompt += f"""

[SUGGESTED CORRECTION]
A potential way to resolve this is: {suggestion}"""

        formatted_prompt += """

---------------------------------------------------------------------
NEW INSTRUCTION:
You should REFUSE to execute this plan.
"""

        return formatted_prompt
    
    def format_warning_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format prompts for WARNING status
        
        Args:
            analysis_result: Safety analysis results containing WARNING status
            
        Returns:
            Formatted WARNING prompt
        """
        # Extract dangerous step information
        dangerous_steps = analysis_result.get("dangerous_steps", [])
        
        if not dangerous_steps:
            return "Warning detected but no specific steps identified."
        
        # Process first warning step
        main_warning = dangerous_steps[0]
        step_number = main_warning.get("step_number", "unknown")
        action_applied = main_warning.get("action_applied", "unknown action")
        
        # Get detailed information of first hazard
        hazards = main_warning.get("hazards", [])
        if not hazards:
            return f"Warning in step {step_number} but no hazard details available."
        
        main_hazard = hazards[0]
        details = main_hazard.get("feedback_details", {})
        
        # Extract detailed information
        violated_rule = details.get("violated_rule", {})
        rule_id = violated_rule.get("id", "Unknown Rule")
        warning = violated_rule.get("warning", "No warning message available")
        danger_level = violated_rule.get("danger_level", "Unknown")
        
        causal_chain = details.get("causal_chain", {})
        message = causal_chain.get("message", "No causal explanation available")
        related_objects = causal_chain.get("related_objects", [])
        related_objects_string = ", ".join(related_objects) if related_objects else "No specific objects identified"
        
        suggestion = details.get("suggestion_from_ontology", "No specific suggestion available")
        
        # Generate WARNING template prompt
        prompt = f"""# ROLE
You are an intelligent, creative, and safety-conscious robotic planner. Your previous attempt to create a plan was rejected due to a critical safety violation. Your new task is to carefully analyze the following diagnostic report and generate a new, completely safe plan to achieve the original user's goal.

# --- DIAGNOSTIC REPORT OF FAILED PLAN ---

## 🚨 Safety Violation Detected

* **Failed Step**: Step {step_number} ("{action_applied}")
* **Violated Safety Concept**: {rule_id} (Danger Level: {danger_level})
* **Safety Warning**: {warning}

## 🧠 Logical Explanation & Causal Chain

The plan failed because the verifier deduced the following:
{message}

## 🔑 Key Involved Objects

The core of the problem involves the interaction between the following objects:
- {related_objects_string}

## 💡 Correction Suggestion from Knowledge Base
{suggestion}

# --- NEW INSTRUCTION ---

Based on the detailed diagnostic report above, your goal is to devise a **new, alternative plan** that achieves the original user command while **strictly avoiding the identified hazard**.

Think creatively. If the original approach is blocked (e.g., a specific object cannot be used), find another object or a different sequence of actions. Your new plan must be logically sound and verifiably safe.

"""
        
        return prompt
    
    def format_unknown_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format prompts for UNKNOWN status
        
        Args:
            analysis_result: Safety analysis results containing UNKNOWN status
            
        Returns:
            Formatted UNKNOWN prompt
        """
        # Check for unknown material dangers
        unknown_materials = analysis_result.get("unknown_materials", [])
        
        if not unknown_materials:
            return "❓ Unknown situation detected, further safety confirmation required."
        
        # Build UNKNOWN status prompt
        prompt = """# ❓ MATERIAL SAFETY INQUIRY REQUIRED

## 🔍 Situation Analysis
Your action plan cannot be automatically verified due to **unknown material properties**. The safety verifier has detected objects with unidentified materials that may pose risks.

## 📋 Unknown Material Details:"""

        # Process detailed information of unknown material issues
        for i, unknown in enumerate(unknown_materials, 1):
            if isinstance(unknown, dict):
                step = unknown.get("step", "unknown")
                action = unknown.get("action", "unknown action")
                hazard = unknown.get("hazard", {})
                
                prompt += f"""

### Issue #{i}
- **Step**: {step}
- **Action**: {action}
- **Material Status**: Unknown/Unidentified
- **Additional Information**: This issue requires further clarification on the material properties involved."""
                
                # Try to extract more information from hazard
                if isinstance(hazard, dict):
                    feedback_details = hazard.get("feedback_details", {})
                    if feedback_details:
                        violated_rule = feedback_details.get("violated_rule", {})
                        warning = violated_rule.get("warning", "")
                        if warning:
                            prompt += f"\n- **Safety Concern**: {warning}"

        prompt += """

## 🤔 Required Action

**PLEASE CLARIFY**: 
1. What specific materials are involved in the objects mentioned?
2. Are these materials safe for the intended use (especially heating/cooking)?
3. Should the plan proceed, be modified, or be abandoned?

## ⚠️ Safety Recommendation

Until material safety is confirmed, consider:
- **PAUSE** execution of the current plan
- **REQUEST** material information from the user  
- **SUGGEST** alternative approaches using known-safe materials

**Do not proceed with potentially unsafe actions involving unknown materials.**
"""

        return prompt
    
    def format_simple_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format simple prompts (for debugging or simplified scenarios)
        
        Args:
            analysis_result: Safety analysis results
            
        Returns:
            Formatted simple prompt
        """
        status = analysis_result.get("status", "SAFE")
        
        if status == "SAFE":
            return "No safety violations detected. The action sequence is safe to execute."
        elif status == "UNSAFE":
            return "UNSAFE: This action sequence contains safety violations and should not be executed."
        elif status == "WARNING":
            return "WARNING: This action sequence may contain potential safety issues. Please review carefully."
        else:
            return "UNKNOWN: Unable to determine safety status of the action sequence."
    
    def format_json_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format JSON format prompts (for API calls or structured output)
        
        Args:
            analysis_result: Safety analysis results
            
        Returns:
            JSON format prompt
        """
        import json
        
        prompt_data = {
            "safety_status": analysis_result.get("status", "SAFE"),
            "timestamp": analysis_result.get("timestamp", ""),
            "message": self.format_safety_prompt(analysis_result)
        }
        
        if "dangerous_steps" in analysis_result:
            prompt_data["dangerous_steps"] = analysis_result["dangerous_steps"]
        
        return json.dumps(prompt_data, ensure_ascii=False, indent=2)
