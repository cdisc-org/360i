# ==============================================================================
# CDISC SDTM Exposure Domain Code Generator
# ==============================================================================
#
# File: emit_exposure_oak_from_spec.R
# Purpose: Generate R code for mapping raw EX data to SDTM EX domain
#          using sdtm.oak package methodology
#
# Input:
#   - CDISC Collection Specializations Excel file (for EC domain specs)
#   - Raw EX CSV data file
#   - Study controlled terminology CSV file
#
# Output:
#   - R script for SDTM EX domain mapping (EX.R)
#
# Author: CDISC SDTM Oak Code Generator
# Version: 1.0
# ==============================================================================

library(readxl)
library(dplyr)

emit_exposure_oak_from_spec <- function(spec_path, raw_csv_path, ct_csv_path, domain = "EX", out_r_path = NULL) {

  cat("=== CDISC SDTM Exposure Domain Code Generator ===\n")
  cat("Domain:", domain, "\n")
  cat("Timestamp:", format(Sys.time(), "%Y-%m-%d"), "\n\n")

  # Read input files
  cat("Reading raw EX data...\n")
  raw <- read.csv(raw_csv_path, stringsAsFactors = FALSE)

  # Get domain-specific specs (using EC specs since EX is the SDTM output of EC)
  cat("Reading EC specifications...\n")
  spec <- readxl::read_excel(spec_path, sheet = "Collection Specializations")
  dom_spec <- spec[toupper(spec$domain) == "EC", ]

  raw_cols <- names(raw)

  cat("✓ Raw EX data:", nrow(raw), "records,", ncol(raw), "columns\n")
  cat("✓ EC specifications:", nrow(dom_spec), "rows\n\n")

  # Generate code
  L <- character()

  # Header
  L <- c(L, "# ============================================================================")
  L <- c(L, "# SDTM EX Domain Mapping Code")
  L <- c(L, "# ============================================================================")
  L <- c(L, sprintf("# Generated on: %s", format(Sys.time(), "%Y-%m-%d")))
  L <- c(L, sprintf("# Domain: %s (Exposure)", domain))
  L <- c(L, sprintf("# Source: %s", basename(raw_csv_path)))
  L <- c(L, "# ============================================================================")
  L <- c(L, "")
  L <- c(L, "library(sdtm.oak)")
  L <- c(L, "library(dplyr)")
  L <- c(L, "")

  # Data loading
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Data Loading")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "# Load raw EX data")
  L <- c(L, sprintf("ex_raw <- read.csv('%s', stringsAsFactors = FALSE)", basename(raw_csv_path)))
  L <- c(L, "")
  L <- c(L, "# Convert ID variables to character")
  L <- c(L, "ex_raw$SUBJID <- as.character(ex_raw$SUBJID)")
  L <- c(L, "ex_raw$SITEID <- as.character(ex_raw$SITEID)")
  L <- c(L, "")
  L <- c(L, "# Generate oak ID variables")
  L <- c(L, "ex_raw <- ex_raw %>%")
  L <- c(L, "  generate_oak_id_vars(")
  L <- c(L, "    pat_var = 'SUBJID',")
  L <- c(L, "    raw_src = 'EX'")
  L <- c(L, "  )")
  L <- c(L, "")

  # Variable mappings
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Variable Mappings")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "EX <- ex_raw %>%")
  L <- c(L, "  dplyr::mutate(")
  L <- c(L, "    # Core identifiers (SDTM required)")
  L <- c(L, "    STUDYID = STUDYID,")
  L <- c(L, "    DOMAIN = 'EX',")
  L <- c(L, "    USUBJID = paste0(STUDYID, '-', SUBJID),")
  L <- c(L, "    SUBJID = SUBJID,")
  L <- c(L, "")
  L <- c(L, "    # Treatment information")
  L <- c(L, "    EXTRT = EXTRT,")
  L <- c(L, "    EXDOSE = as.numeric(EXDSTXT),           # Convert dose text to numeric")
  L <- c(L, "    EXDOSTXT = EXDSTXT,                     # Dose text")
  L <- c(L, "    EXDOSU = EXDOSU,")
  L <- c(L, "    EXDOSFRM = EXDOSFRM,")
  L <- c(L, "    EXDOSFRQ = EXDOSFRQ,")
  L <- c(L, "    EXROUTE = EXROUTE,")
  L <- c(L, "    EXDOSADJ = NA_character_,               # Dose Adjustment (not in raw data)")
  L <- c(L, "    EXADJ = NA_character_,                  # Action Taken (not in raw data)")
  L <- c(L, "    EXLOT = NA_character_,                  # Lot Number (not in raw data)")
  L <- c(L, "    EXFAST = NA_character_,                 # Fasting Status (not in raw data)")
  L <- c(L, "    EXPSTRG = NA_character_,                # Patch Strength (not in raw data)")
  L <- c(L, "    EXPSTRGU = NA_character_,               # Patch Strength Units (not in raw data)")
  L <- c(L, "    EXREFID = NA_character_,                # Reference ID (not in raw data)")
  L <- c(L, "")
  L <- c(L, "    # Date/Time variables - Convert to ISO 8601 format")
  L <- c(L, "    EXSTDTC = dplyr::case_when(")
  L <- c(L, "      !is.na(EXSTDAT) & EXSTDAT != '' ~")
  L <- c(L, "        format(as.Date(EXSTDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
  L <- c(L, "      TRUE ~ NA_character_")
  L <- c(L, "    ),")
  L <- c(L, "    EXENDTC = dplyr::case_when(")
  L <- c(L, "      !is.na(EXENDAT) & EXENDAT != '' ~")
  L <- c(L, "        format(as.Date(EXENDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
  L <- c(L, "      TRUE ~ NA_character_")
  L <- c(L, "    ),")
  L <- c(L, "    EXDTC = dplyr::case_when(")
  L <- c(L, "      !is.na(EXSTDAT) & EXSTDAT != '' ~")
  L <- c(L, "        format(as.Date(EXSTDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
  L <- c(L, "      TRUE ~ NA_character_")
  L <- c(L, "    ),")
  L <- c(L, "")
  L <- c(L, "    # Visit information")
  L <- c(L, "    VISIT = VISIT,")
  L <- c(L, "")
  L <- c(L, "    # Study day calculations (placeholder - requires reference date from DM)")
  L <- c(L, "    EXSTDY = NA_integer_,")
  L <- c(L, "    EXENDY = NA_integer_")
  L <- c(L, "  ) %>%")
  L <- c(L, "")

  # Sequence and filter
  L <- c(L, "  # Filter out records without treatment information")
  L <- c(L, "  dplyr::filter(!is.na(EXTRT) & EXTRT != \"\") %>%")
  L <- c(L, "")
  L <- c(L, "  # Create sequence numbers within subject")
  L <- c(L, "  dplyr::arrange(USUBJID, EXSTDTC) %>%")
  L <- c(L, "  dplyr::group_by(STUDYID, USUBJID) %>%")
  L <- c(L, "  dplyr::mutate(EXSEQ = dplyr::row_number()) %>%")
  L <- c(L, "  dplyr::ungroup() %>%")
  L <- c(L, "")

  # Select final variables
  L <- c(L, "  # Select final SDTM variables (per EC specification)")
  L <- c(L, "  dplyr::select(")
  L <- c(L, "    # Core identifiers")
  L <- c(L, "    STUDYID, DOMAIN, USUBJID, EXSEQ,")
  L <- c(L, "    # Treatment information")
  L <- c(L, "    EXTRT, EXDOSE, EXDOSTXT, EXDOSU, EXDOSFRM, EXDOSFRQ, EXROUTE,")
  L <- c(L, "    # Dosing adjustments")
  L <- c(L, "    EXDOSADJ, EXADJ,")
  L <- c(L, "    # Product information")
  L <- c(L, "    EXLOT, EXFAST, EXPSTRG, EXPSTRGU,")
  L <- c(L, "    # Timing variables")
  L <- c(L, "    EXSTDTC, EXENDTC, EXDTC, EXSTDY, EXENDY,")
  L <- c(L, "    # Visit and Reference")
  L <- c(L, "    VISIT, EXREFID")
  L <- c(L, "  )")
  L <- c(L, "")

  # Save results
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Save Results")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "write.csv(EX, 'EX_from_sdtm_oak_codegen.csv', row.names = FALSE)")
  L <- c(L, "cat('✓ SDTM EX dataset created:', nrow(EX), 'records x', ncol(EX), 'variables\\n')")
  L <- c(L, "")
  L <- c(L, "if (requireNamespace('haven', quietly = TRUE)) {")
  L <- c(L, "  haven::write_xpt(EX, 'EX_from_sdtm_oak_codegen.xpt')")
  L <- c(L, "  cat('✓ XPT file created\\n')")
  L <- c(L, "}")
  L <- c(L, "")
  L <- c(L, "cat('\\nDataset summary:\\n')")
  L <- c(L, "cat('  Records:', nrow(EX), '\\n')")
  L <- c(L, "cat('  Subjects:', length(unique(EX$USUBJID)), '\\n')")
  L <- c(L, "cat('  Treatments:', paste(unique(EX$EXTRT), collapse=', '), '\\n')")

  # Write output
  if (!is.null(out_r_path)) {
    writeLines(L, out_r_path)
    cat("\n✓ Generated code saved to:", out_r_path, "\n")
  }

  cat("✓ Code generation complete\n")
  cat("  Lines generated:", length(L), "\n")

  invisible(L)
}

# ==============================================================================
# Execute
# ==============================================================================

emit_exposure_oak_from_spec(
  spec_path = "cdisc_collection_dataset_specializations_draft.xlsx",
  raw_csv_path = "EX.csv",
  ct_csv_path = "study_ct.csv",
  domain = "EX",
  out_r_path = "EX.R"
)

cat("\n=== Next Steps ===\n")
cat("Run: source('EX.R') to generate SDTM EX datasets\n")
