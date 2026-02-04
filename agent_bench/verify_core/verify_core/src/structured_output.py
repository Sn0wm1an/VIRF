#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for generating structured safety reports
"""

from typing import Dict, Any, List
import re

def _extract_safety_warning(hazard_details: Dict[str, Any]) -> str:
    """
    Extract safety warning information from hazard_details
    """
    safety_warning = hazard_details.get('safety_warning')
    if isinstance(safety_warning, list) and len(safety_warning) > 0:
        return str(safety_warning[0])
    elif safety_warning:
        return str(safety_warning)
    return ''

def _extract_danger_level(hazard_details: Dict[str, Any]) -> str:
    """
    Extract danger level from hazard_details
    """
    danger_level = hazard_details.get('danger_level')
    if isinstance(danger_level, list) and len(danger_level) > 0:
        return str(danger_level[0])
    elif danger_level is not None:
        return str(danger_level)
    return ''

def _extract_trigger_reason(hazard_details: Dict[str, Any]) -> str:
    """
    Extract trigger reason from hazard_details
    """
    trigger_reason = hazard_details.get('trigger_reason')
    if isinstance(trigger_reason, list) and len(trigger_reason) > 0:
        return str(trigger_reason[0])
    elif trigger_reason:
        return str(trigger_reason)
    return ''

def _extract_related_objects(hazard_details: Dict[str, Any]) -> List[str]:
    """
    Extract related object instances from hazard_details
    """
    related_objects = []
    
    # Extract object names from causal_chain message
    causal_chain = hazard_details.get('causal_chain', {})
    message = causal_chain.get('message', '')
    
    # Use regex to extract possible object names (usually containing underscores or specific patterns)
    if message:
        # Find object names in formats like "TestPot_Dual", "TestMicrowave_Action"
        object_pattern = r'\b[A-Z][a-zA-Z]*_[A-Za-z0-9]+\b'
        matches = re.findall(object_pattern, message)
        related_objects.extend(matches)
        
        # Find other possible object name patterns
        if 'identified as dangerous' in message:
            parts = message.split('identified as dangerous')
            if len(parts) > 0:
                obj_part = parts[0].strip()
                # 提取最后一个可能的对象名称
                obj_words = obj_part.split()
                if obj_words:
                    potential_obj = obj_words[-1]
                    if potential_obj not in related_objects:
                        related_objects.append(potential_obj)
    
    # Extract material-related objects from key_facts
    key_facts = causal_chain.get('key_facts', [])
    for fact in key_facts:
        if isinstance(fact, str) and ('材料:' in fact or 'material:' in fact.lower()):
            # This indicates objects with specific materials exist
            pass
    
    # Return empty list if no specific objects found
    return list(set(related_objects))  # Remove duplicates

def create_hazard_feedback_details(action_info_str: str, hazard_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build feedback_details block for a single hazard
    
    Args:
        action_info_str: Action string that caused the hazard
        hazard_details: Detailed hazard information from SafetyVerifier
        
    Returns:
        Dictionary containing feedback_details
    """
    
    # 1. Change action_info to direct string format
    action_info = action_info_str
    
    # 2. Expand violated_rule structure
    original_violated_rule = hazard_details.get('violated_rule', {})
    violated_rule = {
        "id": original_violated_rule.get('id', 'UnknownRule'),
        "warning": _extract_safety_warning(hazard_details),
        "danger_level": _extract_danger_level(hazard_details), 
        "reason": _extract_trigger_reason(hazard_details)
    }
    
    # 3. Modify causal_chain to show related object instances
    original_causal_chain = hazard_details.get('causal_chain', {})
    causal_chain = {
        "message": original_causal_chain.get('message', 'No causal chain information available.'),
        "related_objects": _extract_related_objects(hazard_details),
        "key_facts": original_causal_chain.get('key_facts', [])
    }
    
    # Build feedback_details block
    feedback = {
        "feedback_details": {
            "action_info": action_info,
            "violated_rule": violated_rule,
            "causal_chain": causal_chain
        }
    }
    
    # Only add suggestion when it's not null
    suggestion = hazard_details.get('suggestion_from_ontology')
    if suggestion:
        feedback["feedback_details"]["suggestion_from_ontology"] = suggestion
    return feedback
