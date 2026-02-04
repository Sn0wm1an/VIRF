#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safety verifier based on Pellet reasoner
Using Owlready2 and Pellet for ontological reasoning and safety verification
"""

import owlready2 as owl
from owlready2 import sync_reasoner_pellet
import os
import sys
from typing import Dict, Any, List

try:
    from ontology_loader import OntologyLoader
except ImportError:
    # Fallback if ontology_loader is not available
    class OntologyLoader:
        def __init__(self, verbose=False):
            self.verbose = verbose
        def load_ontology(self, ontology_file=None, ontology_uri=None, world_instance=None):
            if world_instance is None:
                world_instance = owl.World()
            if ontology_uri:
                return world_instance.get_ontology(ontology_uri).load()
            elif ontology_file:
                return world_instance.get_ontology(f"file://{ontology_file}").load()
            else:
                raise ValueError("Either ontology_file or ontology_uri must be provided")


class SafetyVerifier:
    """Safety verifier class using Pellet reasoner for safety checks"""
    
    def __init__(self, ontology_path: str = None, external_world=None, external_onto=None, verbose: bool = False):
        """Initialize SafetyVerifier"""
        self.ontology_path = ontology_path
        self.world = external_world
        self.onto = external_onto
        self.verbose = verbose
        self.using_external_world = external_world is not None and external_onto is not None
        
    def load_ontology(self, ontology_path: str = None) -> bool:
        """Load ontology file"""
        if self.using_external_world:
            if self.verbose:
                print("✅ Using external world and onto, skipping ontology loading")
            return True
            
        try:
            if ontology_path:
                self.ontology_path = ontology_path
                
            if not self.ontology_path:
                print("Error: Ontology file path not specified")
                return False
            
            self.world = owl.World()
            loader = OntologyLoader(verbose=self.verbose)
            
            if self.ontology_path.startswith("http"):
                self.onto = loader.load_ontology(ontology_uri=self.ontology_path, world_instance=self.world)
            else:
                self.onto = loader.load_ontology(ontology_file=self.ontology_path, world_instance=self.world)
            
            if self.verbose:
                print(f"✅ Ontology loaded successfully: {self.ontology_path}")
            return True
                
        except Exception as e:
            print(f"❌ Failed to load ontology: {e}")
            return False

    
    def run_reasoning(self) -> bool:
        """Run Pellet reasoner using owlready2 built-in functionality"""
        try:
            if self.verbose:
                print("\n[Step 2] Calling Pellet reasoner...")
            owl.sync_reasoner_pellet(self.world, infer_property_values=True)
            if self.verbose:
                print(" -> Reasoning completed")
            return True
            
        except owl.OwlReadyInconsistentOntologyError as e:
            print("❌ Ontology inconsistent")
            print(f"Detailed error: {e}")
            return False
        except Exception as e:
            print(f"❌ Reasoning failed: {e}")
            return False
    


    
    def _build_causal_chain(self, hazard_instance) -> Dict[str, Any]:
        """
        Build simplified causal chain by analyzing hazard instance properties and relations
        """
        subject_name = hazard_instance.name
        key_facts = []
        
        # Check danger level
        danger_level = getattr(hazard_instance, 'dangerLevel', None)
        if danger_level:
            key_facts.append(f"Danger level: {danger_level}")
        
        # Check safety warning
        safety_warning = getattr(hazard_instance, 'safetyWarning', None)
        if safety_warning:
            key_facts.append(f"Warning: {safety_warning}")
        
        # Check key material properties
        materials = getattr(hazard_instance, 'hasMaterial', [])
        if materials:
            material_names = [m.name if hasattr(m, 'name') else str(m) for m in materials]
            key_facts.append(f"Materials: {', '.join(material_names)}")
        
        # Check key properties
        properties = getattr(hazard_instance, 'hasProperty', [])
        if properties:
            dangerous_props = []
            for prop in properties:
                prop_name = prop.name if hasattr(prop, 'name') else str(prop)
                if any(keyword in prop_name for keyword in ['Conductive', 'Flammable', 'Toxic', 'Sharp']):
                    dangerous_props.append(prop_name)
            if dangerous_props:
                key_facts.append(f"Dangerous properties: {', '.join(dangerous_props)}")
        
        # Generate concise message
        if key_facts:
            message = f"{subject_name} identified as hazardous: {'; '.join(key_facts)}"
        else:
            message = f"{subject_name} identified as dangerous situation by reasoning system"

        return {
            "message": message,
            "key_facts": key_facts
        }

    def _get_rich_hazard_details(self, hazard_instance) -> Dict[str, Any]:
        """
        Extract all structured information for a single hazard instance
        """
        # 1. Determine the most specific hazard type as violated rule ID
        HazardousSituationClass = self.world.search_one(iri="*DangerousSituation")
        inferred_types = []
        
        
        # Simplified logic: directly find danger-related types
        for c in hazard_instance.is_a:
            if hasattr(c, 'name'):
                class_name = c.name
                # Check if class name contains danger keywords or is subclass of DangerousSituation
                if ('Danger' in class_name or 'Hazard' in class_name or 'LogicalInconsistency' in class_name):
                    if class_name != 'DangerousSituation':  # Exclude base class, select more specific subclass
                        inferred_types.append(c)
                elif hasattr(c, 'ancestors') and callable(c.ancestors):
                    try:
                        if HazardousSituationClass in c.ancestors():
                            inferred_types.append(c)
                    except:
                        pass
        
        
        # Select most specific subclass as rule ID - prioritize LogicalInconsistency and InterruptDangerousSituation
        violated_rule_class = HazardousSituationClass
        if inferred_types:
            # Prioritize LogicalInconsistency types
            logical_inconsistency_classes = [c for c in inferred_types if 'LogicalInconsistency' in c.name]
            if logical_inconsistency_classes:
                violated_rule_class = logical_inconsistency_classes[0]
            else:
                # Next, select InterruptDangerousSituation or classes containing Interrupt
                interrupt_classes = [c for c in inferred_types if 'Interrupt' in c.name]
                if interrupt_classes:
                    violated_rule_class = interrupt_classes[0]
                else:
                    # Finally, select the first inference type
                    violated_rule_class = inferred_types[0]
        violated_rule_id = violated_rule_class.name
        if self.verbose:
            print(f"   📊 Extracted rule ID: violated_rule_class={violated_rule_class}, name='{violated_rule_id}'")
        
        # 2. Query rule description and suggestions
        description = "No description available."
        suggestion = None
        
        # Use rdfs:comment as description
        comments = getattr(violated_rule_class, "comment", [])
        if comments:
            description = comments[0]
            
        # Use custom annotation property core:suggestion as suggestions
        # Note: annotation property needs to be defined in ontology
        suggestions = getattr(violated_rule_class, "suggestion", [])
        if suggestions:
            suggestion = suggestions[0]

        # 3. Extract danger properties from OWL class definitions
        danger_level = self._extract_owl_has_value(violated_rule_class, 'dangerLevel')
        safety_warning = self._extract_owl_has_value(violated_rule_class, 'safetyWarning')
        trigger_reason = self._extract_owl_has_value(violated_rule_class, 'triggerReason')
        
        # If not available on class, try to get from instance
        if danger_level is None:
            danger_level = getattr(hazard_instance, 'dangerLevel', None)
        if safety_warning is None:
            safety_warning = getattr(hazard_instance, 'safetyWarning', None)
        if trigger_reason is None:
            trigger_reason = getattr(hazard_instance, 'triggerReason', None)
        
        # 4. Build causal chain
        causal_chain = self._build_causal_chain(hazard_instance)
        
        # 5. Assemble final hazard_details
        details = {
            "violated_rule": {
                "id": violated_rule_id,
                "description": description
            },
            "causal_chain": causal_chain,
            "suggestion_from_ontology": suggestion,
            "danger_level": danger_level,
            "safety_warning": safety_warning,
            "trigger_reason": trigger_reason
        }
        
        return details

    def _extract_owl_has_value(self, owl_class, property_name: str):
        """Extract hasValue from OWL class restrictions
        
        Args:
            owl_class: OWL class object
            property_name: Property name (e.g., dangerLevel, safetyWarning)
            
        Returns:
            Extracted value, None if not found
        """
        try:
            # Check all parent class constraints (is_a relations)
            for parent in owl_class.is_a:
                # Check if it's an OWL Restriction
                if hasattr(parent, '__class__') and 'Restriction' in str(parent.__class__):
                    # Check onProperty and hasValue
                    if hasattr(parent, 'property') and hasattr(parent, 'value'):
                        prop = parent.property
                        prop_name = prop.name if hasattr(prop, 'name') else str(prop)
                        
                        # Check if property name matches
                        if property_name in prop_name:
                            value = parent.value
                            return value
            
            # Recursively check all ancestor classes
            if hasattr(owl_class, 'ancestors'):
                try:
                    for ancestor in owl_class.ancestors():
                        if ancestor != owl_class:  # Avoid self-loop
                            result = self._extract_owl_has_value(ancestor, property_name)
                            if result is not None:
                                return result
                except:
                    pass
                                    
        except Exception as e:
            pass
                
        return None

    def check_safety(self):
        """Check safety status and return structured hazard information"""
        try:
            if self.verbose:
                print("\n[Step 4] Querying reasoning results...")
            
            result = {'is_safe': True, 'hazard_count': 0, 'hazards': [], 'message': ''}
            hazardous_instances = []
            
            # Find all dangerous instances
            all_individuals = list(self.world.individuals())
            danger_patterns = ['Danger', 'DangerousSituation', 'Hazard', 'LogicalInconsistency']
            
            for ind in all_individuals:
                for cls in ind.is_a:
                    if hasattr(cls, 'name') and any(pattern in cls.name for pattern in danger_patterns):
                        if ind not in hazardous_instances:
                            hazardous_instances.append(ind)

            if not hazardous_instances:
                result['message'] = "Safe (no dangerous situations detected)"
                return result

            # Separate LogicalInconsistency from other hazards
            logical_inconsistency_hazards = []
            other_hazards = []
            
            for instance in hazardous_instances:
                is_logical_inconsistency = any(
                    hasattr(cls, 'name') and 'LogicalInconsistency' in cls.name 
                    for cls in instance.is_a
                )
                
                if is_logical_inconsistency:
                    logical_inconsistency_hazards.append(instance)
                else:
                    other_hazards.append(instance)
            
            # Set status based on instance types
            if other_hazards:
                result['is_safe'] = False
                result['status'] = 'DANGER'  
                result['message'] = f"Detected {len(other_hazards)} dangerous situation(s)"
                if logical_inconsistency_hazards:
                    result['message'] += f" and {len(logical_inconsistency_hazards)} logical inconsistency warning(s)"
            elif logical_inconsistency_hazards:
                result['is_safe'] = True
                result['status'] = 'WARNING'
                result['message'] = f"Detected {len(logical_inconsistency_hazards)} warning(s) (logical inconsistency)"
            else:
                result['is_safe'] = False
                result['status'] = 'DANGER'  
                result['message'] = f"Detected {len(hazardous_instances)} unclassified dangerous situation(s)"

            result['hazard_count'] = len(hazardous_instances)
            
            # Extract hazard details
            for hazard_instance in hazardous_instances:
                hazard_details = self._get_rich_hazard_details(hazard_instance)
                result['hazards'].append(hazard_details)
            
            return result

        except Exception as e:
            print(f"\n❌ Safety check failed: {e}")
            result = {'is_safe': True, 'hazard_count': 0, 'hazards': [], 'message': f"Safety check failed: {e}"}
            return result

