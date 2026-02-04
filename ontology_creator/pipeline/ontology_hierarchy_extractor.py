"""
Ontology hierarchy extractor
Extracts class hierarchy tree structures from OWL files for Step 3 new class placement analysis
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add project root path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


class OntologyHierarchyExtractor:
    """Ontology hierarchy extractor"""
    
    def __init__(self):
        """Initialize extractor"""
        self.ontology_root = Path(__file__).parent.parent / 'ontology' / 'core'
        self.namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'owl': 'http://www.w3.org/2002/07/owl#'
        }
        
    def extract_all_hierarchies(self) -> Dict[str, Dict[str, Any]]:
        """Extract hierarchy structure from all ontology files"""
        print("🌳 Starting ontology hierarchy extraction...")
        
        hierarchies = {}
        ontology_files = [
            ('object', 'object.owl'),
            ('material', 'material.owl'), 
            ('attribute', 'attribute.owl'),
            ('state', 'state.owl'),
            ('action', 'actions.owl'),
            ('agent', 'agents.owl'),
            ('danger', 'danger.owl')
        ]
        
        for category, filename in ontology_files:
            file_path = self.ontology_root / filename
            if file_path.exists():
                print(f"  📁 Processing {category}: {filename}")
                hierarchy = self.extract_hierarchy_from_file(file_path, category)
                if hierarchy:
                    # Ensure all Path objects are serialized
                    hierarchy = self._serialize_all_paths(hierarchy)
                    hierarchies[category] = hierarchy
                    print(f"    ✅ Extracted {len(hierarchy.get('classes', {}))} classes")
                else:
                    print(f"    ⚠️ Unable to extract hierarchy structure")
            else:
                print(f"    ❌ File does not exist: {filename}")
                
        # Finally ensure the entire result is fully serialized
        return self._serialize_all_paths(hierarchies)
    
    def _serialize_all_paths(self, obj):
        """Recursively serialize all Path objects"""
        if isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, '__fspath__'):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_all_paths(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_all_paths(item) for item in obj]
        elif isinstance(obj, set):
            return list(self._serialize_all_paths(list(obj)))
        else:
            return obj
    
    def extract_hierarchy_from_file(self, owl_file: Path, category: str) -> Optional[Dict[str, Any]]:
        """Extract hierarchy structure from a single OWL file"""
        try:
            tree = ET.parse(owl_file)
            root = tree.getroot()
            
            # Update namespace mapping
            namespaces = self.namespaces.copy()
            for prefix, uri in root.attrib.items():
                if prefix.startswith('xmlns:'):
                    namespaces[prefix[6:]] = uri
            
            classes = {}
            relationships = []
            
            # Find all class definitions
            for cls in root.findall('.//owl:Class', namespaces):
                class_info = self._extract_class_info(cls, namespaces)
                if class_info:
                    classes[class_info['uri']] = class_info
                    
            # Find subClassOf relationships
            for cls in root.findall('.//owl:Class', namespaces):
                subclass_relations = self._extract_subclass_relations(cls, namespaces)
                relationships.extend(subclass_relations)
            
            # Build tree structure
            tree_structure = self._build_tree_structure(classes, relationships)
            
            return {
                'category': category,
                'classes': classes,
                'relationships': relationships,
                'tree': tree_structure,
                'root_classes': self._find_root_classes(classes, relationships)
            }
            
        except Exception as e:
            print(f"    ❌ Failed to parse file: {e}")
            return None
    
    def _extract_class_info(self, cls_element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract basic class information"""
        about = cls_element.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
        if not about:
            return None
            
        # Extract label
        label_elem = cls_element.find('.//rdfs:label', namespaces)
        label = label_elem.text if label_elem is not None else ''
        
        # Extract comment
        comment_elem = cls_element.find('.//rdfs:comment', namespaces)
        comment = comment_elem.text if comment_elem is not None else ''
        
        # Extract class name (from URI)
        class_name = about.split('#')[-1] if '#' in about else about.split('/')[-1]
        
        return {
            'uri': about,
            'name': class_name,
            'label': label,
            'comment': comment,
            'parents': [],
            'children': []
        }
    
    def _extract_subclass_relations(self, cls_element, namespaces: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract subClassOf relationships"""
        relationships = []
        about = cls_element.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
        
        if not about:
            return relationships
            
        # Find all subClassOf elements
        for subclass_elem in cls_element.findall('.//rdfs:subClassOf', namespaces):
            resource = subclass_elem.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
            if resource:
                relationships.append({
                    'child': about,
                    'parent': resource,
                    'relation_type': 'subClassOf'
                })
                
        return relationships
    
    def _build_tree_structure(self, classes: Dict[str, Any], relationships: List[Dict[str, str]]) -> Dict[str, Any]:
        """Build tree structure"""
        # Initialize parent-child relationships
        for relationship in relationships:
            child_uri = relationship['child']
            parent_uri = relationship['parent']
            
            if child_uri in classes:
                classes[child_uri]['parents'].append(parent_uri)
            if parent_uri in classes:
                classes[parent_uri]['children'].append(child_uri)
        
        # Build hierarchy tree
        tree = {}
        root_classes = self._find_root_classes(classes, relationships)
        
        for root_uri in root_classes:
            if root_uri in classes:
                tree[root_uri] = self._build_subtree(root_uri, classes)
                
        return tree
    
    def _build_subtree(self, root_uri: str, classes: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively build subtree"""
        root_class = classes[root_uri]
        subtree = {
            'uri': root_uri,
            'name': root_class['name'],
            'label': root_class['label'],
            'comment': root_class['comment'],
            'children': {}
        }
        
        for child_uri in root_class['children']:
            if child_uri in classes:
                subtree['children'][child_uri] = self._build_subtree(child_uri, classes)
                
        return subtree
    
    def _find_root_classes(self, classes: Dict[str, Any], relationships: List[Dict[str, str]]) -> List[str]:
        """Find root classes (classes without internal parents or only external parents)"""
        root_classes = []
        
        # Build internal parent-child relationship mapping
        internal_children = {}  # child -> [internal_parents]
        
        for rel in relationships:
            child_uri = rel['child']
            parent_uri = rel['parent']
            
            # Only consider internal parent-child relationships
            if parent_uri in classes:
                if child_uri not in internal_children:
                    internal_children[child_uri] = []
                internal_children[child_uri].append(parent_uri)
        
        # Find classes without internal parents (i.e. root classes)
        for class_uri in classes:
            if class_uri not in internal_children:
                root_classes.append(class_uri)
                
        return root_classes
    
    def format_tree_for_llm(self, hierarchy: Dict[str, Any], max_depth: int = 3) -> str:
        """Format tree structure as text suitable for LLM analysis"""
        if not hierarchy or 'tree' not in hierarchy:
            return ""
            
        category = hierarchy['category']
        tree = hierarchy['tree']
        
        formatted = f"## {category.upper()} Ontology Hierarchy:\n\n"
        
        for root_uri, subtree in tree.items():
            formatted += self._format_subtree_for_llm(subtree, 0, max_depth)
            formatted += "\n"
            
        return formatted
    
    def _format_subtree_for_llm(self, subtree: Dict[str, Any], current_depth: int, max_depth: int) -> str:
        """Recursively format subtree as text"""
        if current_depth > max_depth:
            return ""
            
        indent = "  " * current_depth
        name = subtree['name']
        label = subtree['label']
        comment = subtree['comment']
        
        # Format current node
        node_text = f"{indent}• {name}"
        if label and label != name:
            node_text += f" ({label})"
        if comment:
            node_text += f" - {comment[:100]}{'...' if len(comment) > 100 else ''}"
        node_text += "\n"
        
        # Recursively process child nodes
        for child_subtree in subtree['children'].values():
            node_text += self._format_subtree_for_llm(child_subtree, current_depth + 1, max_depth)
            
        return node_text
    
    def get_hierarchy_summary(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Get hierarchy summary information"""
        if not hierarchy:
            return {}
            
        return {
            'category': hierarchy['category'],
            'total_classes': len(hierarchy['classes']),
            'root_classes_count': len(hierarchy['root_classes']),
            'root_classes': [
                {
                    'name': hierarchy['classes'][uri]['name'],
                    'label': hierarchy['classes'][uri]['label'],
                    'children_count': len(hierarchy['classes'][uri]['children'])
                }
                for uri in hierarchy['root_classes']
                if uri in hierarchy['classes']
            ]
        }


def test_hierarchy_extraction():
    """Test hierarchy extraction"""
    extractor = OntologyHierarchyExtractor()
    
    print("🧪 Testing ontology hierarchy extraction...")
    hierarchies = extractor.extract_all_hierarchies()
    
    for category, hierarchy in hierarchies.items():
        print(f"\n📊 {category.upper()} Summary:")
        summary = extractor.get_hierarchy_summary(hierarchy)
        print(f"  - Total classes: {summary['total_classes']}")
        print(f"  - Root classes count: {summary['root_classes_count']}")
        
        print(f"\n🌳 {category.upper()} Tree Structure Preview:")
        tree_text = extractor.format_tree_for_llm(hierarchy, max_depth=2)
        print(tree_text[:500] + "..." if len(tree_text) > 500 else tree_text)


if __name__ == "__main__":
    test_hierarchy_extraction()
