"""
Ontology hierarchy analyzer - Step3 core component
Analyzes the optimal placement of new classes in the ontology hierarchy
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import json
from datetime import datetime

# Add project root path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from pipeline.ontology_hierarchy_extractor import OntologyHierarchyExtractor
from llm.llm_service import call_llm


class HierarchyAnalyzer:
    """Ontology hierarchy analyzer"""
    
    def __init__(self):
        """Initialize analyzer"""
        self.extractor = OntologyHierarchyExtractor()
        self.hierarchies = None
        
    def initialize_hierarchies(self):
        """Initialize ontology hierarchy data"""
        from pathlib import Path
        
        def _deep_serialize_paths(obj):
            """Deep serialize all Path objects to strings"""
            if isinstance(obj, (Path, type(Path()))):
                return str(obj)
            elif hasattr(obj, '__fspath__'):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: _deep_serialize_paths(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [_deep_serialize_paths(item) for item in obj]
            elif isinstance(obj, set):
                return list(_deep_serialize_paths(list(obj)))
            else:
                return obj
        
        print("🌳 Initializing ontology hierarchy data...")
        raw_hierarchies = self.extractor.extract_all_hierarchies()
        self.hierarchies = _deep_serialize_paths(raw_hierarchies)
        print(f"✅ Successfully loaded {len(self.hierarchies)} ontology hierarchies (Path objects serialized)")
        
    def analyze_missing_items(self, validation_report_path: str, debug: bool = False) -> Dict[str, Any]:
        """Analyze the placement of missing items in the hierarchy"""
        if not self.hierarchies:
            self.initialize_hierarchies()
            
        print(f"\n🔍 Step3: Starting analysis of missing item hierarchy placement")
        
        # Load validation report
        validation_report = self._load_validation_report(validation_report_path)
        
        # Collect all missing items
        missing_items = self._collect_missing_items(validation_report)
        if not missing_items:
            print("✅ No missing items found, no hierarchy analysis needed")
            return {
                "step": "step3_hierarchy_analysis",
                "status": "completed",
                "message": "No missing items need analysis",
                "missing_items_analysis": {}
            }
            
        print(f"📋 Found {len(missing_items)} missing items need analysis")
        
        # Analyze each missing item by category
        analysis_results = {}
        
        for category, items in missing_items.items():
            if not items:
                continue
                
            print(f"\n📂 Analyzing {category} category {len(items)} missing items")
            
            category_analysis = self._analyze_category_items(category, items, debug)
            if category_analysis:
                analysis_results[category] = category_analysis
                
        # Analyze complex rules in propertyChains and generate safety attributes
        property_chains_validation = validation_report.get('validations', {}).get('property_chains', {})
        complex_definitions = property_chains_validation.get('complex_definitions', [])
        
        rule_safety_attributes = {}
        if complex_definitions:
            print(f"\n⚠️ Generating {len(complex_definitions)} rule safety attributes")
            rule_safety_attributes = self._generate_rule_safety_attributes(complex_definitions, debug)
        
        def serialize_paths(obj):
            """Recursively convert Path objects to strings"""
            from pathlib import Path
            if isinstance(obj, Path):
                return str(obj)
            elif hasattr(obj, '__fspath__'):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: serialize_paths(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize_paths(item) for item in obj]
            elif isinstance(obj, set):
                return list(serialize_paths(list(obj)))
            else:
                return obj

        result = {
            "step": "step3_hierarchy_analysis", 
            "status": "completed",
            "generated_at": datetime.now().isoformat(),
            "total_missing_items": sum(len(items) for items in missing_items.values()),
            "categories_analyzed": list(analysis_results.keys()),
            "missing_items_analysis": analysis_results,
            "rule_safety_attributes": rule_safety_attributes,
            "summary": self._generate_analysis_summary(analysis_results)
        }
        
        return serialize_paths(result)
    
    def _collect_missing_items(self, validation_report: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Collect all missing items from validation report"""
        missing_items = {
            'objects': [],
            'materials': [],
            'attributes': [],
            'states': [],
            'dangers': []
        }
        
        # Extract missing items from validation report results
        validations = validation_report.get('validations', {})
        
        for category_key, category_data in validations.items():
            if not isinstance(category_data, dict):
                continue
            
            # Collect missing_items and similar_items (similar_items also need hierarchy analysis)
            category_missing = category_data.get('missing_items', [])
            category_similar = category_data.get('similar_items', [])
            
            # Merge missing and similar items
            all_items = category_missing + category_similar
            
            # Map to corresponding categories
            if 'object' in category_key.lower():
                missing_items['objects'].extend(all_items)
            elif 'material' in category_key.lower():
                missing_items['materials'].extend(all_items)
            elif 'attribute' in category_key.lower():
                missing_items['attributes'].extend(all_items)
            elif 'state' in category_key.lower():
                missing_items['states'].extend(all_items)
            elif 'danger' in category_key.lower():
                missing_items['dangers'].extend(all_items)
                
        return missing_items
    
    def _analyze_complex_rules(self, complex_definitions: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Analyze complex rule definitions"""
        if debug:
            print(f"\n🔍 [DEBUG] Starting analysis of complex rule definitions")
            
        analysis_results = {
            "total_rules": len(complex_definitions),
            "rule_analyses": [],
            "complexity_summary": {
                "simple": 0,
                "moderate": 0, 
                "complex": 0
            },
            "missing_components": [],
            "rule_validation_issues": []
        }
        
        for rule_def in complex_definitions:
            equivalent_class = rule_def.get('equivalent_class', '')
            definition = rule_def.get('definition', '')
            rule_complexity = rule_def.get('rule_complexity', {})
            component_validations = rule_def.get('component_validations', [])
            
            if debug:
                print(f"\n📋 [DEBUG] Analyzing rule: {equivalent_class} ≡ {definition}")
                print(f"🔧 [DEBUG] Complexity: {rule_complexity.get('level', 'unknown')} (score: {rule_complexity.get('score', 0)})")
            
            # Count complexity
            complexity_level = rule_complexity.get('level', 'simple')
            if complexity_level in analysis_results["complexity_summary"]:
                analysis_results["complexity_summary"][complexity_level] += 1
            
            # Analyze missing components
            missing_components = []
            validation_issues = []
            
            for comp_val in component_validations:
                component = comp_val.get('component', '')
                status = comp_val.get('status', '')
                comp_type = comp_val.get('type', 'unknown')
                
                if status == 'not_found':
                    missing_components.append({
                        "component": component,
                        "type": comp_type,
                        "context": f"In definition of rule {equivalent_class}"
                    })
                elif status == 'similar_found':
                    validation_issues.append({
                        "component": component,
                        "issue": "Similar items exist but no exact match",
                        "similar_classes": comp_val.get('similar_classes', []),
                        "similar_properties": comp_val.get('similar_properties', [])
                    })
            
            # If there are missing components, use LLM to analyze placement suggestions
            rule_placement_analysis = None
            if missing_components and equivalent_class:
                try:
                    if debug:
                        print(f"🤖 [DEBUG] Performing LLM analysis on rule {equivalent_class}")
                    rule_placement_analysis = self._get_llm_rule_placement_recommendation(
                        equivalent_class, definition, missing_components, debug
                    )
                except Exception as e:
                    if debug:
                        print(f"❌ [DEBUG] LLM rule analysis failed: {e}")
                    validation_issues.append({
                        "component": equivalent_class,
                        "issue": f"LLM analysis failed: {e}",
                        "error": str(e)
                    })
            
            rule_analysis = {
                "equivalent_class": equivalent_class,
                "definition": definition,
                "complexity": rule_complexity,
                "missing_components": missing_components,
                "validation_issues": validation_issues,
                "llm_placement_analysis": rule_placement_analysis,
                "is_complete": len(missing_components) == 0 and len(validation_issues) == 0
            }
            
            analysis_results["rule_analyses"].append(rule_analysis)
            analysis_results["missing_components"].extend(missing_components)
            analysis_results["rule_validation_issues"].extend(validation_issues)
        
        return analysis_results
    
    def _generate_rule_safety_attributes(self, complex_definitions: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Dict[str, Any]]:
        """Generate safety attributes for complex rules"""
        safety_attributes = {
            "total_rules": len(complex_definitions),
            "rule_safety_attributes": {}
        }
        
        for rule_def in complex_definitions:
            if debug:
                print(f"📋 [DEBUG] Rule definition raw data: {rule_def}")
            
            original_rule_name = rule_def.get('equivalent_class', 'UnknownRule')  # Use correct field name
            manchester_definition = rule_def.get('definition', '')  # Use correct field name
            
            if debug:
                print(f"🔍 [DEBUG] Extracted fields:")
                print(f"  original_rule_name: '{original_rule_name}'")
                print(f"  manchester_definition: '{manchester_definition}'")
            
            # Use LLM to generate more meaningful rule names
            improved_rule_name = self._generate_improved_rule_name(manchester_definition, debug)
            rule_name = improved_rule_name if improved_rule_name else original_rule_name
            
            if debug:
                print(f"\n⚠️ [DEBUG] Generating safety attributes for rule {rule_name}")
            
            try:
                # Call LLM to generate safety attributes
                safety_attrs = self._get_llm_safety_attributes(rule_name, manchester_definition, debug)
                
                safety_attributes["rule_safety_attributes"][rule_name] = {
                    "original_rule_name": original_rule_name,
                    "improved_rule_name": rule_name,
                    "rule_definition": manchester_definition,
                    "safety_attributes": safety_attrs,
                    "generation_status": safety_attrs.get('status', 'unknown')
                }
                
            except Exception as e:
                if debug:
                    print(f"❌ [DEBUG] Safety attribute generation failed: {e}")
                safety_attributes["rule_safety_attributes"][rule_name] = {
                    "original_rule_name": original_rule_name,
                    "improved_rule_name": rule_name,
                    "rule_definition": manchester_definition,
                    "safety_attributes": {
                        "status": "failed",
                        "error": str(e)
                    },
                    "generation_status": "failed"
                }
        
        return safety_attributes
    
    def _generate_improved_rule_name(self, manchester_definition: str, debug: bool = False) -> Optional[str]:
        """Use LLM to generate more meaningful rule names"""
        try:
            if debug:
                print(f"🏷️ [DEBUG] Calling LLM to generate improved rule name")
                print(f"🔤 [DEBUG] Manchester definition: {manchester_definition}")
            
            # Prepare prompt data
            prompt_data = {
                'manchester_definition': manchester_definition,
                'context': 'kitchen_safety'
            }
            
            # Serialize prompt_data to avoid Path objects
            def serialize_data(data):
                from pathlib import Path
                if isinstance(data, (Path, type(Path()))):
                    return str(data)
                elif hasattr(data, '__fspath__'):
                    return str(data)
                elif isinstance(data, dict):
                    return {k: serialize_data(v) for k, v in data.items()}
                elif isinstance(data, (list, tuple)):
                    return [serialize_data(item) for item in data]
                else:
                    return data
            
            # Call LLM to generate rule name
            response = call_llm('rule_naming', **serialize_data(prompt_data))
            
            if debug:
                print(f"📝 [DEBUG] LLM generated rule name: {response}")
            
            # Simple parsing to extract rule name
            import re
            # Look for patterns like "RuleName:" or "suggested rule name:" 
            name_match = re.search(r'(?:Rule\s*Name|Suggested.*Rule.*Name)[:：]\s*([A-Za-z][A-Za-z0-9_]*)', response, re.IGNORECASE)
            if name_match:
                return name_match.group(1)
            
            # If no formatted name found, try to extract the first English word
            word_match = re.search(r'\b([A-Z][a-zA-Z0-9_]{2,})\b', response)
            if word_match:
                return word_match.group(1)
                
            return None
            
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Rule name generation failed: {e}")
            return None
    
    def _get_llm_safety_attributes(self, rule_name: str, rule_definition: str, debug: bool = False) -> Dict[str, Any]:
        """Use LLM to generate safety attributes for rules"""
        try:
            if debug:
                print(f"🤖 [DEBUG] Calling LLM to generate safety attributes for rule {rule_name}")
            
            # Prepare prompt data - using danger_safety_analysis template defined in prompts.py
            prompt_data = {
                'danger_name': rule_name,
                'danger_definition': rule_definition
            }
            
            # Serialize all Path objects in prompt_data
            def serialize_prompt_data(data):
                """Ensure there are no Path objects in prompt_data"""
                from pathlib import Path
                if isinstance(data, (Path, type(Path()))):
                    return str(data)
                elif hasattr(data, '__fspath__'):
                    return str(data)
                elif isinstance(data, dict):
                    return {k: serialize_prompt_data(v) for k, v in data.items()}
                elif isinstance(data, (list, tuple)):
                    return [serialize_prompt_data(item) for item in data]
                else:
                    return data
            
            serialized_prompt_data = serialize_prompt_data(prompt_data)
            
            if debug:
                print(f"🔤 [DEBUG] Prompt parameters:")
                print(f"  rule_name: {rule_name}")
                print(f"  rule_definition: {rule_definition}")
                
            
            # Call LLM
            response = call_llm('danger_safety_analysis', **serialized_prompt_data)
            
            if debug:
                print(f"📝 [DEBUG] LLM response: {response[:200]}...")
            
            # Parse LLM response
            parsed_result = self._parse_safety_attributes_response(response)
            
            return parsed_result
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'danger_level': 2,  # Default medium risk
                'safety_warning': 'Please pay attention to safety operations',
                'trigger_reason': 'Potential safety risk'
            }
    
    def _parse_safety_attributes_response(self, response: str) -> Dict[str, Any]:
        """Parse safety attributes LLM response"""
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                
                try:
                    parsed = json.loads(json_str)
                    
                    if not isinstance(parsed, dict):
                        raise ValueError(f"Parsed result is not a dictionary: {type(parsed)}")
                    
                    return {
                        'status': 'success',
                        'danger_level': parsed.get('danger_level', 2),
                        'safety_warning': parsed.get('safety_warning', 'Please pay attention to safety operations'),
                        'trigger_reason': parsed.get('trigger_reason', 'Potential safety risk'),
                        'confidence': parsed.get('confidence', 0.8),
                        'reasoning': parsed.get('reasoning', '')
                    }
                except json.JSONDecodeError:
                    pass
            
            # Simple text parsing fallback
            return {
                'status': 'partial',
                'reasoning': response,
                'danger_level': 2,
                'safety_warning': 'Please pay attention to safety operations',
                'trigger_reason': 'Potential safety risk',
                'confidence': 0.6
            }
                
        except Exception as e:
            return {
                'status': 'parse_failed',
                'error': str(e),
                'raw_response': response,
                'danger_level': 2,
                'safety_warning': 'Please pay attention to safety operations',
                'trigger_reason': 'Potential safety risk'
            }
    
    def _generate_danger_safety_attributes(self, danger_name: str, original_definition: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
        """Generate safety attributes for danger classes (danger level, safety warning, trigger reason)"""
        try:
            if debug:
                print(f"🤖 [DEBUG] Generating safety attributes for danger '{danger_name}'")
            
            # Extract danger definition information
            danger_class = original_definition.get('class', danger_name)
            subclass_of = original_definition.get('subclassOf', 'HazardousSituation')
            
            # Build context information
            context = f"Kitchen safety context: {danger_name} is a type of {subclass_of}"
            
            # Prepare LLM prompt data
            prompt_data = {
                'danger_name': danger_name,
                'danger_definition': f"{danger_class} subClassOf {subclass_of}",
                'context': context
            }
            
            if debug:
                print(f"📝 [DEBUG] LLM prompt data:")
                print(f"  danger_name: {danger_name}")
                print(f"  danger_definition: {prompt_data['danger_definition']}")
                print(f"  context: {context}")
            
            # Serialize prompt_data to avoid Path objects
            def serialize_data(data):
                from pathlib import Path
                if isinstance(data, (Path, type(Path()))):
                    return str(data)
                elif hasattr(data, '__fspath__'):
                    return str(data)
                elif isinstance(data, dict):
                    return {k: serialize_data(v) for k, v in data.items()}
                elif isinstance(data, (list, tuple)):
                    return [serialize_data(item) for item in data]
                else:
                    return data
            
            # Call LLM
            response = call_llm('danger_safety_analysis', **serialize_data(prompt_data))
            
            if debug:
                print(f"📝 [DEBUG] LLM response: {response[:200]}...")
                
            # Parse LLM response
            return self._parse_danger_safety_response(response, debug)
            
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Danger safety attribute generation failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'danger_level': 3,
                'safety_warning': f'Detected {danger_name} situation, please pay attention to safety!',
                'trigger_reason': f'{danger_name} safety risk'
            }
    
    def _parse_danger_safety_response(self, response: str, debug: bool = False) -> Dict[str, Any]:
        """Parse LLM-generated danger safety attribute response"""
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                
                try:
                    parsed = json.loads(json_str)
                    
                    if not isinstance(parsed, dict):
                        raise ValueError(f"Parsed result is not a dictionary: {type(parsed)}")
                    
                    # Validate required fields and return
                    return {
                        'status': 'success',
                        'danger_level': parsed.get('danger_level', 3),
                        'safety_warning': parsed.get('safety_warning', 'Please pay attention to safety'),
                        'trigger_reason': parsed.get('trigger_reason', 'Potential safety risk'),
                        'confidence': parsed.get('confidence', 0.8),
                        'reasoning': parsed.get('reasoning', '')
                    }
                except json.JSONDecodeError:
                    pass
            
            # Simple text parsing fallback
            danger_level = 3
            safety_warning = "Please pay attention to safety operations"
            trigger_reason = "Potential safety risk"
            
            # Try to extract numbers from text as danger level
            import re
            level_match = re.search(r'danger[_\s]*level[:\s]*(\d+)', response, re.IGNORECASE)
            if level_match:
                danger_level = min(max(int(level_match.group(1)), 1), 4)
                
            # Try to extract warning information
            warning_patterns = [
                r'warning[:\s]*["\']([^"\']+)["\']',
                r'safety[_\s]*warning[:\s]*["\']([^"\']+)["\']'
            ]
            for pattern in warning_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    safety_warning = match.group(1)
                    break
            
            return {
                'status': 'text_parsed',
                'danger_level': danger_level,
                'safety_warning': safety_warning,
                'trigger_reason': trigger_reason,
                'confidence': 0.6,
                'reasoning': 'Parsed from text response due to JSON parsing failure'
            }
            
        except Exception as e:
            return {
                'status': 'parse_failed',
                'error': str(e),
                'raw_response': response,
                'danger_level': 3,
                'safety_warning': 'Please pay attention to safety operations',
                'trigger_reason': 'Potential safety risk'
            }
    
    def _analyze_category_items(self, category: str, items: List[Dict[str, Any]], debug: bool = False) -> Optional[Dict[str, Any]]:
        """Analyze missing items under a category"""
        # Special handling for danger category - all dangers inherit from DangerousSituation, but need LLM-generated safety attributes
        if category == 'dangers':
            if debug:
                print(f"⚠️ [DEBUG] Danger category handling: inherit from DangerousSituation and generate safety attributes")
            
            items_analysis = []
            for item in items:
                danger_name = item.get('name', '')
                original_definition = item.get('original_definition', {})
                
                # Generate danger safety attributes
                safety_attrs = self._generate_danger_safety_attributes(
                    danger_name, original_definition, debug
                )
                
                item_analysis = {
                    "name": danger_name,
                    "status": "missing",
                    "recommended_parent": "DangerousSituation",
                    "confidence": 1.0,
                    "reasoning": "All danger classes inherit from DangerousSituation",
                    "original_definition": original_definition,
                    "safety_attributes": safety_attrs  # Add LLM-generated safety attributes
                }
                items_analysis.append(item_analysis)
                
                if debug:
                    print(f"  ✓ [DEBUG] Processing danger: {danger_name}")
                    if safety_attrs.get('status') == 'success':
                        print(f"    - Danger level: {safety_attrs.get('danger_level')}")
                        print(f"    - Safety warning: {safety_attrs.get('safety_warning')}")
                        print(f"    - Trigger reason: {safety_attrs.get('trigger_reason')}")
                    else:
                        print(f"    - Generation failed: {safety_attrs.get('error')}")
            
            return {
                "category": category,
                "total_items": len(items),
                "analysis_method": "fixed_hierarchy_with_llm_attributes",
                "parent_class": "DangerousSituation",
                "items_analysis": items_analysis
            }
        
        # Map plural forms to singular forms
        category_mapping = {
            'objects': 'object',
            'materials': 'material', 
            'attributes': 'attribute',
            'states': 'state',
            'actions': 'action',
            'agents': 'agent',
            'dangers': 'danger'
        }
        
        # Get corresponding hierarchy structure
        mapped_category = category_mapping.get(category, category)
        hierarchy = self.hierarchies.get(mapped_category)
        if not hierarchy:
            print(f"⚠️ Not found {category} (mapped to {mapped_category}) hierarchy structure")
            return None
            
        print(f"📊 {category.upper()} hierarchy contains {len(hierarchy['classes'])} classes")
        
        # Analyze placement position for each missing item
        items_analysis = []
        
        for item in items:
            if debug:
                print(f"\n🔍 [DEBUG] Processing item: {type(item)}, content: {item}")
            
            # Ensure item is dictionary type
            if isinstance(item, str):
                print(f"⚠️ [DEBUG] Found string type item: {item}")
                continue
            elif not isinstance(item, dict):
                print(f"⚠️ [DEBUG] Found non-dictionary type item: {type(item)}")
                continue
                
            item_name = item.get('name', '')
            original_def = item.get('original_definition', {})
            
            if debug:
                print(f"\n🔍 [DEBUG] Analyzing item: {item_name}")
                
            # Call LLManalyze placement position
            placement_recommendation = self._get_llm_placement_recommendation(
                item_name, original_def, hierarchy, debug
            )
            
            items_analysis.append({
                'name': item_name,
                'original_definition': original_def,
                'placement_recommendation': placement_recommendation
            })
            
        return {
            'category': category,
            'hierarchy_summary': self.extractor.get_hierarchy_summary(hierarchy),
            'items_count': len(items),
            'items_analysis': items_analysis
        }
    
    def _get_llm_placement_recommendation(self, item_name: str, original_def: Dict[str, Any], 
                                        hierarchy: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
        """Use LLM to analyze the optimal placement position for items"""
        try:
            # Format hierarchy structure for LLM readable text
            hierarchy_text = self.extractor.format_tree_for_llm(hierarchy, max_depth=3)
            
            # Build LLM prompt
            prompt_data = {
                'item_name': item_name,
                'item_definition': original_def,
                'category': hierarchy['category'],
                'hierarchy_structure': hierarchy_text,
                'total_classes': len(hierarchy['classes'])
            }
            
            if debug:
                print(f"🤖 [DEBUG] Calling LLM to analyze {item_name} placement position")
                print(f"🔤 [DEBUG] Prompt parameters:")
                for key, value in prompt_data.items():
                    if key == 'hierarchy_structure':
                        print(f"  {key}: {str(value)[:200]}...")
                    else:
                        print(f"  {key}: {value}")
                
            # Serialize prompt_data to avoid Path objects
            def serialize_data(data):
                from pathlib import Path
                if isinstance(data, (Path, type(Path()))):
                    return str(data)
                elif hasattr(data, '__fspath__'):
                    return str(data)
                elif isinstance(data, dict):
                    return {k: serialize_data(v) for k, v in data.items()}
                elif isinstance(data, (list, tuple)):
                    return [serialize_data(item) for item in data]
                else:
                    return data
            
            # Call LLM
            response = call_llm('hierarchy_placement_analysis', **serialize_data(prompt_data))
            
            if debug:
                print(f"📝 [DEBUG] LLM response: {response[:200]}...")
                
            # Parse LLM response
            parsed_result = self._parse_llm_response(response, hierarchy)
            
            # Validate if recommended parent class exists, if not then recursively analyze
            if parsed_result:
                parsed_result = self._validate_and_build_inheritance_chain(
                    parsed_result, hierarchy, debug, item_name
                )
            
            return parsed_result
        
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'recommended_parent': None,
                'confidence': 0.0
            }
    
    def _parse_llm_response(self, response: str, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                
                return {
                    'status': 'success',
                    'recommended_parent': parsed.get('recommended_parent'),
                    'recommended_parent_uri': parsed.get('recommended_parent_uri'),
                    'confidence': parsed.get('confidence', 0.8),
                    'reasoning': parsed.get('reasoning', ''),
                    'alternative_parents': parsed.get('alternative_parents', []),
                    'new_class_definition': parsed.get('new_class_definition', {}),
                    'potential_conflicts': parsed.get('potential_conflicts', [])
                }
            else:
                # Simple text parsing
                return {
                    'status': 'partial',
                    'reasoning': response,
                    'confidence': 0.6
                }
                
        except Exception as e:
            print(f"❌ Failed to parse LLM response: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'recommended_parent': None,
                'confidence': 0.0
            }
    
    def _analyze_missing_parent(self, parent_name: str, hierarchy: Dict[str, Any], debug: bool = False) -> Optional[Dict[str, Any]]:
        """Analyze where missing parent class should be placed"""
        try:
            if debug:
                print(f"🔍 [DEBUG] Recursively analyzing missing parent class: {parent_name}")
            
            # Create definition for missing parent class
            parent_definition = f"A class representing {parent_name} in the {hierarchy['category']} domain"
            
            # Build hierarchy structure text
            hierarchy_text = self.extractor.format_hierarchy_for_llm(hierarchy)
            
            prompt_data = {
                'item_name': parent_name,
                'item_definition': parent_definition,
                'category': hierarchy['category'],
                'hierarchy_structure': hierarchy_text,
                'total_classes': len(hierarchy['classes'])
            }
            
            if debug:
                print(f"🤖 [DEBUG] Calling LLM analysis for missing parent class {parent_name}")
                
            # Serialize prompt_data to avoid Path objects
            def serialize_data(data):
                from pathlib import Path
                if isinstance(data, (Path, type(Path()))):
                    return str(data)
                elif hasattr(data, '__fspath__'):
                    return str(data)
                elif isinstance(data, dict):
                    return {k: serialize_data(v) for k, v in data.items()}
                elif isinstance(data, (list, tuple)):
                    return [serialize_data(item) for item in data]
                else:
                    return data
            
            # Call LLM
            response = call_llm('hierarchy_placement_analysis', **serialize_data(prompt_data))
            
            # Parse response
            parent_result = self._parse_llm_response(response, hierarchy)
            
            if parent_result:
                # Recursively validate parent class's parent
                parent_result = self._validate_and_build_inheritance_chain(parent_result, hierarchy, debug)
                
            return parent_result
            
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Analysis of missing parent class failed: {e}")
            return None
    
    def _find_path_to_root(self, class_name: str, hierarchy: Dict[str, Any]) -> List[str]:
        """Find path from root class to specified class"""
        # Build parent-child relationship mapping
        class_map = {cls['name']: cls for cls in hierarchy['classes']}
        
        if class_name not in class_map:
            return [class_name]
        
        path = []
        current = class_name
        visited = set()
        
        while current and current not in visited:
            visited.add(current)
            path.insert(0, current)  # Insert at beginning
            
            current_class = class_map.get(current)
            if not current_class:
                break
                
            # Get parent classes
            parents = current_class.get('parents', [])
            if not parents:
                break
            
            # Select first non-external parent class
            next_parent = None
            for parent in parents:
                if parent in class_map:
                    next_parent = parent
                    break
            
            current = next_parent
        
        return path
    
    def _validate_and_build_inheritance_chain(self, parsed_result: Dict[str, Any], hierarchy: Dict[str, Any], debug: bool = False, item_name: str = None) -> Dict[str, Any]:
        """Validate recommended parent class and build complete inheritance chain"""
        # Type checking
        if not isinstance(parsed_result, dict):
            return {
                'status': 'failed',
                'error': f'parsed_result is not a dict: {type(parsed_result)}',
                'raw_result': parsed_result
            }
        
        recommended_parent = parsed_result.get('recommended_parent')
        if not recommended_parent:
            return parsed_result
        
        # Check if recommended parent class exists in current ontology
        classes = hierarchy.get('classes', [])
        
        # Handle different data structures
        if isinstance(classes, dict):
            # If dictionary, extract all keys as class names
            existing_classes = list(classes.keys())
        elif isinstance(classes, list):
            if classes and isinstance(classes[0], dict):
                # If dictionary list, extract name field
                existing_classes = [cls.get('name', '') for cls in classes]
            else:
                # If string list, use directly
                existing_classes = classes
        else:
            existing_classes = []
        
        parent_exists = recommended_parent in existing_classes
        
        if debug:
            print(f"🔍 [DEBUG] Validating if parent class '{recommended_parent}' exists in {hierarchy['category']} ontology: {'✅' if parent_exists else '❌'}")
        
        # Build inheritance chain
        if parent_exists:
            # Parent exists, build path from root class to parent class
            parent_path = self._find_path_to_root(recommended_parent, hierarchy)
            inheritance_chain = parent_path
            if debug:
                print(f"✅ [DEBUG] Found path from root class to parent: {' → '.join(inheritance_chain)}")
        else:
            # Parent doesn't exist, can only start from recommended parent
            inheritance_chain = [recommended_parent]
            if debug:
                print(f"⚠️ [DEBUG] Parent class '{recommended_parent}' does not exist, needs to be created in ontology")
        
        # Add new class to inheritance chain
        new_class_name = item_name if item_name else 'NewClass'
        inheritance_chain.append(new_class_name)
        
        # Update result
        parsed_result.update({
            'parent_exists_in_ontology': parent_exists,
            'inheritance_chain': inheritance_chain,
            'chain_display': ' → '.join(inheritance_chain)
        })
        
        if debug:
            print(f"🌳 [DEBUG] Complete inheritance chain: {parsed_result['chain_display']}")
        
        return parsed_result
    
    def _load_validation_report(self, validation_report_path: str) -> Dict[str, Any]:
        """Load validation report file"""
        try:
            with open(validation_report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check data format, may need to extract validation_report field
            if 'validation_report' in data:
                return data['validation_report']
            else:
                return data
                
        except Exception as e:
            print(f"❌ Failed to load validation report: {e}")
            raise
    
    def _parse_llm_response(self, response: str, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                
                try:
                    parsed = json.loads(json_str)
                    
                    # Ensure parsed is dictionary type
                    if not isinstance(parsed, dict):
                        raise ValueError(f"Parsed result is not a dictionary: {type(parsed)}")
                    
                    return {
                        'status': 'success',
                        'recommended_parent': parsed.get('recommended_parent'),
                        'recommended_parent_uri': parsed.get('recommended_parent_uri'),
                        'parent_exists_in_ontology': parsed.get('parent_exists_in_ontology', False),
                        'confidence': parsed.get('confidence', 0.8),
                        'reasoning': parsed.get('reasoning', ''),
                        'inheritance_chain': parsed.get('inheritance_chain', []),
                        'alternative_parents': parsed.get('alternative_parents', []),
                        'new_class_definition': parsed.get('new_class_definition', {}),
                        'potential_conflicts': parsed.get('potential_conflicts', [])
                    }
                except json.JSONDecodeError as je:
                    raise je
            else:
                # Simple text parsing
                return {
                    'status': 'partial',
                    'reasoning': response,
                    'confidence': 0.6
                }
                
        except Exception as e:
            return {
                'status': 'parse_failed',
                'error': str(e),
                'raw_response': response
            }
    
    def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis result summary"""
        total_items = 0
        successful_analyses = 0
        categories_summary = {}
        
        for category, category_data in analysis_results.items():
            items_count = category_data.get('items_count', 0)
            total_items += items_count
            
            # Count successfully analyzed items
            successful_count = sum(
                1 for item in category_data.get('items_analysis', [])
                if item.get('placement_recommendation', {}).get('status') == 'success'
            )
            successful_analyses += successful_count
            
            categories_summary[category] = {
                'items_count': items_count,
                'successful_analyses': successful_count,
                'success_rate': successful_count / items_count if items_count > 0 else 0.0
            }
        
        return {
            'total_items_analyzed': total_items,
            'successful_analyses': successful_analyses,
            'overall_success_rate': successful_analyses / total_items if total_items > 0 else 0.0,
            'categories_summary': categories_summary
        }


def test_hierarchy_analyzer():
    """Test hierarchy analyzer"""
    analyzer = HierarchyAnalyzer()
    analyzer.initialize_hierarchies()
    
    # Mock validation report
    mock_validation_report = {
        "validation_results": {
            "objects_validation": {
                "missing_items": [
                    {
                        "name": "SharpUtensil",
                        "status": "not_found",
                        "original_definition": {
                            "class": "SharpUtensil",
                            "subClassOf": ["Utensil", "SharpObject"]
                        }
                    }
                ]
            },
            "materials_validation": {
                "missing_items": [
                    {
                        "name": "Steel",
                        "status": "not_found", 
                        "original_definition": {
                            "class": "Steel",
                            "subClassOf": ["Metal"]
                        }
                    }
                ]
            }
        }
    }
    
    print("🧪 Testing hierarchy analyzer...")
    result = analyzer.analyze_missing_items(mock_validation_report, debug=True)
    
    print(f"\n📊 Analysis result summary:")
    print(f"- Total items: {result['total_missing_items']}")
    print(f"- Analysis categories: {result['categories_analyzed']}")
    print(f"- Success rate: {result['summary']['overall_success_rate']:.2%}")


if __name__ == "__main__":
    test_hierarchy_analyzer()
