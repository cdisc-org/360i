# DM Domain Implementation - CDISC SDTM Code Generator

This directory contains a complete implementation for generating CDISC SDTM Demographics (DM) domain datasets from raw CDASH data using automated code generation.

## Overview

The DM domain code generator creates SDTM demographics datasets from raw demographic data. DM is a special domain with exactly one record per subject, containing baseline demographic characteristics collected at study entry.

## Files in this Directory

### Core Generator Files
- **`emit_demographics_oak_from_spec.R`** - Main code generator for DM domain
- **`generate_dm_dataset.R`** - Simplified dataset generator (recommended)

### Generated Output
- **`new dm code.R`** - Generated SDTM mapping code (178+ lines)
- **`DM_from_sdtm_oak_codegen.csv`** - Final SDTM DM dataset (CSV format)
- **`DM_from_sdtm_oak_codegen.xpt`** - Final SDTM DM dataset (XPT format)

### Input Data
- **`DM.csv`** - Raw CDISC pilot study demographics data (306 subjects)
- **`study_ct.csv`** - Study controlled terminology
- **`cdisc_collection_dataset_specializations_draft.xlsx`** - CDISC specifications

## Quick Start

### Option 1: Generate SDTM Dataset Directly (Recommended)

```r
# Set working directory
setwd("/path/to/DM domain implementation")

# Run the simplified generator
source("generate_dm_dataset.R")
```

This will create:
- `DM_from_sdtm_oak_codegen.csv` - SDTM DM dataset in CSV format
- `DM_from_sdtm_oak_codegen.xpt` - SDTM DM dataset in XPT format

### Option 2: Generate R Code First, Then Execute

```r
# Set working directory
setwd("/path/to/DM domain implementation")

# Generate the mapping code
source("emit_demographics_oak_from_spec.R")

# Execute the generated code (Note: may require sdtm.oak package)
source("new dm code.R")
```

## Prerequisites

### Required R Packages
```r
install.packages(c("dplyr", "readxl", "haven"))
```

### Optional Package (for oak-based generation)
```r
# Only needed if using emit_demographics_oak_from_spec.R
install.packages("sdtm.oak")
```

## Input Data Requirements

### Raw DM Data (`DM.csv`)
Expected columns include:
- **Subject identifiers**: STUDYID, SUBJID, SITEID
- **Demographics**: AGE, AGEU, SEX, RACE, ETHNIC, COUNTRY
- **Collection date**: DMDAT (DD-MMM-YYYY format)

### Date Format
Dates should be in DD-MMM-YYYY format (e.g., "26-DEC-2013")

## Output

### Generated SDTM DM Dataset
The output contains 18 SDTM variables:
- **Core identifiers**: STUDYID, DOMAIN, USUBJID, SUBJID, SITEID
- **Demographics**: AGE, AGEU, SEX, RACE, ETHNIC, COUNTRY
- **Collection date**: DMDTC (ISO format)
- **Reference dates**: RFSTDTC, RFENDTC, RFXSTDTC, RFXENDTC
- **Treatment arms**: ARM, ACTARM

### Key Transformations
1. **USUBJID creation**: STUDYID-SUBJID format
2. **Date standardization**: DD-MMM-YYYY → YYYY-MM-DD (ISO 8601)
3. **Race handling**: Extracts primary race if multiple values (e.g., "CA,HP" → "CA")
4. **Domain assignment**: DOMAIN = "DM"
5. **Reference dates**: Placeholders for study-specific dates

## Example Usage

### Basic Execution
```r
# Navigate to the directory
setwd("/Users/siddharthlokineni/Documents/Oak implementation/DM domain implementation")

# Generate SDTM datasets
source("generate_dm_dataset.R")

# Check results
dm_data <- read.csv("DM_from_sdtm_oak_codegen.csv")
cat("Generated", nrow(dm_data), "subject records\n")
```

### Customizing for Your Data
To use with your own DM data:

1. **Replace input files**:
   - Update `DM.csv` with your raw demographics data
   - Update `study_ct.csv` with your controlled terminology
   - Update specifications file if needed

2. **Modify column mappings** in `generate_dm_dataset.R` if your column names differ

3. **Update date formats** if your dates use a different format

4. **Add reference dates** if you have actual study reference dates

## Validation Results

This implementation has been tested with CDISC pilot study data:
- **Input**: 306 subjects with demographics
- **Output**: Complete SDTM DM dataset with proper variable mappings
- **Date range**: 2012-07-06 to 2014-08-29
- **Demographics**:
  - Age: 50-89 years (mean 75.1)
  - Sex: 179 Female, 127 Male
  - Race: 273 Caucasian, 29 African American, 2 East Asian, 2 Other
  - Ethnicity: 289 Not Hispanic/Latino, 17 Hispanic/Latino

## Domain-Specific Considerations

### DM Domain Characteristics
- **One record per subject**: Unlike Events or Findings domains
- **Baseline data**: Collected at study entry
- **Reference anchor**: Used for calculating study days in other domains
- **Required variables**: STUDYID, DOMAIN, USUBJID are mandatory

### Reference Dates
The DM domain typically contains key reference dates:
- **RFSTDTC**: Reference start date (first exposure)
- **RFENDTC**: Reference end date (last exposure/follow-up)
- **RFXSTDTC**: First exposure to study treatment
- **RFXENDTC**: Last exposure to study treatment

*Note: In this implementation, reference dates are set as placeholders and should be populated with actual study-specific dates.*

## Troubleshooting

### Common Issues

1. **Package not found errors**:
   ```r
   install.packages(c("dplyr", "readxl", "haven"))
   ```

2. **Date parsing errors**:
   - Ensure dates are in DD-MMM-YYYY format
   - Check for missing or malformed date values

3. **Multiple race values**:
   - Current implementation takes the first race code
   - Modify race handling logic if different approach needed

4. **Missing demographics**:
   - Check that all expected demographic variables are present
   - Update column mappings in the generator script

### Getting Help

If you encounter issues:
1. Check that all input files are present and readable
2. Verify R package dependencies are installed
3. Review the console output for specific error messages
4. Consider using the simplified `generate_dm_dataset.R` approach

## File Sizes

Typical file sizes with CDISC pilot data:
- Input DM.csv: ~23KB (306 subjects)
- Output CSV: ~40KB
- Output XPT: ~35KB

## Next Steps

After generating your SDTM DM dataset:
1. **Populate reference dates** with actual study dates
2. **Add treatment arms** (ARM, ACTARM) if available
3. **Validate** demographics against source data
4. **Use as reference** for other domain study day calculations
5. **Integrate** into your clinical data pipeline

## Integration with Other Domains

The DM dataset serves as the foundation for other SDTM domains:
- **Subject identifiers**: USUBJID used across all domains
- **Reference dates**: Used for calculating study days (--DY variables)
- **Demographics**: Used for population analysis and reporting

---

**Generated by**: CDISC 360I SDTM Oak Code Generator
**Version**: 1.0
**Compatible with**: CDISC SDTM v1.4+