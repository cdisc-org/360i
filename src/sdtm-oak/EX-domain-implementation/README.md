# EX Domain Implementation - CDISC SDTM Code Generator

This directory contains a complete implementation for generating CDISC SDTM Exposure (EX) domain datasets from raw exposure data using the sdtm.oak package methodology.

## Overview

The EX domain captures information about study treatments administered to subjects. It is an Interventions domain that documents the exposure to study drugs, including dosing information, timing, and route of administration. This implementation processes CDISC pilot study data and generates production-ready SDTM EX datasets.

## Files in this Directory

### Core Generator Files
- **`emit_exposure_oak_from_spec.R`** - Main code generator for EX domain
- **`EX.R`** - Generated SDTM mapping code (111 lines)

### Input Data
- **`EX.csv`** - Raw exposure data (591 records, 254 subjects)
- **`study_ct.csv`** - Study controlled terminology
- **`cdisc_collection_dataset_specializations_draft.xlsx`** - CDISC specifications

### Generated Output
- **`EX_from_sdtm_oak_codegen.csv`** - Final SDTM EX dataset (CSV format, 83KB)
- **`EX_from_sdtm_oak_codegen.xpt`** - Final SDTM EX dataset (XPT format, 79KB)

## Data Source

**Raw Data**: `EX.csv` from raw_data directory
**Domain Type**: Interventions
**SDTM Class**: Interventions
**CDISC SDTM Version**: 1.4+

## Quick Start

### Option 1: Generate SDTM Dataset Directly (Recommended)

```r
# Set working directory
setwd("/path/to/ROAK validation/EX domain implementation")

# Run the generated mapping code
source("EX.R")
```

This will create:
- `EX_from_sdtm_oak_codegen.csv` - SDTM EX dataset in CSV format
- `EX_from_sdtm_oak_codegen.xpt` - SDTM EX dataset in XPT format

### Option 2: Regenerate Code First, Then Execute

```r
# Set working directory
setwd("/path/to/ROAK validation/EX domain implementation")

# Generate the mapping code
source("emit_exposure_oak_from_spec.R")

# Execute the generated code
source("EX.R")
```

## Prerequisites

### Required R Packages
```r
install.packages(c("sdtm.oak", "dplyr", "readxl", "haven"))
```

## Input Data Requirements

### Raw EX Data (`EX.csv`)
Expected columns include:
- **Subject identifiers**: STUDYID, SITEID, SUBJID
- **Treatment**: EXTRT (e.g., "PLACEBO", "XANOMELINE")
- **Dosing**: EXDSTXT (dose text), EXDOSU (dose units)
- **Formulation**: EXDOSFRM (dose form), EXDOSFRQ (frequency), EXROUTE (route)
- **Dates**: EXSTDAT, EXENDAT (DD-MMM-YYYY format)
- **Visit**: VISIT

### Date Format
Dates should be in DD-MMM-YYYY format (e.g., "02-JAN-2014")

## Output

### Generated SDTM EX Dataset
The output contains 16 SDTM variables:

#### Core Identifiers (4 variables)
- **STUDYID** - Study Identifier
- **DOMAIN** - Domain Abbreviation (EX)
- **USUBJID** - Unique Subject Identifier (format: STUDYID-SUBJID)
- **EXSEQ** - Sequence Number (within subject)

#### Treatment Information (6 variables)
- **EXTRT** - Name of Treatment (PLACEBO, XANOMELINE)
- **EXDOSE** - Dose per Administration (numeric, converted from EXDSTXT)
- **EXDOSU** - Dose Units (e.g., mg)
- **EXDOSFRM** - Dose Form (e.g., PATCH)
- **EXDOSFRQ** - Dosing Frequency per Interval (e.g., QD)
- **EXROUTE** - Route of Administration (e.g., TRANSDERMAL)

#### Timing Variables (5 variables)
- **EXSTDTC** - Start Date/Time of Treatment (ISO 8601: YYYY-MM-DD)
- **EXENDTC** - End Date/Time of Treatment (ISO 8601: YYYY-MM-DD)
- **EXDTC** - Date/Time of Collection (ISO 8601: YYYY-MM-DD)
- **EXSTDY** - Study Day of Start of Treatment (placeholder)
- **EXENDY** - Study Day of End of Treatment (placeholder)

#### Additional Variables (1 variable)
- **VISIT** - Visit Name

### Key Transformations
1. **Date standardization**: DD-MMM-YYYY → YYYY-MM-DD (ISO 8601)
2. **USUBJID creation**: STUDYID-SUBJID format
3. **Dose conversion**: EXDSTXT text to numeric EXDOSE
4. **Sequence numbering**: EXSEQ within subject, ordered by start date
5. **Record filtering**: Excludes records without treatment information
6. **Oak ID tracking**: Full data lineage via oak_id_vars

## Example Usage

### Basic Execution
```r
# Navigate to the directory
setwd("/Users/siddharthlokineni/Documents/Oak implementation/ROAK validation/EX domain implementation")

# Generate SDTM datasets
source("EX.R")

# Check results
ex_data <- read.csv("EX_from_sdtm_oak_codegen.csv")
cat("Generated", nrow(ex_data), "exposure records for",
    length(unique(ex_data$USUBJID)), "subjects\n")

# View treatments
table(ex_data$EXTRT)
```

### Customizing for Your Data
To use with your own exposure data:

1. **Replace input file**:
   - Update `EX.csv` with your raw exposure data
   - Ensure column names match expected format:
     - STUDYID, SUBJID, EXTRT, EXDSTXT, EXDOSU, etc.

2. **Modify column mappings** in code generator if column names differ

3. **Update date formats** if your dates use a different format
   - Edit the format string in `emit_exposure_oak_from_spec.R`

4. **Populate study days** if you have reference start dates from DM domain

## Validation Results

This implementation has been tested with CDISC pilot study data:
- **Input**: 591 exposure records
- **Output**: Complete SDTM EX dataset with proper variable mappings
- **Records**: 591 exposure records
- **Subjects**: 254 unique subjects
- **Treatments**:
  - PLACEBO (226 records)
  - XANOMELINE (365 records)
- **Quality**: All required SDTM variables present with proper data types

### Dataset Statistics
- Total records: 591
- File sizes: CSV 83KB, XPT 79KB
- Variables: 16 SDTM-compliant variables
- Average records per subject: ~2.3

## Domain-Specific Considerations

### EX Domain Characteristics
- **Interventions domain**: Captures study treatment exposure
- **Multiple records per subject**: One record per treatment period
- **Timing critical**: Start and end dates document exposure duration
- **Dosing details**: Complete dose, frequency, route, and form information

### Study Day Calculations
The current implementation includes placeholders for study day variables (EXSTDY, EXENDY). These should be populated by:

1. Merging with DM domain to get RFSTDTC (reference start date)
2. Calculating study days as: `date - RFSTDTC + 1`
3. Using negative values for pre-treatment dates (if applicable)

Example:
```r
# Join with DM to get reference date
dm <- read.csv("../DM domain implementation/DM_from_sdtm_oak_codegen.csv")
ex_with_dm <- left_join(EX, dm %>% select(USUBJID, RFSTDTC), by = "USUBJID")

# Calculate study days
ex_with_dm <- ex_with_dm %>%
  mutate(
    EXSTDY = as.numeric(as.Date(EXSTDTC) - as.Date(RFSTDTC)) + 1,
    EXENDY = as.numeric(as.Date(EXENDTC) - as.Date(RFSTDTC)) + 1
  )
```

### Treatment Names
In this pilot data:
- **PLACEBO**: Control treatment (0 dose)
- **XANOMELINE**: Active treatment (various doses)

## Code Generator Architecture

### Design Pattern
This implementation follows the same **specification-driven code generation** pattern as AE and DM domains:

1. **Code Generator** (`emit_exposure_oak_from_spec.R`):
   - Reads CDISC EC specifications
   - Identifies raw data structure
   - Generates optimized R mapping code
   - Creates data lineage with oak_id_vars

2. **Generated Code** (`EX.R`):
   - Loads raw EX data
   - Applies sdtm.oak transformations
   - Generates sequence numbers
   - Exports CSV and XPT formats

### Benefits
- **Maintainability**: Regenerate code when raw data structure changes
- **Consistency**: Same pattern across AE, DM, and EX domains
- **Traceability**: Full data lineage via oak_id
- **Automation**: Can be integrated into data pipelines

## Troubleshooting

### Common Issues

1. **Package not found errors**:
   ```r
   install.packages(c("sdtm.oak", "dplyr", "readxl", "haven"))
   ```

2. **Date parsing errors**:
   - Ensure dates are in DD-MMM-YYYY format
   - Check for missing or malformed date values
   - Verify month abbreviations are in English

3. **Column not found errors**:
   - Verify your EX.csv has the expected column names
   - Regenerate code using `emit_exposure_oak_from_spec.R`
   - Check raw data structure

4. **Missing dose values**:
   - Check EXDSTXT contains numeric dose information
   - Verify dose conversion works with your format

5. **XPT export fails**:
   - Install haven package: `install.packages("haven")`
   - Check file write permissions

## Integration with Other Domains

The EX dataset integrates with other SDTM domains:

### Dependencies
- **DM Domain**: Required for USUBJID validation and RFSTDTC for study days

### Relationships
- **AE Domain**: Link adverse events to treatment exposure periods
- **DS Domain**: Relate disposition events to treatment (discontinuation)
- **VS Domain**: Compare vital signs during treatment periods

## Next Steps

After generating your SDTM EX dataset:

1. **Calculate study days** using reference dates from DM domain
2. **Validate** the output against CDISC standards
3. **Review** variable mappings for correctness
4. **Test** with your study's data validation rules
5. **Document** any study-specific derivations
6. **Integrate** into your clinical data pipeline

## SDTM Compliance Notes

This implementation follows CDISC SDTM v1.4+ standards:
- All required Interventions class variables included
- ISO 8601 date/time format for all date variables
- Proper variable naming and labeling conventions
- Sequence numbers unique within subject
- Full data lineage via oak_id_vars
- Treatment period properly captured with start/end dates

### Regulatory Readiness
- CSV format for data review and analysis
- XPT format for FDA/PMDA submission
- Complete metadata and traceability
- Follows industry best practices

---

**Generated by**: CDISC SDTM Oak Code Generator
**Version**: 1.0
**Generated on**: 2025-11-06
**Compatible with**: CDISC SDTM v1.4+
**Source**: Raw data directory
**Domain Class**: Interventions
**Methodology**: sdtm.oak algorithm-based mapping
**Pattern**: Follows AE/DM domain implementation pattern
