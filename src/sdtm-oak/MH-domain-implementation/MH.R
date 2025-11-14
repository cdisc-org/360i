# ============================================================================
# SDTM MH Domain Mapping Code
# ============================================================================
# Generated on: 2025-11-06
# Domain: MH (Medical History)
# ============================================================================

library(sdtm.oak)
library(dplyr)

# ==============================================================================
# Data Loading
# ==============================================================================

mh_raw <- read.csv('MH.csv', stringsAsFactors = FALSE)

mh_raw$SUBJID <- as.character(mh_raw$SUBJID)
mh_raw$SITEID <- as.character(mh_raw$SITEID)

mh_raw <- mh_raw %>%
  generate_oak_id_vars(
    pat_var = 'SUBJID',
    raw_src = 'MH'
  )

# ==============================================================================
# Variable Mappings
# ==============================================================================

MH <- mh_raw %>%
  dplyr::mutate(
    STUDYID = STUDYID,
    DOMAIN = 'MH',
    USUBJID = paste0(STUDYID, '-', SUBJID),

    MHTERM = MHTERM,
    MHDECOD = MHDECOD,
    MHCAT = MHCAT,
    MHSEV = MHSEV,
    MHSPID = MHSPID,
    MHLLT = MHLLT,
    MHHLT = MHHLT,
    MHHLGT = MHHLGT,
    MHBODSYS = MHSOC,

    # Date conversions
    MHSTDTC = dplyr::case_when(
      !is.na(MHSTDAT) & MHSTDAT != '' ~
        format(as.Date(MHSTDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),
    MHDTC = dplyr::case_when(
      !is.na(MHDAT) & MHDAT != '' ~
        format(as.Date(MHDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),

    VISIT = VISIT,
    MHDY = NA_integer_
  ) %>%

  dplyr::filter(!is.na(MHTERM) & MHTERM != "") %>%
  dplyr::arrange(USUBJID, MHSTDTC) %>%
  dplyr::group_by(STUDYID, USUBJID) %>%
  dplyr::mutate(MHSEQ = dplyr::row_number()) %>%
  dplyr::ungroup() %>%

  dplyr::select(
    STUDYID, DOMAIN, USUBJID, MHSEQ,
    MHTERM, MHDECOD, MHCAT, MHSEV,
    MHLLT, MHHLT, MHHLGT, MHBODSYS,
    MHSTDTC, MHDTC, MHDY,
    VISIT, MHSPID
  )

# ==============================================================================
# Save Results
# ==============================================================================

write.csv(MH, 'MH_from_sdtm_oak_codegen.csv', row.names = FALSE)
cat('✓ SDTM MH dataset created:', nrow(MH), 'records x', ncol(MH), 'variables\n')

if (requireNamespace('haven', quietly = TRUE)) {
  haven::write_xpt(MH, 'MH_from_sdtm_oak_codegen.xpt')
  cat('✓ XPT file created\n')
}
