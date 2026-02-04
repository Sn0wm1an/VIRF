#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refactored ontology loader
Uses class structure to manage ontology loading and mapping uniformly, avoiding duplicate imports and global variable chaos
"""

import os
import json
import owlready2 as owl
from typing import Optional, Dict, List


class OntologyLoader:
    """Ontology loader class for uniform management of ontology mapping and loading"""
    
    # Class-level global instance for backward compatibility
    _global_instance: Optional['OntologyLoader'] = None
    
    def __init__(self, config_file: Optional[str] = None, verbose: bool = False):
        """
        Initialize ontology loader
        
        Args:
            config_file: Configuration file path, defaults to ontology_mappings.json in the same directory
            verbose: Whether to enable detailed logging
        """
        # Use path relative to module file, go up one level to verify_core directory, then enter ontology directory
        module_dir = os.path.dirname(__file__)  # src directory
        verify_core_dir = os.path.dirname(module_dir)  # verify_core directory
        self.ontology_base_dir = os.path.join(verify_core_dir, "ontology")
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), "ontology_mappings.json")
        self.verbose = verbose
        self.mappings: Dict[str, str] = {}
        self._load_mappings()
        self._register_mappings()
        
        # Set as global instance (if not already set)
        if OntologyLoader._global_instance is None:
            OntologyLoader._global_instance = self
    
    def _load_mappings(self):
        """Load ontology mappings from JSON configuration file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Directly read flat mapping structure
            for uri, relative_path in config["mappings"].items():
                # Convert relative path to absolute path
                abs_path = os.path.join(self.ontology_base_dir, relative_path.replace('/', os.sep))
                self.mappings[uri] = abs_path
            
            if self.verbose:
                print(f"✅ Loaded {len(self.mappings)} ontology mappings from configuration file")
            
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON configuration file format error: {e}")
        except Exception as e:
            print(f"❌ Error occurred while loading configuration file: {e}")
    
    def _register_mappings(self):
        """Register mappings to owlready2's PREDEFINED_ONTOLOGIES"""
        if self.verbose:
            print("🔧 Registering ontology mappings to PREDEFINED_ONTOLOGIES...")
        registered_count = 0
        
        for uri, file_path in self.mappings.items():
            if os.path.exists(file_path):
                abs_path = os.path.abspath(file_path)
                owl.PREDEFINED_ONTOLOGIES[uri] = abs_path
                # if self.verbose:
                #     print(f"   ✅ {uri} -> {abs_path}")
                registered_count += 1
            else:
                print(f"   ⚠️ File does not exist: {uri} -> {file_path}")
        
        if self.verbose:
            print(f"✅ Successfully registered {registered_count} ontology mappings")
    
    def load_ontology(self, ontology_uri: Optional[str] = None, 
                     ontology_file: Optional[str] = None, 
                     world_instance: Optional[owl.World] = None):
        """
        Load ontology file
        
        Args:
            ontology_uri: Ontology URI (if already in mapping)
            ontology_file: Ontology file path (if direct loading needed)
            world_instance: Existing World instance (optional)
        
        Returns:
            Loaded ontology object
        """
        try:
            if ontology_uri:
                if self.verbose:
                    print(f"📄 Loading ontology via URI: {ontology_uri}")
                if world_instance:
                    onto = world_instance.get_ontology(ontology_uri)
                else:
                    onto = owl.get_ontology(ontology_uri)
            elif ontology_file:
                file_uri = f"file://{os.path.abspath(ontology_file)}"
                if self.verbose:
                    print(f"📄 Loading ontology via file: {file_uri}")
                if world_instance:
                    onto = world_instance.get_ontology(file_uri)
                else:
                    onto = owl.get_ontology(file_uri)
            else:
                raise ValueError("Must provide ontology_uri or ontology_file")
            
            onto.load()
            if self.verbose:
                print(f"✅ Ontology loaded successfully: {onto.base_iri}")
            
            # 显示导入的本体
            # if self.verbose and onto.imported_ontologies:
#                print("📦 自动导入的依赖本体:")
#                for imported in onto.imported_ontologies:
#                    print(f"   - {imported.base_iri}")
            
            return onto
            
        except Exception as e:
            print(f"❌ Ontology loading failed: {e}")
            raise
    
    def load_ontology_simple(self, ontology_uri: str = None, ontology_file: str = None):
        """Simplified ontology loading function for backward compatibility"""
        loader = self.get_global_instance()
        world = owl.World()
        
        if ontology_uri:
            if self.verbose:
                print(f"📄 Loading ontology via URI: {ontology_uri}")
            onto = loader.load_ontology(ontology_uri=ontology_uri, world_instance=world)
        elif ontology_file:
            file_uri = f"file://{os.path.abspath(ontology_file)}"
            if self.verbose:
                print(f"📄 Loading ontology via file: {file_uri}")
            onto = loader.load_ontology(ontology_file=ontology_file, world_instance=world)
        else:
            raise ValueError("Must provide ontology_uri or ontology_file")
        
        onto.load()
        return onto
    
    def load_all_ontologies(self, world_instance: Optional[owl.World] = None):
        """
        Load all ontology files into the same world
        
        Args:
            world_instance: Existing World instance, create new one if None
            
        Returns:
            tuple: (world, main_ontology) tuple
        """
        if world_instance is None:
            world = owl.World()
        else:
            world = world_instance
            
        if self.verbose:
            print("📦 Starting to load all ontology files...")
        
        loaded_ontologies = {}
        
        # Load ontologies by priority (load basic ontologies first, then dependent ontologies)
        load_order = [
            # Basic ontologies
            "http://purl.obolibrary.org/obo/bfo.owl",
            "http://purl.obolibrary.org/obo/core/object",
            "http://purl.obolibrary.org/obo/core/material",
            "http://purl.obolibrary.org/obo/core/relation",
            "http://purl.obolibrary.org/obo/core/state",
            "http://purl.obolibrary.org/obo/core/danger",  # Add danger attribute ontology
            # Domain ontologies
            "http://purl.obolibrary.org/obo/domain/material-mappings",
            
            "http://purl.obolibrary.org/obo/domain/kitchen-axioms",
            "http://purl.obolibrary.org/obo/domain/attribute-mappings",
            # Environment ontologies
            "http://purl.obolibrary.org/obo/kitchen-environment"
        ]
        
        for uri in load_order:
            if uri in self.mappings:
                try:
                    if self.verbose:
                        print(f"  📄 Loading: {uri}")
                    onto = world.get_ontology(uri)
                    onto.load()
                    loaded_ontologies[uri] = onto
                    if self.verbose:
                        print(f"    ✅ Success: {onto.base_iri}")
                        
                        # Show imported ontologies
                        if onto.imported_ontologies:
                            print(f"    📦 Imported: {len(onto.imported_ontologies)} ontologies")
                        
                except Exception as e:
                    print(f"    ❌ Failed: {e}")
            else:
                if self.verbose:
                    print(f"  ⚠️ Mapping not found: {uri}")
        
        # Return world and main ontology (kitchen-environment or kitchen-axioms)
        main_onto = None
        if "http://purl.obolibrary.org/obo/kitchen-environment" in loaded_ontologies:
            main_onto = loaded_ontologies["http://purl.obolibrary.org/obo/kitchen-environment"]
        elif "http://purl.obolibrary.org/obo/domain/kitchen-axioms" in loaded_ontologies:
            main_onto = loaded_ontologies["http://purl.obolibrary.org/obo/domain/kitchen-axioms"]
        
        if self.verbose:
            print(f"\n✅ Total loaded {len(loaded_ontologies)} ontologies")
            print(f"🌐 Number of namespaces in World: {len(list(world.ontologies))}")
        
        return world, main_onto
    
    def list_available_ontologies(self):
        """List all available ontology mappings"""
        print("\n📋 Available ontology mapping list:")
        for uri, file_path in self.mappings.items():
            if os.path.exists(file_path):
                print(f"   ✅ {uri}")
            else:
                print(f"   ❌ {uri} (file does not exist)")
    
    def get_available_ontologies(self) -> List[str]:
        """Get list of available ontology URIs"""
        available_ontologies = []
        for uri, file_path in self.mappings.items():
            if os.path.exists(file_path):
                available_ontologies.append(uri)
        return available_ontologies
    
    @classmethod
    def get_global_instance(cls, **kwargs) -> 'OntologyLoader':
        """
        Get global instance
        Create one if global instance doesn't exist
        """
        if cls._global_instance is None:
            cls._global_instance = cls(**kwargs)
        return cls._global_instance
