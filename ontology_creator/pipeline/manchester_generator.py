#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manchester syntax generator - Convert hazard descriptions to Manchester OWL syntax
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add project root directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from llm.llm_service import call_llm
from pipeline.relation_extractor import RelationExtractor
from pipeline.manchester_json_validator import ManchesterJSONValidator


class ManchesterGenerator:
    """Manchester syntax generator"""
    
    def __init__(self):
        """Initialize generator"""
        self.relation_extractor = RelationExtractor()
        self.json_validator = ManchesterJSONValidator()
        
        # Define fixed attribute relations
        self.required_attribute_relations = {
            'hasMaterial', 'hasState', 'hasProperty'
        }
        
        # Get valid spatial relations
        self.valid_spatial_relations = self.relation_extractor.get_spatial_relations()
        
        print(f"🏗️ Initializing Manchester syntax generator")
        print(f"📋 Available spatial relations: {len(self.valid_spatial_relations)} items")
        print(f"🏷️ Fixed attribute relations: {len(self.required_attribute_relations)} items")
    
    def generate_manchester_syntax(self, hazard_description: str) -> str:
        """
        Convert hazard description to Manchester syntax
        
        Args:
            hazard_description: Hazard description text
            
        Returns:
            Manchester syntax string
        """
        print(f"\n🔄 Starting Manchester syntax generation")
        print(f"📝 Input: {hazard_description}")
        
        try:
            # Build prompt data
            prompt_data = self._build_prompt_data(hazard_description)
            
            # Call LLM to generate Manchester syntax
            response = call_llm('manchester_generation', **prompt_data)
            
            if response:
                # Validate and clean response
                cleaned_syntax = self._clean_manchester_syntax(response)
                print(f"✅ Successfully generated Manchester syntax")
                
                # Perform vector validation
                print(f"\n🔍 Starting vector validation")
                validation_report = self.json_validator.validate_manchester_json(cleaned_syntax)
                
                return {
                    "manchester_json": cleaned_syntax,
                    "validation_report": validation_report
                }
            else:
                raise Exception("LLM did not return valid response")
                
        except Exception as e:
            print(f"❌ Error generating Manchester syntax: {e}")
            raise
    
    def _build_prompt_data(self, hazard_description: str) -> Dict[str, Any]:
        """Build LLM prompt data"""
        
        # Build available relations list
        spatial_relations_list = "\n".join([f"- {rel}" for rel in sorted(self.valid_spatial_relations)])
        attribute_relations_list = "\n".join([f"- {rel}" for rel in sorted(self.required_attribute_relations)])
        
        return {
            'text': hazard_description,  # Parameter name expected by LLM client
            'spatial_relations': spatial_relations_list,
            'attribute_relations': attribute_relations_list,
            'example_input': "Store sharp utensils like kitchen shears and knives safely to prevent harm.",
            'example_output': self._get_example_output()
        }
    
    def _get_example_output(self) -> str:
        """Get example output"""
        return """Class: Utensil
Class: SharpUtensil
SubClassOf: Utensil
Class: Knife
SubClassOf: SharpUtensil
Class: KitchenShears
SubClassOf: SharpUtensil
Class: StorageMethod
Class: SafeStorageMethod
SubClassOf: StorageMethod
Class: UnsafeStorageMethod
SubClassOf: StorageMethod
DisjointWith: SafeStorageMethod
Class: Harm
Class: HazardousSituation
ObjectProperty: hasStorageMethod
Domain: Utensil
Range: StorageMethod
ObjectProperty: mayCause
Domain: HazardousSituation
Range: Harm
Class: HazardousSituation
EquivalentTo: SharpUtensil and (hasStorageMethod some UnsafeStorageMethod)"""
    
    def _clean_manchester_syntax(self, raw_response: str) -> str:
        """Clean and validate Manchester syntax response"""
        
        # Remove extra blank lines and formatting
        lines = raw_response.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    
    def validate_syntax(self, manchester_syntax: str) -> Dict[str, Any]:
        """Validate generated Manchester syntax"""
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        lines = manchester_syntax.strip().split('\n')
        
        # Count various syntax elements
        classes = []
        properties = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Class:'):
                classes.append(line.replace('Class:', '').strip())
            elif line.startswith('ObjectProperty:'):
                properties.append(line.replace('ObjectProperty:', '').strip())
        
        validation_result['statistics'] = {
            'total_lines': len([l for l in lines if l.strip()]),
            'classes': len(classes),
            'properties': len(properties)
        }
        
        return validation_result


if __name__ == "__main__":
    # Test Manchester syntax generator
    generator = ManchesterGenerator()
    
    # Test example
    test_description = "Store sharp utensils like kitchen shears and knives safely to prevent harm."
    
    result = generator.generate_manchester_syntax(test_description)
    
    print(f"\n📋 Generated Manchester syntax:")
    print("=" * 50)
    print(result)
    print("=" * 50)
    
    # Validate results
    validation = generator.validate_syntax(result)
    print(f"\n🔍 Validation results: {validation}")
