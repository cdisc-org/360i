"""
Dataset-JSON Generator from Define-XML
========================================

This module processes CDISC Define-XML files and generates Dataset-JSON files
conforming to the CDISC Dataset-JSON v1.1 specification.

It uses XSLT transformations via SaxonC to extract dataset metadata and structure
from Define-XML, then validates and outputs Dataset-JSON files for each dataset.

Key Features:
- Extracts dataset definitions from Define-XML
- Generates Dataset-JSON v1.1 compliant output files
- Schema validation against Dataset-JSON specification
- Command-line interface with configurable options
- Debug mode for troubleshooting
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from jsonschema import validate, ValidationError
from saxonche import PySaxonProcessor


class DatasetJSONGenerator:
    """
    Generator for Dataset-JSON files from Define-XML.
    
    This class processes CDISC Define-XML files and generates Dataset-JSON files
    for each dataset defined in the Define-XML using XSLT transformations.
    
    Attributes:
        define_file (str): Path to input Define-XML file
        output_dir (str): Directory for output Dataset-JSON files
        debug (bool): Enable debug mode with verbose output
        processor (PySaxonProcessor): Saxon XSLT processor instance
        schema (dict): Loaded Dataset-JSON schema
    """
    
    # Constants for schema and XSLT files
    SCHEMA_FILE = "dataset.schema.json"
    XSL_EXTRACT_FILE = "extract-list-ds.xsl"
    XSL_TRANSFORM_FILE = "transform-to-ds-json.xsl"
    
    def __init__(self, define_file, output_dir=None, debug=False):
        """
        Initialize the Dataset-JSON generator.
        
        Args:
            define_file (str): Path to Define-XML file
            output_dir (str, optional): Output directory for Dataset-JSON files
            debug (bool): Enable debug mode (default: False)
            
        Raises:
            FileNotFoundError: If required input files are not found
        """
        self.define_file = define_file
        self.output_dir = output_dir or os.path.dirname(define_file) or "."
        self.debug = debug
        
        # Validate input files exist
        self._validate_input_files()
        
        # Initialize Saxon processor
        self.processor = PySaxonProcessor(license=False)
        
        # Load schema
        self.schema = self._load_schema()
        
        # Statistics
        self.datasets_processed = 0
        self.datasets_failed = 0
        self.validation_errors = []

    def _validate_input_files(self):
        """
        Validate that all required input files exist.
        
        Raises:
            FileNotFoundError: If any required file is missing
        """
        required_files = {
            "Define-XML file": self.define_file,
            "Schema file": self.SCHEMA_FILE,
            "Extract XSL file": self.XSL_EXTRACT_FILE,
            "Transform XSL file": self.XSL_TRANSFORM_FILE
        }
        
        missing_files = []
        for file_type, file_path in required_files.items():
            if not os.path.exists(file_path):
                missing_files.append(f"{file_type}: {file_path}")
        
        if missing_files:
            raise FileNotFoundError(
                f"Required files not found:\n" + "\n".join(f"  - {f}" for f in missing_files)
            )

    def _load_schema(self):
        """
        Load and parse the Dataset-JSON schema file.
        
        Returns:
            dict: Parsed JSON schema
            
        Raises:
            json.JSONDecodeError: If schema file is invalid JSON
        """
        try:
            with open(self.SCHEMA_FILE, "r", encoding="utf-8") as f:
                schema = json.load(f)
            
            if self.debug:
                print(f"✓ Loaded schema from: {self.SCHEMA_FILE}")
            
            return schema
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in schema file {self.SCHEMA_FILE}: {e.msg}",
                e.doc, e.pos
            )

    def _extract_dataset_list(self):
        """
        Extract list of dataset names from Define-XML.
        
        Returns:
            list: List of dataset names
            
        Raises:
            Exception: If XSLT transformation fails
        """
        try:
            executable = self.processor.new_xslt30_processor().compile_stylesheet(
                stylesheet_file=self.XSL_EXTRACT_FILE
            )
            
            result = executable.transform_to_string(
                xdm_node=self.processor.parse_xml(xml_file_name=self.define_file)
            )
            
            datasets = [ds.strip() for ds in result.split(",") if ds.strip()]
            
            if self.debug:
                print(f"\n✓ Extracted {len(datasets)} datasets: {', '.join(datasets)}")
            
            return datasets
            
        except Exception as e:
            raise Exception(f"Failed to extract dataset list: {str(e)}")

    def _generate_dataset_json(self, dataset_name):
        """
        Generate Dataset-JSON for a single dataset.
        
        Args:
            dataset_name (str): Name of the dataset to generate
            
        Returns:
            dict: Generated Dataset-JSON data, or None if generation failed
        """
        try:
            executable_ds = self.processor.new_xslt30_processor().compile_stylesheet(
                stylesheet_file=self.XSL_TRANSFORM_FILE
            )
            
            executable_ds.set_parameter("dsName", self.processor.make_string_value(dataset_name))
            executable_ds.set_parameter(
                "datasetJSONCreationDateTime",
                self.processor.make_string_value(datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
            )
            
            result = executable_ds.transform_to_string(
                xdm_node=self.processor.parse_xml(xml_file_name=self.define_file)
            )
            
            json_data = json.loads(result)
            
            if self.debug:
                print(f"  ✓ Generated JSON for dataset: {dataset_name}")
            
            return json_data
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON decode error for {dataset_name}: {e.msg}")
            return None
        except Exception as e:
            print(f"  ✗ Failed to generate JSON for {dataset_name}: {str(e)}")
            return None

    def _validate_dataset_json(self, dataset_name, json_data):
        """
        Validate Dataset-JSON against schema.
        
        Args:
            dataset_name (str): Name of the dataset
            json_data (dict): Dataset-JSON data to validate
            
        Returns:
            bool: True if validation passed, False otherwise
        """
        try:
            validate(json_data, self.schema)
            
            if self.debug:
                print(f"  ✓ Validation passed for: {dataset_name}")
            
            return True
            
        except ValidationError as e:
            error_msg = f"{dataset_name}: {e.message}"
            self.validation_errors.append(error_msg)
            print(f"  ✗ Validation failed for {dataset_name}: {e.message}")
            
            if self.debug and e.path:
                print(f"    Path: {' > '.join(str(p) for p in e.path)}")
            
            return False

    def _save_dataset_json(self, dataset_name, json_data):
        """
        Save Dataset-JSON to file.
        
        Args:
            dataset_name (str): Name of the dataset
            json_data (dict): Dataset-JSON data to save
            
        Returns:
            str: Path to saved file, or None if save failed
        """
        try:
            output_path = os.path.join(self.output_dir, f"{dataset_name}.json")
            
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            
            if self.debug:
                print(f"  ✓ Saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"  ✗ Failed to save {dataset_name}.json: {str(e)}")
            return None

    def process(self):
        """
        Main processing method to generate all Dataset-JSON files.
        
        Execution flow:
        1. Extract dataset list from Define-XML
        2. For each dataset:
           - Generate Dataset-JSON
           - Validate against schema
           - Save to output file
        3. Print summary statistics
        
        Returns:
            bool: True if all datasets processed successfully, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Dataset-JSON Generator")
        print(f"{'='*70}")
        print(f"Input Define-XML: {self.define_file}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*70}\n")
        
        try:
            # Extract dataset list
            datasets = self._extract_dataset_list()
            
            if not datasets:
                print("⚠ No datasets found in Define-XML file")
                return False
            
            # Process each dataset
            print(f"\nProcessing {len(datasets)} dataset(s)...\n")
            
            for dataset_name in datasets:
                print(f"Processing: {dataset_name}")
                
                # Generate Dataset-JSON
                json_data = self._generate_dataset_json(dataset_name)
                if json_data is None:
                    self.datasets_failed += 1
                    continue
                
                # Validate
                if not self._validate_dataset_json(dataset_name, json_data):
                    self.datasets_failed += 1
                    # Still save even if validation failed
                
                # Save
                output_path = self._save_dataset_json(dataset_name, json_data)
                if output_path:
                    self.datasets_processed += 1
                else:
                    self.datasets_failed += 1
                
                print()  # Blank line between datasets
            
            # Print summary
            self._print_summary()
            
            return self.datasets_failed == 0
            
        except Exception as e:
            print(f"\n✗ Fatal error: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False

    def _print_summary(self):
        """Print processing summary statistics."""
        print(f"\n{'='*70}")
        print(f"Processing Summary")
        print(f"{'='*70}")
        print(f"Total datasets processed: {self.datasets_processed}")
        print(f"Failed datasets: {self.datasets_failed}")
        
        if self.validation_errors:
            print(f"\nValidation Errors ({len(self.validation_errors)}):")
            for error in self.validation_errors:
                print(f"  - {error}")
        
        if self.datasets_failed == 0:
            print(f"\n✅ All datasets processed successfully!")
        else:
            print(f"\n⚠ {self.datasets_failed} dataset(s) failed processing")
        
        print(f"{'='*70}\n")


def main():
    """
    Main entry point for command-line execution.
    
    Parses command-line arguments and orchestrates the Dataset-JSON
    generation process.
    """
    parser = argparse.ArgumentParser(
        description="Generate Dataset-JSON files from CDISC Define-XML.",
        epilog="Example: python create-shells-ds-json.py --define_file define-2-1-ADaM.xml --output_dir output/"
    )
    
    parser.add_argument(
        "--define_file",
        required=True,
        help="Path to Define-XML file"
    )
    parser.add_argument(
        "--output_dir",
        help="Output directory for Dataset-JSON files (default: same as define_file)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        generator = DatasetJSONGenerator(
            define_file=args.define_file,
            output_dir=args.output_dir,
            debug=args.debug
        )
        
        success = generator.process()
        
        # Exit with appropriate code
        exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
