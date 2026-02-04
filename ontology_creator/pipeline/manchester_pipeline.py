#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manchester syntax generation pipeline
Contains complete two-step execution logic: Step1 LLM generation + Step2 vector validation
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import sys
import json
from datetime import datetime

# Add project root directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from pipeline.relation_extractor import RelationExtractor
    from pipeline.manchester_json_validator import ManchesterJSONValidator
    from pipeline.ontology_writer_refactored import write_ontology_from_analysis
    from llm.llm_service import call_llm
except ImportError as e:
    print(f"❌ Module import failed: {e}")
    raise


class ManchesterPipeline:
    """Manchester syntax generation pipeline main class"""
    
    def __init__(self):
        """Initialize pipeline"""
        self.test_output_dir = Path("test_output")
        self.test_output_dir.mkdir(exist_ok=True)
        
        print("🏗️ Initializing Manchester syntax generation pipeline")
        print(f"📁 Output directory: {self.test_output_dir.absolute()}")
    
    def step1_generate_json(self, hazard_description: str) -> str:
        """
        Step 1: Use LLM to generate Manchester JSON and save to file
        
        Args:
            hazard_description: Hazard description text
            
        Returns:
            Saved file path
        """
        print(f"\n🎯 Step 1: LLM generates Manchester JSON")
        print(f"📝 Input: {hazard_description}")
        
        try:
            # Initialize relation extractor
            relation_extractor = RelationExtractor()
            
            # Get spatial relations and attribute relations
            spatial_relations = relation_extractor.get_spatial_relations()
            attribute_relations = ['hasMaterial', 'hasState', 'hasProperty']
            
            # Build prompt data
            prompt_data = {
                'text': hazard_description,
                'spatial_relations': spatial_relations,
                'attribute_relations': attribute_relations,
                'example_input': "Keep plastic containers away from hot surfaces to prevent melting.",
                'example_output': self._get_example_output()
            }
            
            # Call LLM to generate JSON
            manchester_json = call_llm('manchester_generation', **prompt_data)
            
            if not manchester_json:
                raise Exception("LLM did not return valid response")
            
            # Save to file
            filepath = self._save_json_result(hazard_description, manchester_json)
            
            print(f"✅ Step 1 completed")
            print(f"📄 JSON saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Step 1 failed: {e}")
            raise
    
    def step2_validate_json(self, json_filepath: str = None, debug: bool = False) -> Dict[str, Any]:
        """
        Step 2: Vector validation of saved JSON file
        
        Args:
            json_filepath: JSON file path, if None validate the latest file
            debug: Whether to enable debug mode, showing detailed vector matching information
            
        Returns:
            Validation results
        """
        print(f"\n🔍 Step 2: Vector validation of JSON")
        
        try:
            # Determine file to validate
            json_filepath = self._get_json_filepath(json_filepath)
            
            # Read JSON data
            manchester_json, input_description = self._load_json_data(json_filepath)
            
            print(f"📝 Input description: {input_description}")
            
            # Execute vector validation
            validator = ManchesterJSONValidator()
            validation_report = validator.validate_manchester_json(manchester_json, debug=debug)
            
            # Save validation results
            validation_filepath = self._save_validation_result(json_filepath, validation_report)
            
            print(f"✅ Step 2 completed")
            print(f"📄 Validation report saved: {validation_filepath}")
            
            # Return complete results including file path
            return {
                **validation_report,
                "filepath": validation_filepath
            }
            
        except Exception as e:
            print(f"❌ Step 2 failed: {e}")
            raise
    
    def step3_analyze_hierarchy(self, validation_report_path: str = None, debug: bool = False) -> Dict[str, Any]:
        """
        Step 3: Hierarchy structure analysis
        
        Args:
            validation_report_path: Validation report file path, if None analyze the latest report
            debug: Whether to enable debug mode
            
        Returns:
            Hierarchy structure analysis results
        """
        print(f"\n🌳 Step 3: Hierarchy structure analysis")
        
        try:
            # Import hierarchy analyzer
            from pipeline.hierarchy_analyzer import HierarchyAnalyzer
            
            # If no validation report path specified, find the latest one
            if validation_report_path is None:
                validation_report_path = self._find_latest_validation_report()
            
            print(f"📋 Analyzing validation report: {validation_report_path}")
            
            # Execute hierarchy analysis
            analyzer = HierarchyAnalyzer()
            analysis_result = analyzer.analyze_missing_items(validation_report_path, debug=debug)
            
            # Save analysis results
            analysis_filepath = self._save_hierarchy_analysis(validation_report_path, analysis_result)
            
            print(f"✅ Step 3 completed")
            print(f"📄 Hierarchy analysis report saved: {analysis_filepath}")
            
            return analysis_filepath
            
        except Exception as e:
            print(f"❌ Step 3 failed: {e}")
            raise
    
    def run_all_steps(self, hazard_description: str) -> Dict[str, Any]:
        """
        Execute complete four-step process
        
        Args:
            hazard_description: Hazard description text
            
        Returns:
            Complete results
        """
        print(f"\n🚀 Execute complete four-step process (1→2→3→4)")
        print(f"📝 Input: {hazard_description}")
        
        try:
            # Step 1: Generate JSON
            print(f"\n🎯 Step 1: LLM generates Manchester JSON")
            json_filepath = self.step1_generate_json(hazard_description)
            
            # Step 2: Validate JSON
            print(f"\n🔍 Step 2: Vector validation")
            validation_report = self.step2_validate_json(json_filepath)
            
            # Step 3: Hierarchy analysis
            print(f"\n🌳 Step 3: Hierarchy structure analysis")
            hierarchy_filepath = self.step3_analyze_hierarchy(validation_report['filepath'])
            
            # Step 4: Ontology writing
            print(f"\n📝 Step 4: Ontology writing")
            ontology_result = self.step4_write_ontology()
            
            print(f"\n✅ Complete four-step process executed successfully!")
            
            # Generate detailed report
            summary = ontology_result.get('summary', {})
            print(f"\n📊 Final results summary:")
            print(f"   - JSON file: {Path(json_filepath).name}")
            print(f"   - Validation report: {Path(validation_report['filepath']).name}")
            print(f"   - Hierarchy analysis: {Path(hierarchy_filepath).name}")
            print(f"   - Classes written: {summary.get('total_classes_written', 0)}")
            print(f"   - Rules written: {summary.get('total_rules_written', 0)}")
            print(f"   - Reasoning validation: {'✅ Passed' if summary.get('reasoning_passed') else '⚠️ Skipped or failed'}")
            
            return {
                "success": True,
                "json_filepath": json_filepath,
                "validation_report": validation_report,
                "hierarchy_filepath": hierarchy_filepath,
                "ontology_result": ontology_result,
                "summary": {
                    "total_steps": 4,
                    "classes_written": summary.get('total_classes_written', 0),
                    "rules_written": summary.get('total_rules_written', 0),
                    "reasoning_passed": summary.get('reasoning_passed', False)
                }
            }
            
        except Exception as e:
            print(f"❌ Complete process execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_saved_files(self):
        """List saved files"""
        json_files = list(self.test_output_dir.glob("manchester_json_*.json"))
        validation_files = list(self.test_output_dir.glob("validation_report_*.json"))
        
        print(f"\n📁 Files in test_output directory:")
        print(f"📄 JSON files ({len(json_files)} items):")
        for f in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True):
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"   - {f.name} ({mtime})")
            
        print(f"🔍 Validation reports ({len(validation_files)} items):")
        for f in sorted(validation_files, key=lambda x: x.stat().st_mtime, reverse=True):
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"   - {f.name} ({mtime})")
    
    def _get_example_output(self) -> str:
        """Get example output"""
        return '''{
"objects": [
  {"class": "Container", "subclassOf": "PhysicalObject"},
  {"class": "PlasticContainer", "subclassOf": "Container"},
  {"class": "HotSurface", "subclassOf": "PhysicalObject"}
],
"materials": [
  {"class": "Plastic", "attributeRelation": "hasMaterial"}
],
"attributes": [
  {"class": "Hot", "attributeRelation": "hasState"}
],
"states": [],
"dangers": [
  {"class": "MeltingHazard", "subclassOf": "HazardousSituation"}
],
"spatialRelations": [
  {"objectProperty": "isNear", "domain": "Container", "range": "HotSurface"}
],
"attributeRelations": [
  {"objectProperty": "hasMaterial", "domain": "Container", "range": "Plastic"},
  {"objectProperty": "hasState", "domain": "HotSurface", "range": "Hot"}
],
"propertyChains": [
  {
    "equivalentClass": "MeltingHazard",
    "definition": "PlasticContainer and (isNear some (HotSurface and (hasState some Hot)))"
  }
]
}'''
    
    def _save_json_result(self, hazard_description: str, manchester_json: str) -> Path:
        """Save JSON result to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manchester_json_{timestamp}.json"
        filepath = self.test_output_dir / filename
        
        result_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "input_description": hazard_description,
                "filename": filename
            },
            "manchester_json": manchester_json,
            "raw_response": manchester_json
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def _get_json_filepath(self, json_filepath: str = None) -> Path:
        """Get JSON file path to validate"""
        if json_filepath is None:
            # Find latest JSON file
            json_files = list(self.test_output_dir.glob("manchester_json_*.json"))
            if not json_files:
                raise Exception("No JSON files found in test_output directory")
            json_filepath = max(json_files, key=lambda x: x.stat().st_mtime)
            print(f"📄 Automatically selected latest file: {json_filepath.name}")
        else:
            json_filepath = Path(json_filepath)
            
        if not json_filepath.exists():
            raise Exception(f"File does not exist: {json_filepath}")
            
        return json_filepath
    
    def _load_json_data(self, json_filepath: str) -> Tuple[dict, str]:
        """Load JSON data"""
        with open(json_filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        manchester_json = saved_data.get("manchester_json", "")
        if not manchester_json:
            raise Exception("manchester_json data not found in JSON file")
        
        input_description = saved_data.get('metadata', {}).get('input_description', 'Unknown')
        
        return manchester_json, input_description
    
    def _save_validation_result(self, json_filepath: Path, validation_report: Dict[str, Any]) -> Path:
        """Save validation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        validation_filename = f"validation_report_{timestamp}.json"
        validation_filepath = self.test_output_dir / validation_filename
        
        validation_data = {
            "metadata": {
                "validated_at": datetime.now().isoformat(),
                "source_file": str(json_filepath),
                "validation_filename": validation_filename
            },
            "validation_report": validation_report
        }
        
        with open(validation_filepath, 'w', encoding='utf-8') as f:
            json.dump(validation_data, f, ensure_ascii=False, indent=2)
        
        return validation_filepath
    
    def _find_latest_validation_report(self) -> str:
        """Find latest validation report file"""
        validation_files = list(self.test_output_dir.glob("validation_report_*.json"))
        if not validation_files:
            raise FileNotFoundError("No validation report files found in test_output directory")
        
        # Sort by modification time, return latest
        latest_file = max(validation_files, key=lambda p: p.stat().st_mtime)
        return str(latest_file)
    
    def _save_hierarchy_analysis(self, validation_report_path: str, analysis_result: Dict[str, Any]) -> str:
        """Save hierarchy analysis results"""
        # Generate analysis result filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_filename = f"hierarchy_analysis_{timestamp}.json"
        analysis_filepath = self.test_output_dir / analysis_filename
        
        # Recursively convert Path objects to strings to ensure JSON serializability
        def convert_paths_to_strings(obj, path="root", debug_print=False):
            """Recursively convert all Path objects and other non-serializable objects to strings"""
            import os
            from pathlib import Path
            
            # First check if it's a Path or Path-like object (including all subclasses)
            try:
                # Check all possible Path types - broader detection
                if isinstance(obj, os.PathLike) or hasattr(obj, '__fspath__'):
                    if debug_print:
                        print(f"🔍 [DEBUG] Found PathLike object at {path}: {type(obj)} = {obj}")
                    return str(obj)
                elif 'Path' in str(type(obj).__name__):  # Type name contains Path
                    if debug_print:
                        print(f"🔍 [DEBUG] Found Path type object at {path}: {type(obj)} = {obj}")
                    return str(obj)
                elif isinstance(obj, Path):  # Standard pathlib.Path check
                    if debug_print:
                        print(f"🔍 [DEBUG] Found Path object at {path}: {type(obj)} = {obj}")
                    return str(obj)
            except Exception:
                pass
            
            if isinstance(obj, dict):
                return {k: convert_paths_to_strings(v, f"{path}.{k}", debug_print) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_paths_to_strings(item, f"{path}[{i}]", debug_print) for i, item in enumerate(obj)]
            elif isinstance(obj, set):
                return list(convert_paths_to_strings(list(obj), f"{path}[set]", debug_print))
            else:
                # Finally try to serialize, if it fails convert to string
                try:
                    import json
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError) as e:
                    if debug_print:
                        print(f"🔍 [DEBUG] Serialization failed at {path}: {type(obj)} = {obj}, error: {e}")
                    # For all non-serializable objects, convert to string
                    return str(obj)
        
        # Save analysis results
        analysis_data = {
            "metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "source_validation_report": str(validation_report_path),
                "analysis_filename": analysis_filename
            },
            "analysis_result": convert_paths_to_strings(analysis_result, debug_print=True)
        }
        
        with open(analysis_filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        return str(analysis_filepath)
    
    def step4_write_ontology(self, analysis_file: str = None, debug: bool = False) -> Dict[str, Any]:
        """
        Step 4: Ontology writing
        
        Args:
            analysis_file: Hierarchy analysis file path, if not provided use latest
            debug: Debug mode
            
        Returns:
            Write result dictionary
        """
        print(f"\n📝 Step 4: Ontology writing")
        
        try:
            if analysis_file is None:
                analysis_file = self._find_latest_hierarchy_analysis()
                print(f"📄 Using latest hierarchy analysis file: {Path(analysis_file).name}")
            
            print(f"📖 Loading analysis file: {analysis_file}")
            
            # Call ontology writer
            result = write_ontology_from_analysis(analysis_file, debug)
            
            print(f"✅ Step 4 completed")
            return result
            
        except Exception as e:
            error_msg = f"Step 4 execution failed: {e}"
            print(f"❌ {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "generated_at": datetime.now().isoformat()
            }
    
    def _find_latest_hierarchy_analysis(self) -> str:
        """Find latest hierarchy analysis file"""
        analysis_files = list(self.test_output_dir.glob("hierarchy_analysis_*.json"))
        if not analysis_files:
            raise FileNotFoundError("No hierarchy analysis files found in test_output directory")
        
        # Sort by modification time, return latest
        latest_file = max(analysis_files, key=lambda p: p.stat().st_mtime)
        return str(latest_file)


if __name__ == "__main__":
    # Test module
    pipeline = ManchesterPipeline()
    test_description = "Store sharp utensils like kitchen shears and knives safely to prevent harm."
    
    print("🧪 Testing ManchesterPipeline module")
    result = pipeline.run_all_steps(test_description)
    
    if result['success']:
        print("✅ Test successful")
    else:
        print(f"❌ Test failed: {result['error']}")
