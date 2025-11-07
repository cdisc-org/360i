# AE Domain Implementation - CDISC SDTM Code Generator

This directory contains a complete implementation for generating CDISC SDTM Adverse Events (AE) domain datasets from raw CDASH data using automated code generation.

## Overview

The AE domain code generator follows the same validated pattern as the VS (Vital Signs) domain, adapted specifically for Events domains. It processes real CDISC pilot study data and generates production-ready SDTM AE datasets.

## Files in this Directory

### Core Generator Files
- **`emit_events_oak_from_spec.R`** - Main code generator for AE domain
- **`generate_ae_dataset.R`** - Simplified dataset generator (recommended)
- **`run_ae_generation.R`** - Test script for code generation

### Generated Output
- **`new ae code.R`** - Generated SDTM mapping code (266+ lines)
- **`AE_from_sdtm_oak_codegen.csv`** - Final SDTM AE dataset (CSV format)
- **`AE_from_sdtm_oak_codegen.xpt`** - Final SDTM AE dataset (XPT format)

### Input Data
- **`AE.csv`** - Raw CDISC pilot study AE data (1,272 records, 306 subjects)
- **`study_ct.csv`** - Study controlled terminology
- **`cdisc_collection_dataset_specializations_draft.xlsx`** - CDISC specifications

## Quick Start

### Option 1: Generate SDTM Dataset Directly (Recommended)

```r
# Set working directory
setwd("/path/to/AE domain implementation")

# Run the simplified generator
source("generate_ae_dataset.R")
```

This will create:
- `AE_from_sdtm_oak_codegen.csv` - SDTM AE dataset in CSV format
- `AE_from_sdtm_oak_codegen.xpt` - SDTM AE dataset in XPT format

### Option 2: Generate R Code First, Then Execute

```r
# Set working directory
setwd("/path/to/AE domain implementation")

# Generate the mapping code
source("emit_events_oak_from_spec.R")

# Execute the generated code (Note: may require sdtm.oak package)
source("new ae code.R")
```

## Prerequisites

### Required R Packages
```r
install.packages(c("dplyr", "readxl", "haven"))
```

### Optional Package (for oak-based generation)
```r
# Only needed if using emit_events_oak_from_spec.R
install.packages("sdtm.oak")
```

## Input Data Requirements

### Raw AE Data (`AE.csv`)
Expected columns include:
- **Subject identifiers**: STUDYID, SUBJID
- **AE terms**: AETERM, AEDECOD, AESOC
- **MedDRA hierarchy**: AELLT, AEHLT, AEHLGT, AESOCCD, etc.
- **Assessments**: AESEV (1=MILD, 2=MODERATE, 3=SEVERE), AESER, AEREL, AEACN, AEOUT
- **Dates**: AESTDAT, AEENDAT (DD-MMM-YYYY format)
- **Other**: AEYN, AESPID, AEONGO

### Date Format
Dates should be in DD-MMM-YYYY format (e.g., "09-JAN-2014")

## Output

### Generated SDTM AE Dataset
The output contains 26 SDTM variables:
- **Core identifiers**: STUDYID, DOMAIN, USUBJID, AESEQ
- **AE terms**: AETERM, AEDECOD, AEBODSYS
- **Assessments**: AESEV, AESER, AEREL, AEACN, AEOUT
- **Dates**: AESTDTC, AEENDTC, AEDY
- **MedDRA hierarchy**: AELLT, AELLTCD, AEHLT, AEHLTCD, AEHLGT, AEHLGTCD, AESOCCD, AEPTCD
- **AE-specific**: AEYN, AESPID, AEONGO
- **Visit**: VISITNUM, VISIT

### Key Transformations
1. **AESOC → AEBODSYS**: System Organ Class mapping
2. **Severity conversion**: 1→MILD, 2→MODERATE, 3→SEVERE
3. **Date standardization**: DD-MMM-YYYY → YYYY-MM-DD (ISO 8601)
4. **USUBJID creation**: STUDYID-SUBJID format
5. **Sequence numbering**: AESEQ within subject

## Example Usage

### Basic Execution
```r
# Navigate to the directory
setwd("/Users/siddharthlokineni/Documents/Oak implementation/AE domain implementation")

# Generate SDTM datasets
source("generate_ae_dataset.R")

# Check results
ae_data <- read.csv("AE_from_sdtm_oak_codegen.csv")
cat("Generated", nrow(ae_data), "AE records for", length(unique(ae_data$USUBJID)), "subjects\n")
```

### Customizing for Your Data
To use with your own AE data:

1. **Replace input files**:
   - Update `AE.csv` with your raw AE data
   - Update `study_ct.csv` with your controlled terminology
   - Update specifications file if needed

2. **Modify column mappings** in `generate_ae_dataset.R` if your column names differ

3. **Update date formats** if your dates use a different format

## Validation Results

This implementation has been tested with CDISC pilot study data:
- **Input**: 1,272 AE records from 306 subjects
- **Output**: Complete SDTM AE dataset with proper variable mappings
- **Date range**: 2011-12-05 to 2014-11-03
- **Quality**: All required SDTM variables present with proper data types

## Troubleshooting

### Common Issues

1. **Package not found errors**:
   ```r
   install.packages(c("dplyr", "readxl", "haven"))
   ```

2. **Date parsing errors**:
   - Ensure dates are in DD-MMM-YYYY format
   - Check for missing or malformed date values

3. **Column not found errors**:
   - Verify your AE.csv has the expected column names
   - Update column mappings in the generator script

4. **sdtm.oak package issues**:
   - Use `generate_ae_dataset.R` instead (recommended)
   - This version doesn't require sdtm.oak package

### Getting Help

If you encounter issues:
1. Check that all input files are present and readable
2. Verify R package dependencies are installed
3. Review the console output for specific error messages
4. Consider using the simplified `generate_ae_dataset.R` approach

## File Sizes

Typical file sizes with CDISC pilot data:
- Input AE.csv: ~260KB (1,272 records)
- Output CSV: ~315KB
- Output XPT: ~495KB

## Next Steps

After generating your SDTM AE dataset:
1. **Validate** the output against CDISC standards
2. **Review** variable mappings for correctness
3. **Test** with your study's data validation rules
4. **Integrate** into your clinical data pipeline

---

**Generated by**: CDISC 360I SDTM Oak Code Generator
**Version**: 1.0
**Compatible with**: CDISC SDTM v1.4+