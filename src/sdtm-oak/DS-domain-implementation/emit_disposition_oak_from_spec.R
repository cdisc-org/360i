# ==============================================================================
# CDISC SDTM Disposition Domain Code Generator
# ==============================================================================

library(readxl)
library(dplyr)

emit_disposition_oak_from_spec <- function(spec_path, raw_csv_path, ct_csv_path, domain = "DS", out_r_path = NULL) {

  cat("=== CDISC SDTM Disposition Domain Code Generator ===\n")
  cat("Domain:", domain, "\n")
  cat("Timestamp:", format(Sys.time(), "%Y-%m-%d"), "\n\n")

  # Read input files
  cat("Reading raw DS data...\n")
  raw <- read.csv(raw_csv_path, stringsAsFactors = FALSE)
  raw_cols <- names(raw)

  cat("Reading DS specifications...\n")
  spec <- readxl::read_excel(spec_path, sheet = "Collection Specializations")
  dom_spec <- spec[toupper(spec$domain) == "DS", ]

  cat("✓ Raw DS data:", nrow(raw), "records,", ncol(raw), "columns\n")
  cat("✓ DS specifications:", nrow(dom_spec), "rows\n\n")

  # Get SDTM target variables
  sdtm_vars <- unique(dom_spec$sdtm_target_variable)
  sdtm_vars <- sdtm_vars[!is.na(sdtm_vars)]

  # Generate code
  L <- character()

  # Header
  L <- c(L, "# ============================================================================")
  L <- c(L, "# SDTM DS Domain Mapping Code")
  L <- c(L, "# ============================================================================")
  L <- c(L, sprintf("# Generated on: %s", format(Sys.time(), "%Y-%m-%d")))
  L <- c(L, sprintf("# Domain: %s (Disposition)", domain))
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
  L <- c(L, sprintf("ds_raw <- read.csv('%s', stringsAsFactors = FALSE)", basename(raw_csv_path)))
  L <- c(L, "")
  L <- c(L, "ds_raw$SUBJID <- as.character(ds_raw$SUBJID)")
  L <- c(L, "ds_raw$SITEID <- as.character(ds_raw$SITEID)")
  L <- c(L, "")
  L <- c(L, "ds_raw <- ds_raw %>%")
  L <- c(L, "  generate_oak_id_vars(")
  L <- c(L, "    pat_var = 'SUBJID',")
  L <- c(L, "    raw_src = 'DS'")
  L <- c(L, "  )")
  L <- c(L, "")

  # Variable mappings
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Variable Mappings")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "DS <- ds_raw %>%")
  L <- c(L, "  dplyr::mutate(")
  L <- c(L, "    STUDYID = STUDYID,")
  L <- c(L, "    DOMAIN = 'DS',")
  L <- c(L, "    USUBJID = paste0(STUDYID, '-', SUBJID),")
  L <- c(L, "")

  # Map available columns
  if("DSTERM" %in% raw_cols) L <- c(L, "    DSTERM = DSTERM,")
  if("DSDECOD" %in% raw_cols) L <- c(L, "    DSDECOD = DSDECOD,")
  if("DSCAT" %in% raw_cols) L <- c(L, "    DSCAT = DSCAT,")
  if("DSSPID" %in% raw_cols) L <- c(L, "    DSSPID = DSSPID,")

  L <- c(L, "")
  L <- c(L, "    # Date conversions")

  if("DSSTDAT" %in% raw_cols) {
    L <- c(L, "    DSSTDTC = dplyr::case_when(")
    L <- c(L, "      !is.na(DSSTDAT) & DSSTDAT != '' ~")
    L <- c(L, "        format(as.Date(DSSTDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
    L <- c(L, "      TRUE ~ NA_character_")
    L <- c(L, "    ),")
  }

  if("DSDAT" %in% raw_cols) {
    L <- c(L, "    DSDTC = dplyr::case_when(")
    L <- c(L, "      !is.na(DSDAT) & DSDAT != '' ~")
    L <- c(L, "        format(as.Date(DSDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
    L <- c(L, "      TRUE ~ NA_character_")
    L <- c(L, "    ),")
  }

  L <- c(L, "")
  if("VISIT" %in% raw_cols) L <- c(L, "    VISIT = VISIT,")
  L <- c(L, "    DSDY = NA_integer_")
  L <- c(L, "  ) %>%")
  L <- c(L, "")

  # Sequence
  L <- c(L, "  dplyr::filter(!is.na(DSTERM) & DSTERM != \"\") %>%")
  L <- c(L, "  dplyr::arrange(USUBJID, DSSTDTC) %>%")
  L <- c(L, "  dplyr::group_by(STUDYID, USUBJID) %>%")
  L <- c(L, "  dplyr::mutate(DSSEQ = dplyr::row_number()) %>%")
  L <- c(L, "  dplyr::ungroup() %>%")
  L <- c(L, "")

  # Select variables
  L <- c(L, "  dplyr::select(")
  L <- c(L, "    STUDYID, DOMAIN, USUBJID, DSSEQ,")
  L <- c(L, "    DSTERM, DSDECOD, DSCAT, DSSPID,")
  L <- c(L, "    DSSTDTC, DSDTC, DSDY,")
  L <- c(L, "    VISIT")
  L <- c(L, "  )")
  L <- c(L, "")

  # Save
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Save Results")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "write.csv(DS, 'DS_from_sdtm_oak_codegen.csv', row.names = FALSE)")
  L <- c(L, "cat('✓ SDTM DS dataset created:', nrow(DS), 'records x', ncol(DS), 'variables\\n')")
  L <- c(L, "")
  L <- c(L, "if (requireNamespace('haven', quietly = TRUE)) {")
  L <- c(L, "  haven::write_xpt(DS, 'DS_from_sdtm_oak_codegen.xpt')")
  L <- c(L, "  cat('✓ XPT file created\\n')")
  L <- c(L, "}")

  if (!is.null(out_r_path)) {
    writeLines(L, out_r_path)
    cat("\n✓ Generated code saved to:", out_r_path, "\n")
  }

  cat("✓ Code generation complete\n")
  invisible(L)
}

# Execute
emit_disposition_oak_from_spec(
  spec_path = "cdisc_collection_dataset_specializations_draft.xlsx",
  raw_csv_path = "DS.csv",
  ct_csv_path = "study_ct.csv",
  domain = "DS",
  out_r_path = "DS.R"
)
