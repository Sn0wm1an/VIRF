#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rule Creator - responsible for creating safety rules
"""

from typing import Dict, Any, List
from owlready2 import Thing
from .base_writer import BaseOntologyWriter


class RuleCreator(BaseOntologyWriter):
    """Rule Creator - responsible for creating safety rules"""
    
    def create_safety_rules(self, analysis_data: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
        """Use owlready2 to create safety rules"""
        result = {
            "operation": "create_safety_rules_owlready2",
            "rules_created": [],
            "status": "completed"
        }
        
        try:
            # Extract rule data from rule_safety_attributes.rule_safety_attributes
            rule_analysis = analysis_data.get('rule_safety_attributes', {})
            rule_items = rule_analysis.get('rule_safety_attributes', {})
            
            if debug:
                print(f"\n⚠️ [DEBUG] Use owlready2 to create {len(rule_items)} items safety rules")
            
            # Get rag_kitchen ontology
            rag_onto = self.ontologies.get('rag_kitchen')
            if not rag_onto:
                if debug:
                    print(f"⚠️ [DEBUG] rag_kitchen ontology not found, skip safety rule creation")
                return result
            
            with rag_onto:
                for rule_name, rule_data in rule_items.items():
                    if not rule_data or rule_data.get('generation_status') != 'success':
                        if debug:
                            print(f"  ⚠️ [DEBUG] Skip {rule_name}: generation status not success")
                        continue
                    
                    # Get rule name
                    improved_name = rule_data.get('improved_rule_name', rule_name)
                    
                    # Get Manchester definition
                    manchester_def = rule_data.get('rule_definition', '')
                    if not manchester_def:
                        if debug:
                            print(f"  ⚠️ [DEBUG] Skip {rule_name}: missing rule definition")
                        continue
                    
                    # Get safety attributes
                    safety_attrs_data = rule_data.get('safety_attributes', {})
                    if safety_attrs_data.get('status') != 'success':
                        if debug:
                            print(f"  ⚠️ [DEBUG] Skip {rule_name}: safety attributes generation failed")
                        continue
                    
                    safety_attrs = {
                        'danger_level': safety_attrs_data.get('danger_level', 2),
                        'safety_warning': safety_attrs_data.get('safety_warning', 'Please pay attention to safety operations'),
                        'trigger_reason': safety_attrs_data.get('trigger_reason', 'Potential safety risk')
                    }
                    
                    # Create safety rule class
                    rule_class_name = f"{improved_name}Danger"
                    if debug:
                        print(f"  🔧 [DEBUG] Create safety rule: {rule_class_name}")
                    
                    # Use owlready2 to create rule class
                    rule_class = type(rule_class_name, (Thing,), {})
                    rule_class.label = [f"{improved_name} Safety Rule"]
                    rule_class.comment = [f"Safety rule for {improved_name}"]
                    
                    # Parse Manchester syntax and set equivalent class
                    try:
                        from .manchester_parser import ManchesterParser
                        parser = ManchesterParser(self)
                        equivalent_expr = parser.parse_to_owlready2(manchester_def, debug)
                        if equivalent_expr:
                            rule_class.equivalent_to = [equivalent_expr]
                            if debug:
                                print(f"    ✅ [DEBUG] Manchester syntax parsing successful: {manchester_def}")
                        else:
                            if debug:
                                print(f"    ⚠️ [DEBUG] Manchester syntax parsing failed: {manchester_def}")
                    except Exception as e:
                        if debug:
                            print(f"    ❌ [DEBUG] Manchester syntax parsing error: {e}")
                    
                    # Generate corresponding XML representation (for manual appending)
                    from .owl_generator import OWLXMLGenerator
                    generator = OWLXMLGenerator()
                    rule_xml = generator.generate_rule_xml(improved_name, manchester_def, safety_attrs)
                    self.new_rules_xml.append(rule_xml)
                    
                    result["rules_created"].append({
                        "name": rule_class_name,
                        "rule_name": improved_name,
                        "manchester_definition": manchester_def,
                        "safety_attributes": safety_attrs
                    })
                    
                    if debug:
                        print(f"    ✅ [DEBUG] Safety rule created successfully: {rule_class_name}")
            
            if debug:
                print(f"✅ [DEBUG] Successfully created {len(result['rules_created'])} items safety rules")
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            if debug:
                print(f"❌ [DEBUG] Safety rule creation failed: {e}")
        
        return result
    
    def write_rules_to_file(self, rules: List[Dict[str, Any]], target_file: str = None) -> bool:
        """Write safety rules to rag-kitchen.owl file"""
        if not target_file:
            target_file = self.ontology_base_path / "domain" / "rag-kitchen.owl"
        
        try:
            if debug:
                print(f"📝 [DEBUG] Start writing safety rules to: {target_file}")
            
            # Read existing file content
            content = ""
            if target_file.exists():
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if debug:
                    print(f"📖 [DEBUG] Read existing file content ({len(content)} characters)")
            else:
                if debug:
                    print(f"❌ [DEBUG] Target file does not exist: {target_file}")
                return False
            
            # Generate rules XML
            from .owl_generator import OWLXMLGenerator
            generator = OWLXMLGenerator()
            
            rules_xml = ""
            for rule in rules:
                rule_name = rule.get('rule_name', f'Rule{len(rules)}')
                manchester_def = rule.get('manchester_definition', '')
                safety_attrs = rule.get('safety_attributes', {})
                
                rule_xml = generator.generate_rule_xml(rule_name, manchester_def, safety_attrs)
                rules_xml += rule_xml + "\n"
            
            # Find </rdf:RDF> tag position for insertion
            insert_position = content.rfind('</rdf:RDF>')
            if insert_position != -1:
                new_content = content[:insert_position] + rules_xml + content[insert_position:]
            else:
                # If </rdf:RDF> is not found, add at the end of the file
                new_content = content.rstrip() + "\n" + rules_xml + "\n</rdf:RDF>"
            
            # Write to file
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            if debug:
                print(f"✅ [DEBUG] Successfully written {len(rules)} items safety rules to rag-kitchen.owl")
            return True
            
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Failed to write safety rules: {str(e)}")
            return False
