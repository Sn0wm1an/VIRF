#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OWL XML Generator - responsible for generating OWL XML format content
"""

from typing import Dict, Any, List


class OWLXMLGenerator:
    """OWL XML Generator - generates standard OWL XML format content"""
    
    def generate_class_xml(self, class_name: str, label: str, comment: str, subclass_of: List[str]) -> str:
        """Generate OWL XML definition for class"""
        # Generate subclass relationships
        subclass_elements = []
        for parent in subclass_of:
            subclass_elements.append(f'        <rdfs:subClassOf rdf:resource="#{parent}"/>')
        
        xml_template = f"""
    <!-- {class_name} Class -->
    <owl:Class rdf:about="#{class_name}">
{chr(10).join(subclass_elements)}
        <rdfs:label>{label}</rdfs:label>
        <rdfs:comment>{comment}</rdfs:comment>
    </owl:Class>"""
        
        return xml_template
    
    def generate_rule_xml(self, rule_name: str, manchester_def: str, safety_attrs: Dict[str, Any]) -> str:
        """Generate OWL XML definition for safety rules (following kitchen-axioms.owl format)"""
        danger_level = safety_attrs.get('danger_level', 2)
        safety_warning = safety_attrs.get('safety_warning', 'Please pay attention to safety operations')
        trigger_reason = safety_attrs.get('trigger_reason', 'Potential safety risk')
        
        # Generate complete equivalent class definition
        equivalent_class_xml = self.generate_full_equivalent_class_xml(manchester_def)
        
        xml_template = f"""
    <!-- {rule_name} Safety Rule -->
    <owl:Class rdf:about="#{rule_name}Danger">
        <rdfs:subClassOf rdf:resource="danger:DangerousSituation"/>
        <rdfs:label>{rule_name} Danger</rdfs:label>
        <rdfs:comment>Safety rule for {rule_name} dangerous situation</rdfs:comment>
        
        {equivalent_class_xml}
        
        <!-- Danger Level Property -->
        <rdfs:subClassOf>
            <owl:Restriction>
                <owl:onProperty rdf:resource="danger:dangerLevel"/>
                <owl:hasValue rdf:datatype="http://www.w3.org/2001/XMLSchema#int">{danger_level}</owl:hasValue>
            </owl:Restriction>
        </rdfs:subClassOf>
        
        <!-- Safety Warning Property -->
        <rdfs:subClassOf>
            <owl:Restriction>
                <owl:onProperty rdf:resource="danger:safetyWarning"/>
                <owl:hasValue rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{safety_warning}</owl:hasValue>
            </owl:Restriction>
        </rdfs:subClassOf>
        
        <!-- Trigger Reason Property -->
        <rdfs:subClassOf>
            <owl:Restriction>
                <owl:onProperty rdf:resource="danger:triggerReason"/>
                <owl:hasValue rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{trigger_reason}</owl:hasValue>
            </owl:Restriction>
        </rdfs:subClassOf>
    </owl:Class>"""
        
        return xml_template
    
    def generate_full_equivalent_class_xml(self, manchester_def: str) -> str:
        """Generate complete equivalent class definition XML (following kitchen-axioms.owl format)"""
        if not manchester_def:
            return ""
        
        # Parse Manchester syntax
        from .manchester_parser import ManchesterParser
        parser = ManchesterParser(None)  # No base_writer needed, only parse conditions
        conditions = parser.parse_conditions(manchester_def)
        
        # If parsing fails or conditions are empty, return empty template
        if not conditions:
            print(f"⚠️ [WARNING] Manchester syntax parsing failed or conditions are empty: {manchester_def}")
            return ""
        
        conditions_xml = []
        for condition in conditions:
            if condition['type'] == 'class':
                # Validate and clean class name
                class_name = self._validate_owl_identifier(condition["value"])
                if class_name:
                    conditions_xml.append(f'                    <rdf:Description rdf:about="http://purl.obolibrary.org/obo/core/object#{class_name}"/>')
            elif condition['type'] == 'restriction':
                restriction_xml = self.generate_restriction_xml(condition)
                if restriction_xml and not restriction_xml.startswith('<!--'):
                    conditions_xml.append(restriction_xml)
        
        # If no valid conditions, return empty
        if not conditions_xml:
            print(f"⚠️ [WARNING] No valid OWL conditions generated: {manchester_def}")
            return ""
        
        equivalent_class_template = f"""<!-- Use equivalent class definition: situations meeting all conditions are dangerous -->
        <owl:equivalentClass>
            <owl:Class>
                <owl:intersectionOf rdf:parseType="Collection">
{chr(10).join(conditions_xml)}
                </owl:intersectionOf>
            </owl:Class>
        </owl:equivalentClass>"""
        
        return equivalent_class_template
    
    def generate_restriction_xml(self, condition: Dict[str, Any]) -> str:
        """Generate restriction XML"""
        property_name = condition.get('property', '').strip()
        target = condition.get('target', '').strip()
        
        # Validate parameters
        if not property_name or not target:
            return f'<!-- Invalid restriction: missing property ({property_name}) or target ({target}) -->'
        
        # Validate and clean property name and target value
        clean_property = self._validate_property_name(property_name)
        if not clean_property:
            return f'<!-- Invalid property name: {property_name} -->'
        
        clean_target = self._validate_owl_identifier(target)
        if not clean_target:
            return f'<!-- Invalid target identifier: {target} -->'
        
        # Determine correct namespace and property based on target type
        target_namespace, final_property = self._determine_target_namespace_and_property(
            clean_property, clean_target, property_name
        )
        
        if condition.get('quantifier') == 'some':
            return f"""                    <owl:Restriction>
                        <owl:onProperty rdf:resource="http://purl.obolibrary.org/obo/core/relation#{final_property}"/>
                        <owl:someValuesFrom rdf:resource="http://purl.obolibrary.org/obo/core/{target_namespace}#{clean_target}"/>
                    </owl:Restriction>"""
        
        return f'<!-- Could not generate restriction for: {condition} -->'
    
    def generate_intersection_class_xml(self, manchester_def: str) -> str:
        """Generate intersection class OWL XML (A and B)"""
        parts = manchester_def.split(' and ')
        
        intersections = []
        for part in parts:
            part = part.strip()
            if part.startswith('(') and part.endswith(')'):
                restriction_xml = self.parse_restriction_xml(part[1:-1])
                intersections.append(restriction_xml)
            elif '(' in part and 'some' in part:
                intersections.append(f'<!-- Could not parse complex restriction: {part} -->')
            else:
                if part and not part.startswith('(') and 'some' not in part:
                    class_xml = f'<rdf:Description rdf:resource="http://purl.obolibrary.org/obo/core/object#{part}"/>'
                    intersections.append(class_xml)
                else:
                    intersections.append(f'<!-- Could not parse restriction: {part} -->')
        
        intersection_content = '\n            '.join(intersections)
        
        return f"""
        <!-- Equivalent Class Definition -->
        <owl:equivalentClass>
            <owl:Class>
                <owl:intersectionOf rdf:parseType="Collection">
                    {intersection_content}
                </owl:intersectionOf>
            </owl:Class>
        </owl:equivalentClass>"""
    
    def parse_restriction_xml(self, restriction_str: str) -> str:
        """Parse restriction string, e.g. 'hasProperty some Sharp'"""
        parts = restriction_str.split()
        if len(parts) >= 3:
            property_name = parts[0]
            quantifier = parts[1]
            target_class = ' '.join(parts[2:])
            
            if quantifier.lower() == 'some':
                return f"""<owl:Restriction>
                    <owl:onProperty rdf:resource="http://purl.obolibrary.org/obo/core/relation#{property_name}"/>
                    <owl:someValuesFrom rdf:resource="http://purl.obolibrary.org/obo/core/attribute#{target_class}"/>
                </owl:Restriction>"""
        
        return f'<!-- Could not parse restriction: {restriction_str} -->'
    
    def _validate_owl_identifier(self, identifier: str) -> str:
        """Validate and clean OWL identifier, remove invalid characters"""
        if not identifier:
            return ""
        
        # Remove invalid characters: spaces, parentheses, "or", "and" etc.
        cleaned = identifier.strip()
        
        # Handle compound names like "Water or Ice"
        if ' or ' in cleaned:
            # Take the first valid part
            parts = cleaned.split(' or ')
            cleaned = parts[0].strip()
        
        if ' and ' in cleaned:
            # Take the first valid part
            parts = cleaned.split(' and ')
            cleaned = parts[0].strip()
        
        # Remove all spaces and special characters
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c in ['_', '-'])
        
        return cleaned if cleaned else ""
    
    def _validate_property_name(self, prop_name: str) -> str:
        """Validate and clean property name"""
        if not prop_name:
            return ""
        
        cleaned = prop_name.strip()
        
        # Handle invalid property names like "not ("
        if 'not (' in cleaned:
            # Try to extract valid part or use default property
            if 'hasState' in cleaned:
                return 'lacksState'
            elif 'isNear' in cleaned:
                return 'lacksNearby'
            else:
                return 'lacks'  # Default negation property
        
        # Remove invalid characters
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c in ['_', '-'])
        
        return cleaned if cleaned else ""
    
    def _determine_target_namespace_and_property(self, property_name: str, target: str, original_property: str) -> tuple:
        """Determine namespace and property based on target type"""
        
        # Common object type indicators
        object_indicators = [
            'Person', 'Child', 'Floor', 'Stove', 'Appliance', 'Water', 'Oil', 
            'DeepFryer', 'Pot', 'Pan', 'Chair', 'Stepstool', 'HotSurface',
            'Fryer', 'Chemical', 'Food', 'Container', 'Equipment', 'Tool',
            'FireSource', 'LooseClothing', 'PlasticUtensil', 'Potholder',
            'DishTowel', 'Curtain', 'Stovetop', 'BackBurner', 'PotHandle',
            'GrillArea', 'FlammableItem', 'HeatProducingEquipment', 'Oven',
            'Grill', 'Burner', 'FireExtinguisher', 'OilGreaseFire', 'Product',
            'Ammonia', 'Bleach', 'ChemicalContainer', 'FoodContainer',
            'FoodContactSurface', 'DryCabinet', 'LockedCabinet', 'Hand'
        ]
        
        # Common attribute type indicators
        attribute_indicators = [
            'Sharp', 'Hot', 'Slippery', 'Wet', 'Dry', 'Clean', 'Dirty',
            'On', 'Off', 'Open', 'Closed', 'Full', 'Empty', 'Safe', 'Dangerous',
            'Flammable', 'Poisonous', 'Toxic', 'Reachable', 'Overheated',
            'Correct', 'ImproperlyStored', 'Unlabelled', 'FreeFromHazards',
            'RecognizedHazard', 'WaterExposedArea', 'PluggedInGFCIOutlet',
            'Timer', 'GrillArea', 'HotOilGrease', 'HouseholdCleaningProduct',
            'Dish', 'FoodPreparationArea'
        ]
        
        # Determine if target is object or attribute
        is_object = any(indicator in target for indicator in object_indicators)
        is_attribute = any(indicator in target for indicator in attribute_indicators)
        
        # Default to object if not attribute
        if not is_object and not is_attribute:
            # If contains these words, usually attribute
            if any(word in target.lower() for word in ['hot', 'cold', 'wet', 'dry', 'sharp', 'safe', 'dangerous']):
                is_attribute = True
            else:
                is_object = True
        
        # Determine namespace and property
        if is_attribute:
            namespace = "attribute"
            # For attribute, use hasProperty relationship
            if 'lacks' in property_name.lower() or 'not' in original_property.lower():
                final_property = "lacksProperty"  # Negative property relationship
            else:
                final_property = "hasProperty"  # Normal property relationship
        else:
            namespace = "object" 
            # For object, use original spatial relationship
            final_property = property_name
        
        return namespace, final_property
