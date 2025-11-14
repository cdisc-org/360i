# ============================================================================
# SDTM DS Domain Mapping Code
# ============================================================================
# Generated on: 2025-11-06
# Domain: DS (Disposition)
# ============================================================================

library(sdtm.oak)
library(dplyr)

# ==============================================================================
# Data Loading
# ==============================================================================

ds_raw <- read.csv('DS.csv', stringsAsFactors = FALSE)

ds_raw$SUBJID <- as.character(ds_raw$SUBJID)
ds_raw$SITEID <- as.character(ds_raw$SITEID)

ds_raw <- ds_raw %>%
  generate_oak_id_vars(
    pat_var = 'SUBJID',
    raw_src = 'DS'
  )

# ==============================================================================
# Variable Mappings
# ==============================================================================

DS <- ds_raw %>%
  dplyr::mutate(
    STUDYID = STUDYID,
    DOMAIN = 'DS',
    USUBJID = paste0(STUDYID, '-', SUBJID),

    DSTERM = DSTERM,
    DSDECOD = DSDECOD,
    DSCAT = DSCAT,
    DSSPID = DSSPID,

    # Date conversions
    DSSTDTC = dplyr::case_when(
      !is.na(DSSTDAT) & DSSTDAT != '' ~
        format(as.Date(DSSTDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),
    DSDTC = dplyr::case_when(
      !is.na(DSDAT) & DSDAT != '' ~
        format(as.Date(DSDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),

    VISIT = VISIT,
    DSDY = NA_integer_
  ) %>%

  dplyr::filter(!is.na(DSTERM) & DSTERM != "") %>%
  dplyr::arrange(USUBJID, DSSTDTC) %>%
  dplyr::group_by(STUDYID, USUBJID) %>%
  dplyr::mutate(DSSEQ = dplyr::row_number()) %>%
  dplyr::ungroup() %>%

  dplyr::select(
    STUDYID, DOMAIN, USUBJID, DSSEQ,
    DSTERM, DSDECOD, DSCAT, DSSPID,
    DSSTDTC, DSDTC, DSDY,
    VISIT
  )

# ==============================================================================
# Save Results
# ==============================================================================

write.csv(DS, 'DS_from_sdtm_oak_codegen.csv', row.names = FALSE)
cat('✓ SDTM DS dataset created:', nrow(DS), 'records x', ncol(DS), 'variables\n')

if (requireNamespace('haven', quietly = TRUE)) {
  haven::write_xpt(DS, 'DS_from_sdtm_oak_codegen.xpt')
  cat('✓ XPT file created\n')
}
