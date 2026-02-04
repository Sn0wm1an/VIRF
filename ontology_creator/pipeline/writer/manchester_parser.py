#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manchester Syntax Parser - responsible for parsing Manchester Syntax
"""

from typing import Dict, Any, List, Optional
from owlready2 import And, Or, Not


class ManchesterParser:
    """Manchester Syntax Parser"""
    
    def __init__(self, base_writer):
        """
        Initialize parser
        
        Args:
            base_writer: BaseOntologyWriter instance, used to get classes and properties
        """
        self.base_writer = base_writer
    
    def parse_to_owlready2(self, manchester_def: str, debug: bool = False):
        """Parse Manchester Syntax to owlready2 expression"""
        try:
            if debug:
                print(f"    🔍 [DEBUG] Parse Manchester Syntax: {manchester_def}")
            
            # Simple Manchester Syntax parsing
            manchester_def = manchester_def.strip()
            
            # Handle 'and' connection
            if ' and ' in manchester_def.lower():
                parts = manchester_def.split(' and ')
                expressions = []
                
                for part in parts:
                    part = part.strip()
                    if part.startswith('(') and part.endswith(')'):
                        part = part[1:-1]  # Remove brackets
                    
                    if ' some ' in part:
                        # Parse "property some class"
                        prop_parts = part.split(' some ')
                        if len(prop_parts) == 2:
                            property_name = prop_parts[0].strip()
                            target_class = prop_parts[1].strip()
                            
                            prop_obj = self.base_writer.get_property_by_name(property_name)
                            class_obj = self.base_writer.get_class_by_name(target_class)
                            
                            if prop_obj and class_obj:
                                expressions.append(prop_obj.some(class_obj))
                    else:
                        # Simple class name
                        class_obj = self.base_writer.get_class_by_name(part)
                        if class_obj:
                            expressions.append(class_obj)
                
                if expressions:
                    return And(expressions) if len(expressions) > 1 else expressions[0]
            
            # Handle 'or' connection
            elif ' or ' in manchester_def.lower():
                parts = manchester_def.split(' or ')
                expressions = []
                
                for part in parts:
                    part = part.strip()
                    if part.startswith('(') and part.endswith(')'):
                        part = part[1:-1]
                    
                    if ' some ' in part:
                        prop_parts = part.split(' some ')
                        if len(prop_parts) == 2:
                            property_name = prop_parts[0].strip()
                            target_class = prop_parts[1].strip()
                            
                            prop_obj = self.base_writer.get_property_by_name(property_name)
                            class_obj = self.base_writer.get_class_by_name(target_class)
                            
                            if prop_obj and class_obj:
                                expressions.append(prop_obj.some(class_obj))
                    else:
                        class_obj = self.base_writer.get_class_by_name(part)
                        if class_obj:
                            expressions.append(class_obj)
                
                if expressions:
                    return Or(expressions) if len(expressions) > 1 else expressions[0]
            
            # Handle single items constraint
            elif ' some ' in manchester_def:
                parts = manchester_def.split(' some ')
                if len(parts) == 2:
                    property_name = parts[0].strip()
                    target_class = parts[1].strip()
                    
                    prop_obj = self.base_writer.get_property_by_name(property_name)
                    class_obj = self.base_writer.get_class_by_name(target_class)
                    
                    if prop_obj and class_obj:
                        return prop_obj.some(class_obj)
            
            # Simple class name
            else:
                return self.base_writer.get_class_by_name(manchester_def)
            
        except Exception as e:
            if debug:
                print(f"    ❌ [DEBUG] Manchester Syntax parsing failed: {e}")
        
        return None
    
    def parse_conditions(self, manchester_def: str) -> List[Dict[str, Any]]:
        """Parse Manchester Syntax to condition list"""
        conditions = []
        
        # Improved parsing: first process nested brackets, then split
        parts = self._smart_split_and(manchester_def)
        
        for part in parts:
            part = part.strip()
            
            # Clean up extra outer brackets
            while part.startswith('(') and part.endswith(')') and self._is_balanced_brackets(part[1:-1]):
                part = part[1:-1].strip()
            
            if ' some ' in part:
                # Process constraint condition: "hasProperty some Sharp" or "isOn some Child"
                prop_parts = part.split(' some ')
                if len(prop_parts) == 2:
                    property_name = prop_parts[0].strip()
                    target_value = prop_parts[1].strip()
                    
                    # Clean up extra brackets in target value
                    target_value = self._clean_target_brackets(target_value)
                    
                    conditions.append({
                        'type': 'restriction',
                        'property': property_name,
                        'quantifier': 'some',
                        'target': target_value
                    })
            else:
                # Simple class name
                if part and not part.startswith('(') and 'some' not in part:
                    conditions.append({
                        'type': 'class',
                        'value': part
                    })
        
        return conditions
    
    def _smart_split_and(self, text: str) -> List[str]:
        """Smartly split 'and', considering nested brackets"""
        parts = []
        current_part = ""
        bracket_count = 0
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if char == '(':
                bracket_count += 1
            elif char == ')':
                bracket_count -= 1
            
            # Check if it's an 'and' separator
            if (bracket_count == 0 and 
                text[i:i+5] == ' and ' and 
                i + 5 < len(text)):
                
                parts.append(current_part.strip())
                current_part = ""
                i += 5  # Skip ' and '
                continue
            
            current_part += char
            i += 1
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    def _is_balanced_brackets(self, text: str) -> bool:
        """Check if brackets are balanced"""
        count = 0
        for char in text:
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
            if count < 0:
                return False
        return count == 0
    
    def _clean_target_brackets(self, target: str) -> str:
        """Clean up extra brackets in target value"""
        target = target.strip()
        
        # Remove obviously extra ending brackets
        while target.endswith('))') and target.count(')') > target.count('('):
            target = target[:-1]
        
        # Remove mismatched ending brackets
        if target.endswith(')') and target.count(')') > target.count('('):
            target = target[:-1]
        
        return target.strip()
    
    def debug_parse_conditions(self, manchester_def: str) -> List[Dict[str, Any]]:
        """Debug version of parsing conditions, output detailed information"""
        print(f"🔍 [DEBUG] Start parsing Manchester Syntax: {manchester_def}")
        
        # Smartly split
        parts = self._smart_split_and(manchester_def)
        print(f"🔍 [DEBUG] Split parts: {parts}")
        
        conditions = []
        for i, part in enumerate(parts):
            print(f"🔍 [DEBUG] Processing part {i+1}: '{part}'")
            
            part = part.strip()
            
            # Clean up extra outer brackets
            original_part = part
            while part.startswith('(') and part.endswith(')') and self._is_balanced_brackets(part[1:-1]):
                part = part[1:-1].strip()
            
            if original_part != part:
                print(f"🔍 [DEBUG] Bracket cleanup: '{original_part}' -> '{part}'")
            
            if ' some ' in part:
                print(f"🔍 [DEBUG] Found constraint condition")
                prop_parts = part.split(' some ')
                if len(prop_parts) == 2:
                    property_name = prop_parts[0].strip()
                    target_value = prop_parts[1].strip()
                    
                    # Clean up extra brackets in target value
                    clean_target = self._clean_target_brackets(target_value)
                    print(f"🔍 [DEBUG] Found constraint: {property_name} some {clean_target}")
                    
                    conditions.append({
                        'type': 'restriction',
                        'property': property_name,
                        'quantifier': 'some',
                        'target': clean_target
                    })
            else:
                # Simple class name
                if part and not part.startswith('(') and 'some' not in part:
                    print(f"🔍 [DEBUG] Found class: {part}")
                    conditions.append({
                        'type': 'class',
                        'value': part
                    })

        print(f"🔍 [DEBUG] Parse result: {conditions}")
        return conditions
