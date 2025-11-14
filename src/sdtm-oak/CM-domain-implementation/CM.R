# ============================================================================
# SDTM CM Domain Mapping Code
# ============================================================================
# Generated on: 2025-11-06
# Domain: CM (Concomitant Medications)
# ============================================================================

library(sdtm.oak)
library(dplyr)

# ==============================================================================
# Data Loading
# ==============================================================================

cm_raw <- read.csv('CM.csv', stringsAsFactors = FALSE)

cm_raw$SUBJID <- as.character(cm_raw$SUBJID)
cm_raw$SITEID <- as.character(cm_raw$SITEID)

cm_raw <- cm_raw %>%
  generate_oak_id_vars(
    pat_var = 'SUBJID',
    raw_src = 'CM'
  )

# ==============================================================================
# Variable Mappings
# ==============================================================================

CM <- cm_raw %>%
  dplyr::mutate(
    STUDYID = STUDYID,
    DOMAIN = 'CM',
    USUBJID = paste0(STUDYID, '-', SUBJID),

    CMTRT = CMTRT,
    CMDECOD = CMDECOD,
    CMCLAS = CMCLAS,
    CMINDC = CMINDC,
    CMDOSE = as.numeric(CMDOSE),
    CMDOSU = CMDOSU,
    CMDOSFRQ = CMDOSFRQ,
    CMROUTE = CMROUTE,
    CMSPID = CMSPID,
    CMONGO = CMONGO,

    # Date conversions
    CMSTDTC = dplyr::case_when(
      !is.na(CMSTDAT) & CMSTDAT != '' ~
        format(as.Date(CMSTDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),
    CMENDTC = dplyr::case_when(
      !is.na(CMENDAT) & CMENDAT != '' ~
        format(as.Date(CMENDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),

    VISIT = VISIT,
    CMSTDY = NA_integer_,
    CMENDY = NA_integer_
  ) %>%

  dplyr::filter(!is.na(CMTRT) & CMTRT != "") %>%
  dplyr::arrange(USUBJID, CMSTDTC) %>%
  dplyr::group_by(STUDYID, USUBJID) %>%
  dplyr::mutate(CMSEQ = dplyr::row_number()) %>%
  dplyr::ungroup() %>%

  dplyr::select(
    STUDYID, DOMAIN, USUBJID, CMSEQ,
    CMTRT, CMDECOD, CMCLAS, CMINDC,
    CMDOSE, CMDOSU, CMDOSFRQ, CMROUTE,
    CMSTDTC, CMENDTC, CMSTDY, CMENDY,
    VISIT, CMSPID, CMONGO
  )

# ==============================================================================
# Save Results
# ==============================================================================

write.csv(CM, 'CM_from_sdtm_oak_codegen.csv', row.names = FALSE)
cat('✓ SDTM CM dataset created:', nrow(CM), 'records x', ncol(CM), 'variables\n')

if (requireNamespace('haven', quietly = TRUE)) {
  haven::write_xpt(CM, 'CM_from_sdtm_oak_codegen.xpt')
  cat('✓ XPT file created\n')
}
