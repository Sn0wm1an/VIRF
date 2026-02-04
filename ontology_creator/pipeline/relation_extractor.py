#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relation extractor - Extract spatial relation properties from OWL files
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Set
from pathlib import Path


class RelationExtractor:
    """Extract spatial relation properties from relation.owl file"""
    
    def __init__(self, relation_owl_path: str = "ontology/core/relation.owl"):
        """
        Initialize relation extractor
        
        Args:
            relation_owl_path: Relative path to relation.owl file
        """
        self.relation_owl_path = Path(relation_owl_path)
        self.spatial_relations = set()
        self.attribute_relations = set()
        self.all_relations = set()
        
        self._extract_relations()
    
    def _extract_relations(self):
        """Extract all relation properties from OWL file"""
        if not self.relation_owl_path.exists():
            print(f"❌ Cannot find OWL file: {self.relation_owl_path}")
            return
        
        try:
            # Read OWL file content
            with open(self.relation_owl_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use regular expressions to extract ObjectProperty
            pattern = r'<owl:ObjectProperty rdf:about="#(\w+)">'
            matches = re.findall(pattern, content)
            
            for relation in matches:
                self.all_relations.add(relation)
                
                # Classify by relation name
                if self._is_spatial_relation(relation, content):
                    self.spatial_relations.add(relation)
                elif self._is_attribute_relation(relation):
                    self.attribute_relations.add(relation)
            
            print(f"🔍 Successfully extracted {len(self.all_relations)} relation properties:")
            print(f"   - Spatial relations: {len(self.spatial_relations)} items")  
            print(f"   - Attribute relations: {len(self.attribute_relations)} items")
            
        except Exception as e:
            print(f"❌ Error extracting relations: {e}")
    
    def _is_spatial_relation(self, relation: str, content: str) -> bool:
        """Determine if it's a spatial relation"""
        # Check if it's a sub-property of SpatialRelation
        spatial_keywords = [
            'SpatialRelation', 'isInside', 'contains', 'touches', 'isAdjacentTo',
            'supports', 'isNear', 'isAbove', 'isBelow', 'isOn', 'isUnder',
            'isLeftOf', 'isRightOf', 'isInFrontOf', 'isBehind', 'isFar',
            'isClose', 'isPartOf', 'hasPart', 'isBetween', 'isAround',
            'isAlongside', 'isConnectedTo'
        ]
        
        return relation in spatial_keywords or 'spatial' in relation.lower()
    
    def _is_attribute_relation(self, relation: str) -> bool:
        """Determine if it's an attribute relation"""
        attribute_relations = ['hasProperty', 'hasState', 'hasMaterial']
        return relation in attribute_relations
    
    def get_spatial_relations(self) -> Set[str]:
        """Get all spatial relations"""
        return self.spatial_relations.copy()
    
    def get_attribute_relations(self) -> Set[str]:
        """Get all attribute relations"""
        return self.attribute_relations.copy()
    
    def get_all_relations(self) -> Set[str]:
        """Get all relations"""
        return self.all_relations.copy()
    
    def is_valid_relation(self, relation: str) -> bool:
        """Check if relation is in valid list"""
        return relation in self.all_relations
    
    def get_relation_info(self) -> Dict[str, List[str]]:
        """Get relation information summary"""
        return {
            'spatial_relations': sorted(list(self.spatial_relations)),
            'attribute_relations': sorted(list(self.attribute_relations)),
            'all_relations': sorted(list(self.all_relations))
        }
    
    def print_relations(self):
        """Print all extracted relations"""
        print("\n🔗 Spatial Relations:")
        for relation in sorted(self.spatial_relations):
            print(f"   - {relation}")
        
        print("\n🏷️ Attribute Relations:")  
        for relation in sorted(self.attribute_relations):
            print(f"   - {relation}")


if __name__ == "__main__":
    # Test relation extractor
    extractor = RelationExtractor()
    extractor.print_relations()
