#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File manager - responsible for file operations and content appending
"""

import os
from typing import Dict, List
from pathlib import Path


class FileManager:
    """File manager - responsible for file operations and content appending"""
    
    def __init__(self, ontology_base_path: Path):
        """
        Initialize file manager
        
        Args:
            ontology_base_path: ontology file root directory path
        """
        self.ontology_base_path = ontology_base_path
    
    def save_ontologies(self, new_classes_xml: List[str], new_rules_xml: List[str], debug: bool = False) -> Dict[str, any]:
        """Manually append new content to OWL files, without overwriting existing content"""
        result = {
            "operation": "manual_append_to_owl_files",
            "files_modified": [],
            "status": "completed"
        }
        
        try:
            if debug:
                print(f"\n✏️ [DEBUG] Manually append content to OWL files (without overwriting existing content)")
            
            # Collect new content to be written
            new_content = {
                "object": new_classes_xml.copy(),
                "rag_kitchen": new_rules_xml.copy()
            }
            
            if debug:
                print(f"  🔍 [DEBUG] Collect {len(new_classes_xml)} items new classes, {len(new_rules_xml)} items new rules")
            
            # Append content to files one by one
            for file_type, content_list in new_content.items():
                if not content_list:
                    continue
                    
                # Determine file path
                if file_type == "object":
                    file_path = self.ontology_base_path / "core" / "object.owl"
                elif file_type == "rag_kitchen":
                    file_path = self.ontology_base_path / "domain" / "rag-kitchen.owl"
                else:
                    continue
                
                if debug:
                    print(f"  📝 [DEBUG] Append {len(content_list)} items content to {file_path}")
                
                # Manually append to file
                self.append_to_owl_file(file_path, content_list, debug)
                result["files_modified"].append(str(file_path))
            
            if debug:
                print(f"✅ [DEBUG] Manually appended {len(result['files_modified'])} items files")
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            if debug:
                print(f"❌ [DEBUG] Manually append failed: {e}")
        
        return result
    
    def append_to_owl_file(self, file_path: Path, new_content: List[str], debug: bool = False):
        """Append new content to OWL file at the end"""
        try:
            # Read existing file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the position of the </rdf:RDF> end tag (actual end tag of the OWL file)
            end_tag = "</rdf:RDF>"
            end_pos = content.rfind(end_tag)
            
            if end_pos == -1:
                if debug:
                    print(f"    ⚠️ [DEBUG] End tag </rdf:RDF> not found, skip file {file_path}")
                return
            
            # Check for duplicate content
            filtered_content = []
            for new_item in new_content:
                # Extract class name for duplicate check
                if 'rdf:about="#' in new_item:
                    class_name = new_item.split('rdf:about="#')[1].split('"')[0]
                    if f'rdf:about="#{class_name}"' not in content:
                        filtered_content.append(new_item)
                    else:
                        if debug:
                            print(f"    ⚠️ [DEBUG] Skip duplicate class: {class_name}")
                else:
                    filtered_content.append(new_item)
            
            if not filtered_content:
                if debug:
                    print(f"    ℹ️ [DEBUG] No new content to append to {file_path}")
                return
            
            # Insert new content before the end tag
            before_end = content[:end_pos]
            after_end = content[end_pos:]
            
            # Build new content string
            new_content_str = "\n".join(filtered_content) + "\n\n"
            
            # Merge content
            updated_content = before_end + new_content_str + after_end
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            if debug:
                print(f"    ✅ [DEBUG] Successfully appended {len(filtered_content)} items content to {file_path}")
                
        except Exception as e:
            if debug:
                print(f"    ❌ [DEBUG] Append failed {file_path}: {e}")
            raise
    
    def write_rules_to_rag_kitchen(self, rules: List[Dict[str, any]], debug: bool = False) -> bool:
        """Write safety rules to rag-kitchen.owl file"""
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
            
            # Find the position of the </rdf:RDF> tag for insertion
            insert_position = content.rfind('</rdf:RDF>')
            if insert_position != -1:
                new_content = content[:insert_position] + rules_xml + content[insert_position:]
            else:
                # If </rdf:RDF> tag is not found, append at the end of the file
                new_content = content.rstrip() + "\n" + rules_xml + "\n</rdf:RDF>"
            
            # Write to file
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            if debug:
                print(f"✅ [DEBUG] Successfully written {len(rules)} items safety rules to rag-kitchen.owl")
            return True
            
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Write safety rules failed: {str(e)}")
            return False
