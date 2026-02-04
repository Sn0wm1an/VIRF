#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manchester JSON vectorization validator
Performs ontological matching validation on generated Manchester syntax JSON
"""

import json
import pickle
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime

# Add project root directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


class ManchesterJSONValidator:
    """Manchester JSON vectorization validator"""
    
    def __init__(self):
        """Initialize validator"""
        self.vector_data = self._load_vector_data()
        self.similarity_threshold = 0.7  # Similarity threshold
        
    def validate_manchester_json(self, manchester_json: str, debug: bool = False) -> Dict[str, Any]:
        """
        Validate the structure and content of Manchester JSON
        
        Args:
            manchester_json: Manchester syntax JSON string
            debug: Whether to enable debug mode, showing detailed vector matching information
            
        Returns:
            Validation result report
        """
        try:
            json_data = json.loads(manchester_json)
            print(f"🔍 Starting validation of Manchester JSON structure")
            
            if debug:
                print(f"🔧 Debug mode enabled")
                print(f"🎯 Similarity threshold: {self.similarity_threshold}")
                print(f"📊 Loaded vector data: {len(self.vector_data.get('class_vectors', {}))} classes, {len(self.vector_data.get('property_vectors', {}))} properties")
            
            # Validate each section
            objects_validation = self._validate_objects(json_data.get('objects', []), debug)
            materials_validation = self._validate_materials(json_data.get('materials', []), debug)
            attributes_validation = self._validate_attributes(json_data.get('attributes', []), debug)
            states_validation = self._validate_states(json_data.get('states', []), debug)
            dangers_validation = self._validate_dangers(json_data.get('dangers', []), debug)
            spatial_relations_validation = self._validate_spatial_relations(json_data.get('spatialRelations', []), debug)
            attribute_relations_validation = self._validate_attribute_relations(json_data.get('attributeRelations', []), debug)
            property_chains_validation = self._validate_property_chains(json_data.get('propertyChains', []), debug)
            
            # Summarize validation results
            validation_report = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "validation_version": "1.0",
                    "total_items_checked": (
                        len(json_data.get('objects', [])) +
                        len(json_data.get('materials', [])) +
                        len(json_data.get('attributes', [])) +
                        len(json_data.get('states', [])) +
                        len(json_data.get('dangers', [])) +
                        len(json_data.get('spatialRelations', [])) +
                        len(json_data.get('attributeRelations', []))
                    )
                },
                "validations": {
                    "objects": objects_validation,
                    "materials": materials_validation,
                    "attributes": attributes_validation,
                    "states": states_validation,
                    "dangers": dangers_validation,
                    "spatial_relations": spatial_relations_validation,
                    "attribute_relations": attribute_relations_validation,
                    "property_chains": property_chains_validation
                },
                "summary": self._generate_validation_summary([
                    objects_validation, materials_validation, attributes_validation,
                    states_validation, dangers_validation, spatial_relations_validation,
                    attribute_relations_validation, property_chains_validation
                ]),
                "recommendations": self._generate_recommendations([
                    objects_validation, materials_validation, attributes_validation,
                    states_validation, dangers_validation, spatial_relations_validation,
                    attribute_relations_validation, property_chains_validation
                ])
            }
            
            self._print_validation_summary(validation_report)
            return validation_report
            
        except json.JSONDecodeError as e:
            return self._create_error_report(f"JSON parsing failed: {e}")
        except Exception as e:
            return self._create_error_report(f"Validation process error: {e}")
    
    def _validate_objects(self, objects: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate object classes - match only in object.owl namespace"""
        if debug:
            print(f"\n🔍 [DEBUG] Starting validation of Objects: {len(objects)} items")
            
        results = {
            "total_items": len(objects),
            "existing_items": [],
            "missing_items": [],
            "similar_items": [],
            "validation_details": []
        }
        
        for obj in objects:
            class_name = obj.get('class', '')
            if not class_name:
                continue
                
            if debug:
                print(f"\n📋 [DEBUG] Validating object: {class_name}")
                
            # Check exact match - restricted to object namespace
            exact_match = self._find_exact_match_by_namespace(class_name, 'object')
            if exact_match:
                if debug:
                    print(f"✅ [DEBUG] Exact match: {class_name} -> {exact_match}")
                results["existing_items"].append({
                    "name": class_name,
                    "match": exact_match,
                    "status": "exact_match"
                })
            else:
                # Check similar match - restricted to object namespace
                if debug:
                    print(f"❌ [DEBUG] No exact match, starting similarity calculation...")
                    print(f"🎯 [DEBUG] Similarity threshold: {self.similarity_threshold}")
                    print(f"🏷️ [DEBUG] Restrict search scope: object namespace")
                similar_matches = self._find_similar_matches_by_namespace(class_name, 'object', debug)
                if similar_matches:
                    if debug:
                        print(f"⚠️ [DEBUG] Found {len(similar_matches)} similar items, highest similarity: {similar_matches[0]['similarity']:.3f}")
                    results["similar_items"].append({
                        "name": class_name,
                        "similar_matches": similar_matches[:3],  # Limit return count
                        "status": "similar_found",
                        "original_definition": obj  # Save original LLM definition
                    })
                else:
                    if debug:
                        print(f"❌ [DEBUG] No similar items meeting threshold, listed as missing items")
                    results["missing_items"].append({
                        "name": class_name,
                        "status": "not_found",
                        "recommendation": "Need to add this class in object ontology",
                        "original_definition": obj  # Save original LLM definition
                    })
        
        return results
    
    def _validate_materials(self, materials: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate material classes - only match within material.owl namespace"""
        return self._validate_generic_category_by_namespace(materials, 'materials', 'material', 'material', debug)
    
    def _validate_attributes(self, attributes: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate attribute classes - only match within attribute.owl namespace"""
        return self._validate_generic_category_by_namespace(attributes, 'attributes', 'attribute', 'attribute', debug)
    
    def _validate_states(self, states: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate state classes - only match within state.owl namespace"""
        return self._validate_generic_category_by_namespace(states, 'states', 'state', 'state', debug)
    
    def _validate_dangers(self, dangers: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate danger classes"""
        return self._validate_generic_category(dangers, 'dangers', 'danger', debug)
    
    def _validate_spatial_relations(self, spatial_relations: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate spatial relations"""
        return self._validate_relations(spatial_relations, 'spatial_relations', debug)
    
    def _validate_attribute_relations(self, attribute_relations: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate attribute relations"""
        return self._validate_relations(attribute_relations, 'attribute_relations', debug)
    
    def _validate_property_chains(self, property_chains: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
        """Validate property chains and equivalent class definitions"""
        results = {
            "total_items": len(property_chains),
            "existing_items": [],
            "missing_items": [],
            "complex_definitions": []
        }
        
        for chain in property_chains:
            equivalent_class = chain.get('equivalentClass', '')
            definition = chain.get('definition', '')
            
            # Parse classes and properties in definition
            if definition:
                parsed_components = self._parse_manchester_definition(definition)
                validation_result = {
                    "equivalent_class": equivalent_class,
                    "definition": definition,
                    "parsed_components": parsed_components,
                    "component_validations": []
                }
                
                # Validate each component
                for component in parsed_components:
                    comp_validation = self._validate_component(component)
                    validation_result["component_validations"].append(comp_validation)
                
                results["complex_definitions"].append(validation_result)
        
        return results
    
    def _validate_generic_category(self, items: List[Dict[str, Any]], category_name: str, category_type: str, debug: bool = False) -> Dict[str, Any]:
        """Generic category validation"""
        if debug:
            print(f"\n🔍 [DEBUG] Starting validation of{category_name}: {len(items)} items")
            
        results = {
            "total_items": len(items),
            "existing_items": [],
            "missing_items": [],
            "similar_items": []
        }
        
        for item in items:
            item_name = item.get('class', '') or item.get('name', '')
            if not item_name:
                continue
                
            if debug:
                print(f"\n📋 [DEBUG] Validating {category_type}: {item_name}")
                
            # Check exact match
            exact_match = self._find_exact_match(item_name, 'classes')
            if exact_match:
                if debug:
                    print(f"✅ [DEBUG] Exact match: {item_name} -> {exact_match}")
                results["existing_items"].append({
                    "name": item_name,
                    "match": exact_match,
                    "status": "exact_match"
                })
            else:
                # Check similar match
                if debug:
                    print(f"❌ [DEBUG] No exact match, starting similarity calculation...")
                    print(f"🎯 [DEBUG] Similarity threshold: {self.similarity_threshold}")
                similar_matches = self._find_similar_matches(item_name, 'classes', debug)
                if similar_matches:
                    if debug:
                        print(f"⚠️ [DEBUG] Found {len(similar_matches)} similar items, highest similarity: {similar_matches[0]['similarity']:.3f}")
                    results["similar_items"].append({
                        "name": item_name,
                        "similar_matches": similar_matches[:3],
                        "status": "similar_found",
                        "original_definition": item  # Save original LLM definition
                    })
                else:
                    if debug:
                        print(f"❌ [DEBUG] No similar items meeting threshold, listed as missing items")
                    results["missing_items"].append({
                        "name": item_name,
                        "status": "not_found",
                        "recommendation": f"Need to add in ontology{category_type}class this item",
                        "original_definition": item  # Save original LLM definition
                    })
        
        return results
    
    def _validate_generic_category_by_namespace(self, items: List[Dict[str, Any]], category_name: str, category_type: str, namespace: str, debug: bool = False) -> Dict[str, Any]:
        """Generic category validation by namespace"""
        if debug:
            print(f"\n🔍 [DEBUG] Starting validation of{category_name}: {len(items)} items (restricted to{namespace}namespace)")
            
        results = {
            "total_items": len(items),
            "existing_items": [],
            "missing_items": [],
            "similar_items": []
        }
        
        for item in items:
            item_name = item.get('class', '') or item.get('name', '')
            if not item_name:
                continue
                
            if debug:
                print(f"\n📋 [DEBUG] Validating {category_type}: {item_name}")
                
            # Check exact match - restricted to specified namespace
            exact_match = self._find_exact_match_by_namespace(item_name, namespace)
            if exact_match:
                if debug:
                    print(f"✅ [DEBUG] Exact match: {item_name} -> {exact_match}")
                results["existing_items"].append({
                    "name": item_name,
                    "match": exact_match,
                    "status": "exact_match"
                })
            else:
                # Check similar match - restricted to specified namespace
                if debug:
                    print(f"❌ [DEBUG] No exact match, starting similarity calculation...")
                    print(f"🎯 [DEBUG] Similarity threshold: {self.similarity_threshold}")
                    print(f"🏷️ [DEBUG] Restrict search scope: {namespace}namespace")
                similar_matches = self._find_similar_matches_by_namespace(item_name, namespace, debug)
                if similar_matches:
                    if debug:
                        print(f"⚠️ [DEBUG] Found {len(similar_matches)} similar items, highest similarity: {similar_matches[0]['similarity']:.3f}")
                    results["similar_items"].append({
                        "name": item_name,
                        "similar_matches": similar_matches[:3],
                        "status": "similar_found",
                        "original_definition": item  # Save original LLM definition
                    })
                else:
                    if debug:
                        print(f"❌ [DEBUG] No similar items meeting threshold, listed as missing items")
                    results["missing_items"].append({
                        "name": item_name,
                        "status": "not_found",
                        "recommendation": f"Need to add this {category_type} class in {namespace} ontology",
                        "original_definition": item  # Save original LLM definition
                    })
        
        return results
    
    def _validate_relations(self, relations: List[Dict[str, Any]], relation_type: str, debug: bool = False) -> Dict[str, Any]:
        """Validate relation properties"""
        results = {
            "total_items": len(relations),
            "existing_items": [],
            "missing_items": [],
            "similar_items": []
        }
        
        for relation in relations:
            prop_name = relation.get('objectProperty', '') or relation.get('property', '')
            if not prop_name:
                continue
                
            # Check exact match
            exact_match = self._find_exact_match(prop_name, 'properties')
            if exact_match:
                results["existing_items"].append({
                    "name": prop_name,
                    "match": exact_match,
                    "status": "exact_match"
                })
            else:
                # Check similar match
                similar_matches = self._find_similar_matches(prop_name, 'properties', debug)
                if similar_matches:
                    results["similar_items"].append({
                        "name": prop_name,
                        "similar_matches": similar_matches[:3],
                        "status": "similar_found"
                    })
                else:
                    results["missing_items"].append({
                        "name": prop_name,
                        "status": "not_found",
                        "recommendation": f"Need to add this property in ontology {relation_type}"
                    })
        
        return results
    
    def _parse_manchester_definition(self, definition: str) -> List[str]:
        """Parse components in Manchester syntax definition"""
        components = []
        
        # Simple parsing: extract class names and property names
        # More complex parsers can be used here, currently using simple string processing
        import re
        
        # Extract class names (words starting with uppercase)
        class_names = re.findall(r'\b[A-Z][a-zA-Z]*\b', definition)
        components.extend(class_names)
        
        # Extract property names (words starting with has/is)
        property_names = re.findall(r'\b(?:has|is)[A-Z][a-zA-Z]*\b', definition)
        components.extend(property_names)
        
        return list(set(components))  # Remove duplicates
    
    def _validate_component(self, component: str) -> Dict[str, Any]:
        """Validate single component"""
        # First check if it's a class
        class_match = self._find_exact_match(component, 'classes')
        if class_match:
            return {
                "component": component,
                "type": "class",
                "status": "found",
                "match": class_match
            }
        
        # Check if it's a property
        prop_match = self._find_exact_match(component, 'properties')
        if prop_match:
            return {
                "component": component,
                "type": "property",
                "status": "found",
                "match": prop_match
            }
        
        # Check similar match
        similar_classes = self._find_similar_matches(component, 'classes')
        similar_props = self._find_similar_matches(component, 'properties')
        
        if similar_classes or similar_props:
            return {
                "component": component,
                "type": "unknown",
                "status": "similar_found",
                "similar_classes": similar_classes[:2],
                "similar_properties": similar_props[:2]
            }
        
        return {
            "component": component,
            "type": "unknown",
            "status": "not_found",
            "recommendation": "Need to determine the type of this component and add it to the ontology"
        }
    
    def _find_exact_match(self, name: str, category: str) -> Dict[str, Any]:
        """Find exact match"""
        if category == 'classes':
            data_dict = self.vector_data.get('ontology_classes', {})
        else:
            data_dict = self.vector_data.get('relation_properties', {})
            
        for key, value in data_dict.items():
            item_name = value.get('name', '') or key.split('#')[-1] if '#' in key else key
            if item_name.lower() == name.lower():
                return {
                    "uri": key,
                    "name": item_name,
                    "label": value.get('label', ''),
                    "description": value.get('description', ''),
                    "namespace": value.get('namespace', '')
                }
        return None
    
    def _find_exact_match_by_namespace(self, name: str, namespace: str) -> Dict[str, Any]:
        """Find exact match by namespace"""
        data_dict = self.vector_data.get('ontology_classes', {})
        name_lower = name.lower()
        
        for key, value in data_dict.items():
            # Check namespace
            if not self._is_in_namespace(key, namespace):
                continue
                
            item_name = value.get('name', '') or key.split('#')[-1] if '#' in key else key
            if item_name.lower() == name_lower:
                return {
                    "uri": key,
                    "name": item_name,
                    "label": value.get('label', ''),
                    "description": value.get('description', ''),
                    "namespace": value.get('namespace', '')
                }
        return None
    
    def _find_similar_matches_by_namespace(self, name: str, namespace: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find similar matches by namespace"""
        if debug:
            print(f"🔍 [DEBUG] Starting similarity matching: {name} (namespace: {namespace})")
            
        data_dict = self.vector_data.get('ontology_classes', {})
        similar_matches = []
        name_lower = name.lower()
        
        total_checked = 0
        matches_found = 0
        all_scores = []  # Store all similarity calculation results
        
        for key, value in data_dict.items():
            # Check namespace
            if not self._is_in_namespace(key, namespace):
                continue
                
            item_name = value.get('name', '') or key.split('#')[-1] if '#' in key else key
            item_lower = item_name.lower()
            total_checked += 1
            
            # Calculate similarity
            similarity_score = self._calculate_similarity(name_lower, item_lower)
            is_substring_match = name_lower in item_lower or item_lower in name_lower
            
            # Collect all calculation results for debug display
            if debug:
                all_scores.append({
                    "name": item_name,
                    "similarity": similarity_score,
                    "is_substring": is_substring_match
                })
            
            # Check if it matches (only similarity above threshold counts as match)
            if similarity_score > self.similarity_threshold:
                matches_found += 1
                similar_matches.append({
                    "uri": key,
                    "name": item_name,
                    "label": value.get('label', ''),
                    "description": value.get('description', ''),
                    "namespace": value.get('namespace', ''),
                    "similarity": similarity_score
                })
        
        # Debug mode display top 5 items with highest similarity
        if debug:
            all_scores.sort(key=lambda x: x['similarity'], reverse=True)
            print(f"    📊 [DEBUG] Top 5 items with highest similarity (only {namespace} namespace):")
            for i, score_item in enumerate(all_scores[:5]):
                print(f"    🔸 [DEBUG] The top {i+1}: '{name}' vs '{score_item['name']}' -> Similarity: {score_item['similarity']:.3f}, Substring match: {score_item['is_substring']}")
        
        if debug:
            print(f"📊 [DEBUG] Similarity matching results: Checked {total_checked} items, found {matches_found} matches")
        
        # Sort by similarity
        similar_matches.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_matches
    
    def _is_in_namespace(self, uri: str, namespace: str) -> bool:
        """Check if URI belongs to specified namespace"""
        namespace_mappings = {
            'object': ['object#', 'core/object#'],
            'material': ['material#', 'core/material#'],
            'attribute': ['attribute#', 'core/attribute#'],
            'state': ['state#', 'core/state#'],
            'action': ['action#', 'core/action#', 'actions#'],
            'agent': ['agent#', 'core/agent#', 'agents#'],
            'danger': ['danger#', 'core/danger#'],
            'relation': ['relation#', 'core/relation#']
        }
        
        if namespace not in namespace_mappings:
            return True  # If namespace is undefined, allow all
            
        return any(ns in uri for ns in namespace_mappings[namespace])
    
    def _find_similar_matches(self, name: str, category: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find similar matches"""
        if debug:
            print(f"🔍 [DEBUG] Starting similarity matching: {name} (category: {category})")
            
        if category == 'classes':
            data_dict = self.vector_data.get('ontology_classes', {})
        else:
            data_dict = self.vector_data.get('relation_properties', {})
            
        similar_matches = []
        name_lower = name.lower()
        
        total_checked = 0
        matches_found = 0
        all_scores = []  # Store all similarity calculation results
        
        for key, value in data_dict.items():
            item_name = value.get('name', '') or key.split('#')[-1] if '#' in key else key
            item_lower = item_name.lower()
            total_checked += 1
            
            # Calculate similarity
            similarity_score = self._calculate_similarity(name_lower, item_lower)
            is_substring_match = name_lower in item_lower or item_lower in name_lower
            
            # Collect all calculation results for debug display
            if debug:
                all_scores.append({
                    "name": item_name,
                    "similarity": similarity_score,
                    "is_substring": is_substring_match
                })
            
            # Check if it matches (only similarity above threshold counts as match)
            if similarity_score > self.similarity_threshold:
                matches_found += 1
                similar_matches.append({
                    "uri": key,
                    "name": item_name,
                    "label": value.get('label', ''),
                    "description": value.get('description', ''),
                    "namespace": value.get('namespace', ''),
                    "similarity": similarity_score
                })
        
        # Debug mode display top 5 items with highest similarity
        if debug:
            all_scores.sort(key=lambda x: x['similarity'], reverse=True)
            print(f"    📊 [DEBUG] Top 5 items with highest similarity:")
            for i, score_item in enumerate(all_scores[:5]):
                print(f"    🔸 [DEBUG] The top {i+1}: '{name}' vs '{score_item['name']}' -> Similarity: {score_item['similarity']:.3f}, Substring match: {score_item['is_substring']}")
        
        if debug:
            print(f"📊 [DEBUG] Similarity matching results: Checked {total_checked} items, found {matches_found} matches")
        
        # Sort by similarity
        similar_matches.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_matches
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple string similarity"""
        if str1 == str2:
            return 1.0
        
        # Use simple inclusion relationship to calculate similarity
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # Calculate common character ratio
        common_chars = len(set(str1) & set(str2))
        total_chars = len(set(str1) | set(str2))
        return common_chars / total_chars if total_chars > 0 else 0.0
    
    def _load_vector_data(self) -> Dict[str, Any]:
        """Load vectorized data"""
        vector_data = {
            'ontology_classes': {},
            'relation_properties': {}
        }
        
        try:
            # Load vectorized data file
            vector_file = project_root / "vector" / "output" / "ontology_vectors.pkl"
            if vector_file.exists():
                with open(vector_file, 'rb') as f:
                    loaded_vectors = pickle.load(f)
                
                # Parse vector data
                for namespace, items in loaded_vectors.items():
                    for item_data in items:
                        item_uri = item_data.get('uri', '')
                        if item_uri:
                            if 'relation' in namespace.lower() or any(prop in item_data.get('name', '') 
                                                                    for prop in ['has', 'is', 'contains', 'near', 'above']):
                                vector_data['relation_properties'][item_uri] = item_data
                            else:
                                vector_data['ontology_classes'][item_uri] = item_data
                
                print(f"📚 Loaded ontology classes: {len(vector_data['ontology_classes'])} items")
                print(f"🔗 Loaded relation properties: {len(vector_data['relation_properties'])} items")
            else:
                print(f"⚠️ Vector file does not exist: {vector_file}")
                print("💡 Please run vector/run_incremental_vectorization.py first")
                
        except Exception as e:
            print(f"⚠️ Failed to load vector data: {e}")
            
        return vector_data
    
    def _generate_validation_summary(self, validations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate validation summary"""
        total_items = sum(v.get('total_items', 0) for v in validations)
        total_existing = sum(len(v.get('existing_items', [])) for v in validations)
        total_missing = sum(len(v.get('missing_items', [])) for v in validations)
        total_similar = sum(len(v.get('similar_items', [])) for v in validations)
        
        return {
            "total_items": total_items,
            "existing_items": total_existing,
            "missing_items": total_missing,
            "similar_items": total_similar,
            "coverage_ratio": total_existing / total_items if total_items > 0 else 0.0,
            "needs_review": total_missing > 0 or total_similar > 0
        }
    
    def _generate_recommendations(self, validations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        total_missing = sum(len(v.get('missing_items', [])) for v in validations)
        total_similar = sum(len(v.get('similar_items', [])) for v in validations)
        
        if total_missing == 0 and total_similar == 0:
            recommendations.append("✅ All items exist in the ontology, ready to use")
        else:
            if total_missing > 0:
                recommendations.append(f"❌ Found {total_missing} undefined items, need to add to the ontology")
            if total_similar > 0:
                recommendations.append(f"⚠️ Found {total_similar} similar items, suggest manual confirmation for reuse")
            
            recommendations.append("🔍 Suggest entering the manual review process to confirm the handling plan")
        
        return recommendations
    
    def _print_validation_summary(self, report: Dict[str, Any]):
        """Print validation summary"""
        summary = report.get('summary', {})
        
        print(f"\n📊 Manchester JSON validation results:")
        print(f"   📋 Total checked items: {summary.get('total_items', 0)} items")
        print(f"   ✅ Existing items: {summary.get('existing_items', 0)} items")
        print(f"   ❌ Missing items: {summary.get('missing_items', 0)} items")
        print(f"   ⚠️ Similar items: {summary.get('similar_items', 0)} items")
        print(f"   📈 Coverage ratio: {summary.get('coverage_ratio', 0.0):.1%}")
        print(f"   🔍 Needs review: {'Yes' if summary.get('needs_review', False) else 'No'}")
        
        print(f"\n💡 Recommendations:")
        for rec in report.get('recommendations', []):
            print(f"   {rec}")
    
    def _create_error_report(self, error_message: str) -> Dict[str, Any]:
        """Create error report"""
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "validation_version": "1.0",
                "error": True
            },
            "error_message": error_message,
            "summary": {
                "total_items": 0,
                "existing_items": 0,
                "missing_items": 0,
                "similar_items": 0,
                "coverage_ratio": 0.0,
                "needs_review": True
            },
            "recommendations": [f"❌ Validation failed: {error_message}"]
        }


if __name__ == "__main__":
    # Test validator
    validator = ManchesterJSONValidator()
    
    # Example JSON
    test_json = '''
    {
        "objects": [
            {"class": "Utensil"},
            {"class": "Knife", "subclassOf": "SharpUtensil"},
            {"class": "KitchenShears", "subclassOf": "SharpUtensil"}
        ],
        "materials": [],
        "attributes": [
            {"class": "Sharp", "attributeRelation": "hasProperty"}
        ],
        "states": [],
        "dangers": [
            {"class": "Harm"},
            {"class": "HazardousSituation"}
        ],
        "spatialRelations": [],
        "attributeRelations": [
            {"objectProperty": "hasStorageMethod", "domain": "Utensil", "range": "StorageMethod"}
        ]
    }
    '''
    
    result = validator.validate_manchester_json(test_json)
    print(f"\n📄 Validation completed, generating report")
