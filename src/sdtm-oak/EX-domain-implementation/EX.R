# ============================================================================
# SDTM EX Domain Mapping Code
# ============================================================================
# Generated on: 2025-11-06
# Domain: EX (Exposure)
# Source: EX.csv
# ============================================================================

library(sdtm.oak)
library(dplyr)

# ==============================================================================
# Data Loading
# ==============================================================================

# Load raw EX data
ex_raw <- read.csv('EX.csv', stringsAsFactors = FALSE)

# Convert ID variables to character
ex_raw$SUBJID <- as.character(ex_raw$SUBJID)
ex_raw$SITEID <- as.character(ex_raw$SITEID)

# Generate oak ID variables
ex_raw <- ex_raw %>%
  generate_oak_id_vars(
    pat_var = 'SUBJID',
    raw_src = 'EX'
  )

# ==============================================================================
# Variable Mappings
# ==============================================================================

EX <- ex_raw %>%
  dplyr::mutate(
    # Core identifiers (SDTM required)
    STUDYID = STUDYID,
    DOMAIN = 'EX',
    USUBJID = paste0(STUDYID, '-', SUBJID),
    SUBJID = SUBJID,

    # Treatment information
    EXTRT = EXTRT,
    EXDOSE = as.numeric(EXDSTXT),           # Convert dose text to numeric
    EXDOSTXT = EXDSTXT,                     # Dose text
    EXDOSU = EXDOSU,
    EXDOSFRM = EXDOSFRM,
    EXDOSFRQ = EXDOSFRQ,
    EXROUTE = EXROUTE,
    EXDOSADJ = NA_character_,               # Dose Adjustment (not in raw data)
    EXADJ = NA_character_,                  # Action Taken (not in raw data)
    EXLOT = NA_character_,                  # Lot Number (not in raw data)
    EXFAST = NA_character_,                 # Fasting Status (not in raw data)
    EXPSTRG = NA_character_,                # Patch Strength (not in raw data)
    EXPSTRGU = NA_character_,               # Patch Strength Units (not in raw data)
    EXREFID = NA_character_,                # Reference ID (not in raw data)

    # Date/Time variables - Convert to ISO 8601 format
    EXSTDTC = dplyr::case_when(
      !is.na(EXSTDAT) & EXSTDAT != '' ~
        format(as.Date(EXSTDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),
    EXENDTC = dplyr::case_when(
      !is.na(EXENDAT) & EXENDAT != '' ~
        format(as.Date(EXENDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),
    EXDTC = dplyr::case_when(
      !is.na(EXSTDAT) & EXSTDAT != '' ~
        format(as.Date(EXSTDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),

    # Visit information
    VISIT = VISIT,

    # Study day calculations (placeholder - requires reference date from DM)
    EXSTDY = NA_integer_,
    EXENDY = NA_integer_
  ) %>%

  # Filter out records without treatment information
  dplyr::filter(!is.na(EXTRT) & EXTRT != "") %>%

  # Create sequence numbers within subject
  dplyr::arrange(USUBJID, EXSTDTC) %>%
  dplyr::group_by(STUDYID, USUBJID) %>%
  dplyr::mutate(EXSEQ = dplyr::row_number()) %>%
  dplyr::ungroup() %>%

  # Select final SDTM variables (per EC specification)
  dplyr::select(
    # Core identifiers
    STUDYID, DOMAIN, USUBJID, EXSEQ,
    # Treatment information
    EXTRT, EXDOSE, EXDOSTXT, EXDOSU, EXDOSFRM, EXDOSFRQ, EXROUTE,
    # Dosing adjustments
    EXDOSADJ, EXADJ,
    # Product information
    EXLOT, EXFAST, EXPSTRG, EXPSTRGU,
    # Timing variables
    EXSTDTC, EXENDTC, EXDTC, EXSTDY, EXENDY,
    # Visit and Reference
    VISIT, EXREFID
  )

# ==============================================================================
# Save Results
# ==============================================================================

write.csv(EX, 'EX_from_sdtm_oak_codegen.csv', row.names = FALSE)
cat('✓ SDTM EX dataset created:', nrow(EX), 'records x', ncol(EX), 'variables\n')

if (requireNamespace('haven', quietly = TRUE)) {
  haven::write_xpt(EX, 'EX_from_sdtm_oak_codegen.xpt')
  cat('✓ XPT file created\n')
}

cat('\nDataset summary:\n')
cat('  Records:', nrow(EX), '\n')
cat('  Subjects:', length(unique(EX$USUBJID)), '\n')
cat('  Treatments:', paste(unique(EX$EXTRT), collapse=', '), '\n')
