# ==============================================================================
# CDISC SDTM Medical History Domain Code Generator
# ==============================================================================

library(readxl)
library(dplyr)

emit_mh_oak_from_spec <- function(spec_path, raw_csv_path, ct_csv_path, domain = "MH", out_r_path = NULL) {

  cat("=== CDISC SDTM Medical History Domain Code Generator ===\n")
  cat("Domain:", domain, "\n")
  cat("Timestamp:", format(Sys.time(), "%Y-%m-%d"), "\n\n")

  # Read input files
  cat("Reading raw MH data...\n")
  raw <- read.csv(raw_csv_path, stringsAsFactors = FALSE)
  raw_cols <- names(raw)

  cat("Reading MH specifications...\n")
  spec <- readxl::read_excel(spec_path, sheet = "Collection Specializations")
  dom_spec <- spec[toupper(spec$domain) == "MH", ]

  cat("✓ Raw MH data:", nrow(raw), "records,", ncol(raw), "columns\n")
  cat("✓ MH specifications:", nrow(dom_spec), "rows\n\n")

  # Generate code
  L <- character()

  # Header
  L <- c(L, "# ============================================================================")
  L <- c(L, "# SDTM MH Domain Mapping Code")
  L <- c(L, "# ============================================================================")
  L <- c(L, sprintf("# Generated on: %s", format(Sys.time(), "%Y-%m-%d")))
  L <- c(L, sprintf("# Domain: %s (Medical History)", domain))
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
  L <- c(L, sprintf("mh_raw <- read.csv('%s', stringsAsFactors = FALSE)", basename(raw_csv_path)))
  L <- c(L, "")
  L <- c(L, "mh_raw$SUBJID <- as.character(mh_raw$SUBJID)")
  L <- c(L, "mh_raw$SITEID <- as.character(mh_raw$SITEID)")
  L <- c(L, "")
  L <- c(L, "mh_raw <- mh_raw %>%")
  L <- c(L, "  generate_oak_id_vars(")
  L <- c(L, "    pat_var = 'SUBJID',")
  L <- c(L, "    raw_src = 'MH'")
  L <- c(L, "  )")
  L <- c(L, "")

  # Variable mappings
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Variable Mappings")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "MH <- mh_raw %>%")
  L <- c(L, "  dplyr::mutate(")
  L <- c(L, "    STUDYID = STUDYID,")
  L <- c(L, "    DOMAIN = 'MH',")
  L <- c(L, "    USUBJID = paste0(STUDYID, '-', SUBJID),")
  L <- c(L, "")

  # Map available columns
  if("MHTERM" %in% raw_cols) L <- c(L, "    MHTERM = MHTERM,")
  if("MHDECOD" %in% raw_cols) L <- c(L, "    MHDECOD = MHDECOD,")
  if("MHCAT" %in% raw_cols) L <- c(L, "    MHCAT = MHCAT,")
  if("MHSEV" %in% raw_cols) L <- c(L, "    MHSEV = MHSEV,")
  if("MHSPID" %in% raw_cols) L <- c(L, "    MHSPID = MHSPID,")

  # MedDRA coding
  if("MHLLT" %in% raw_cols) L <- c(L, "    MHLLT = MHLLT,")
  if("MHHLT" %in% raw_cols) L <- c(L, "    MHHLT = MHHLT,")
  if("MHHLGT" %in% raw_cols) L <- c(L, "    MHHLGT = MHHLGT,")
  if("MHSOC" %in% raw_cols) L <- c(L, "    MHBODSYS = MHSOC,")

  L <- c(L, "")
  L <- c(L, "    # Date conversions")

  if("MHSTDAT" %in% raw_cols) {
    L <- c(L, "    MHSTDTC = dplyr::case_when(")
    L <- c(L, "      !is.na(MHSTDAT) & MHSTDAT != '' ~")
    L <- c(L, "        format(as.Date(MHSTDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
    L <- c(L, "      TRUE ~ NA_character_")
    L <- c(L, "    ),")
  }

  if("MHDAT" %in% raw_cols) {
    L <- c(L, "    MHDTC = dplyr::case_when(")
    L <- c(L, "      !is.na(MHDAT) & MHDAT != '' ~")
    L <- c(L, "        format(as.Date(MHDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
    L <- c(L, "      TRUE ~ NA_character_")
    L <- c(L, "    ),")
  }

  L <- c(L, "")
  if("VISIT" %in% raw_cols) L <- c(L, "    VISIT = VISIT,")
  L <- c(L, "    MHDY = NA_integer_")
  L <- c(L, "  ) %>%")
  L <- c(L, "")

  # Sequence
  L <- c(L, "  dplyr::filter(!is.na(MHTERM) & MHTERM != \"\") %>%")
  L <- c(L, "  dplyr::arrange(USUBJID, MHSTDTC) %>%")
  L <- c(L, "  dplyr::group_by(STUDYID, USUBJID) %>%")
  L <- c(L, "  dplyr::mutate(MHSEQ = dplyr::row_number()) %>%")
  L <- c(L, "  dplyr::ungroup() %>%")
  L <- c(L, "")

  # Select variables
  L <- c(L, "  dplyr::select(")
  L <- c(L, "    STUDYID, DOMAIN, USUBJID, MHSEQ,")
  L <- c(L, "    MHTERM, MHDECOD, MHCAT, MHSEV,")
  L <- c(L, "    MHLLT, MHHLT, MHHLGT, MHBODSYS,")
  L <- c(L, "    MHSTDTC, MHDTC, MHDY,")
  L <- c(L, "    VISIT, MHSPID")
  L <- c(L, "  )")
  L <- c(L, "")

  # Save
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Save Results")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "write.csv(MH, 'MH_from_sdtm_oak_codegen.csv', row.names = FALSE)")
  L <- c(L, "cat('✓ SDTM MH dataset created:', nrow(MH), 'records x', ncol(MH), 'variables\\n')")
  L <- c(L, "")
  L <- c(L, "if (requireNamespace('haven', quietly = TRUE)) {")
  L <- c(L, "  haven::write_xpt(MH, 'MH_from_sdtm_oak_codegen.xpt')")
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
emit_mh_oak_from_spec(
  spec_path = "cdisc_collection_dataset_specializations_draft.xlsx",
  raw_csv_path = "MH.csv",
  ct_csv_path = "study_ct.csv",
  domain = "MH",
  out_r_path = "MH.R"
)
