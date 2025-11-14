# ==============================================================================
# CDISC SDTM Concomitant Medications Domain Code Generator
# ==============================================================================

library(readxl)
library(dplyr)

emit_cm_oak_from_spec <- function(spec_path, raw_csv_path, ct_csv_path, domain = "CM", out_r_path = NULL) {

  cat("=== CDISC SDTM Concomitant Medications Domain Code Generator ===\n")
  cat("Domain:", domain, "\n")
  cat("Timestamp:", format(Sys.time(), "%Y-%m-%d"), "\n\n")

  # Read input files
  cat("Reading raw CM data...\n")
  raw <- read.csv(raw_csv_path, stringsAsFactors = FALSE)
  raw_cols <- names(raw)

  cat("Reading CM specifications...\n")
  spec <- readxl::read_excel(spec_path, sheet = "Collection Specializations")
  dom_spec <- spec[toupper(spec$domain) == "CM", ]

  cat("✓ Raw CM data:", nrow(raw), "records,", ncol(raw), "columns\n")
  cat("✓ CM specifications:", nrow(dom_spec), "rows\n\n")

  # Generate code
  L <- character()

  # Header
  L <- c(L, "# ============================================================================")
  L <- c(L, "# SDTM CM Domain Mapping Code")
  L <- c(L, "# ============================================================================")
  L <- c(L, sprintf("# Generated on: %s", format(Sys.time(), "%Y-%m-%d")))
  L <- c(L, sprintf("# Domain: %s (Concomitant Medications)", domain))
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
  L <- c(L, sprintf("cm_raw <- read.csv('%s', stringsAsFactors = FALSE)", basename(raw_csv_path)))
  L <- c(L, "")
  L <- c(L, "cm_raw$SUBJID <- as.character(cm_raw$SUBJID)")
  L <- c(L, "cm_raw$SITEID <- as.character(cm_raw$SITEID)")
  L <- c(L, "")
  L <- c(L, "cm_raw <- cm_raw %>%")
  L <- c(L, "  generate_oak_id_vars(")
  L <- c(L, "    pat_var = 'SUBJID',")
  L <- c(L, "    raw_src = 'CM'")
  L <- c(L, "  )")
  L <- c(L, "")

  # Variable mappings
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Variable Mappings")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "CM <- cm_raw %>%")
  L <- c(L, "  dplyr::mutate(")
  L <- c(L, "    STUDYID = STUDYID,")
  L <- c(L, "    DOMAIN = 'CM',")
  L <- c(L, "    USUBJID = paste0(STUDYID, '-', SUBJID),")
  L <- c(L, "")

  # Map available columns
  if("CMTRT" %in% raw_cols) L <- c(L, "    CMTRT = CMTRT,")
  if("CMDECOD" %in% raw_cols) L <- c(L, "    CMDECOD = CMDECOD,")
  if("CMCLAS" %in% raw_cols) L <- c(L, "    CMCLAS = CMCLAS,")
  if("CMINDC" %in% raw_cols) L <- c(L, "    CMINDC = CMINDC,")
  if("CMDOSE" %in% raw_cols) L <- c(L, "    CMDOSE = as.numeric(CMDOSE),")
  if("CMDOSU" %in% raw_cols) L <- c(L, "    CMDOSU = CMDOSU,")
  if("CMDOSFRQ" %in% raw_cols) L <- c(L, "    CMDOSFRQ = CMDOSFRQ,")
  if("CMROUTE" %in% raw_cols) L <- c(L, "    CMROUTE = CMROUTE,")
  if("CMSPID" %in% raw_cols) L <- c(L, "    CMSPID = CMSPID,")
  if("CMONGO" %in% raw_cols) L <- c(L, "    CMONGO = CMONGO,")

  L <- c(L, "")
  L <- c(L, "    # Date conversions")

  if("CMSTDAT" %in% raw_cols) {
    L <- c(L, "    CMSTDTC = dplyr::case_when(")
    L <- c(L, "      !is.na(CMSTDAT) & CMSTDAT != '' ~")
    L <- c(L, "        format(as.Date(CMSTDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
    L <- c(L, "      TRUE ~ NA_character_")
    L <- c(L, "    ),")
  }

  if("CMENDAT" %in% raw_cols) {
    L <- c(L, "    CMENDTC = dplyr::case_when(")
    L <- c(L, "      !is.na(CMENDAT) & CMENDAT != '' ~")
    L <- c(L, "        format(as.Date(CMENDAT, \"%d-%b-%Y\"), \"%Y-%m-%d\"),")
    L <- c(L, "      TRUE ~ NA_character_")
    L <- c(L, "    ),")
  }

  L <- c(L, "")
  if("VISIT" %in% raw_cols) L <- c(L, "    VISIT = VISIT,")
  L <- c(L, "    CMSTDY = NA_integer_,")
  L <- c(L, "    CMENDY = NA_integer_")
  L <- c(L, "  ) %>%")
  L <- c(L, "")

  # Sequence
  L <- c(L, "  dplyr::filter(!is.na(CMTRT) & CMTRT != \"\") %>%")
  L <- c(L, "  dplyr::arrange(USUBJID, CMSTDTC) %>%")
  L <- c(L, "  dplyr::group_by(STUDYID, USUBJID) %>%")
  L <- c(L, "  dplyr::mutate(CMSEQ = dplyr::row_number()) %>%")
  L <- c(L, "  dplyr::ungroup() %>%")
  L <- c(L, "")

  # Select variables
  L <- c(L, "  dplyr::select(")
  L <- c(L, "    STUDYID, DOMAIN, USUBJID, CMSEQ,")
  L <- c(L, "    CMTRT, CMDECOD, CMCLAS, CMINDC,")
  L <- c(L, "    CMDOSE, CMDOSU, CMDOSFRQ, CMROUTE,")
  L <- c(L, "    CMSTDTC, CMENDTC, CMSTDY, CMENDY,")
  L <- c(L, "    VISIT, CMSPID, CMONGO")
  L <- c(L, "  )")
  L <- c(L, "")

  # Save
  L <- c(L, "# ==============================================================================")
  L <- c(L, "# Save Results")
  L <- c(L, "# ==============================================================================")
  L <- c(L, "")
  L <- c(L, "write.csv(CM, 'CM_from_sdtm_oak_codegen.csv', row.names = FALSE)")
  L <- c(L, "cat('✓ SDTM CM dataset created:', nrow(CM), 'records x', ncol(CM), 'variables\\n')")
  L <- c(L, "")
  L <- c(L, "if (requireNamespace('haven', quietly = TRUE)) {")
  L <- c(L, "  haven::write_xpt(CM, 'CM_from_sdtm_oak_codegen.xpt')")
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
emit_cm_oak_from_spec(
  spec_path = "cdisc_collection_dataset_specializations_draft.xlsx",
  raw_csv_path = "CM.csv",
  ct_csv_path = "study_ct.csv",
  domain = "CM",
  out_r_path = "CM.R"
)
