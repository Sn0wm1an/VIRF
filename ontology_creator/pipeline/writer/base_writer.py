#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base ontology writer - core functionality and configuration
"""

import os
import json
import shutil
import datetime as dt
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import owlready2 as owl
    from owlready2 import World, Thing
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from utils.ontology_loader import OntologyLoader
    OWLREADY2_AVAILABLE = True
except ImportError as e:
    print(f"Warning: owlready2 or dependencies not available: {e}")
    OWLREADY2_AVAILABLE = False


class BaseOntologyWriter:
    """Base ontology writer - provides core configuration and common functionality"""
    
    def __init__(self, ontology_base_path: str = "ontology"):
        """
        Initialize base writer
        
        Args:
            ontology_base_path: Ontology file root directory path
        """
        if not OWLREADY2_AVAILABLE:
            raise ImportError("owlready2 library not available, cannot use ontology writer")
            
        self.ontology_base_path = Path(ontology_base_path)
        self.backup_path = Path(ontology_base_path + "_copy")
        
        # Initialize owlready2 World
        self.world = World()
        
        # Ontology URI mapping
        self.ontology_uris = {
            "object": "http://purl.obolibrary.org/obo/core/object",
            "relation": "http://purl.obolibrary.org/obo/core/relation", 
            "danger": "http://purl.obolibrary.org/obo/core/danger",
            "material": "http://purl.obolibrary.org/obo/core/material",
            "state": "http://purl.obolibrary.org/obo/core/state",
            "attribute": "http://purl.obolibrary.org/obo/core/attribute",
            "rag_kitchen": "http://example.org/ontology/rag-kitchen",
            "new_ontology": "http://example.org/ontology/new-ontology"
        }
        
        # Ontology object cache
        self.ontologies = {}
        self.loaded_classes = {}
        self.loaded_properties = {}
        
        # Track newly created content
        self.new_classes_xml = []
        self.new_rules_xml = []
    
    def backup_ontology(self, debug: bool = False):
        """Backup ontology directory"""
        try:
            if self.backup_path.exists():
                if debug:
                    print(f"🗑️ [DEBUG] Delete old backup: {self.backup_path}")
                shutil.rmtree(self.backup_path)
            
            if debug:
                print(f"💾 [DEBUG] Create ontology backup: {self.ontology_base_path} -> {self.backup_path}")
            
            shutil.copytree(self.ontology_base_path, self.backup_path)
            
            if debug:
                print(f"✅ [DEBUG] Backup completed")
                
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Backup failed: {e}")
            raise
    
    def load_ontologies_to_world(self, debug: bool = False):
        """Use OntologyLoader to load existing ontology files to owlready2 World"""
        try:
            if debug:
                print(f"🌐 [DEBUG] Load ontologies to owlready2 World")
            
            # Load all ontologies
            loader = OntologyLoader()
            world, main_onto = loader.load_all_ontologies(self.world)
            
            # Update world reference
            self.world = world
            
            # Build ontology mapping cache
            for onto_iri in list(self.world.ontologies):
                try:
                    # Get ontology object through IRI
                    onto_obj = self.world.get_ontology(onto_iri)
                    
                    if onto_obj and hasattr(onto_obj, 'base_iri'):
                        base_iri = onto_obj.base_iri
                        
                        # Map ontology name based on URI
                        if "object" in base_iri:
                            self.ontologies["object"] = onto_obj
                        elif "relation" in base_iri:
                            self.ontologies["relation"] = onto_obj
                        elif "danger" in base_iri:
                            self.ontologies["danger"] = onto_obj
                        elif "material" in base_iri:
                            self.ontologies["material"] = onto_obj
                        elif "state" in base_iri:
                            self.ontologies["state"] = onto_obj
                        elif "attribute" in base_iri:
                            self.ontologies["attribute"] = onto_obj
                        elif "rag-kitchen" in base_iri:
                            self.ontologies["rag_kitchen"] = onto_obj
                        
                        if debug:
                            print(f"  ✅ [DEBUG] Ontology mapped: {base_iri}")
                    else:
                        if debug:
                            print(f"  ⚠️ [DEBUG] Invalid ontology object: {onto_iri}")
                            
                except Exception as e:
                    if debug:
                        print(f"  ❌ [DEBUG] Failed to get ontology {onto_iri}: {e}")
                
            if debug:
                print(f"🎯 [DEBUG] Total loaded {len(list(self.world.ontologies))} ontologies")
                print(f"🎯 [DEBUG] Cached mapping {len(self.ontologies)} main ontologies")
                
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Ontology loading failed: {e}")
            raise
    
    def load_analysis_data(self, analysis_file: str, debug: bool = False) -> Optional[Dict[str, Any]]:
        """Load hierarchical analysis data"""
        try:
            if debug:
                print(f"📖 [DEBUG] Loading analysis file: {analysis_file}")
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if debug:
                print(f"✅ [DEBUG] Data loaded successfully")
                
            return data.get('analysis_result', {})
            
        except Exception as e:
            if debug:
                print(f"❌ [DEBUG] Data loading failed: {e}")
            return None
    
    def get_class_by_name(self, class_name: str):
        """Get class object by name"""
        # Cache check
        if class_name in self.loaded_classes:
            return self.loaded_classes[class_name]
        
        # Search in all loaded ontologies
        for onto in self.ontologies.values():
            for cls in onto.classes():
                if cls.name == class_name:
                    self.loaded_classes[class_name] = cls
                    return cls
        
        return None
    
    def get_property_by_name(self, property_name: str):
        """Get property object by name"""
        # Cache check
        if property_name in self.loaded_properties:
            return self.loaded_properties[property_name]
        
        # Search in all loaded ontologies
        for onto in self.ontologies.values():
            for prop in onto.properties():
                if prop.name == property_name:
                    self.loaded_properties[property_name] = prop
                    return prop
        
        return None
    
    def init_ontology_world(self, debug: bool = False) -> Dict[str, Any]:
        """Convenience method to initialize ontology world"""
        try:
            self.load_ontologies_to_world(debug)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
