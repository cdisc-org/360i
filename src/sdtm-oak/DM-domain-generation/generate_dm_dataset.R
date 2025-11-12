# ==============================================================================
# Simple DM Dataset Generator
# ==============================================================================

library(dplyr)

# Load raw data
dm_raw <- read.csv('DM.csv', stringsAsFactors = FALSE)
cat("Loaded DM data: ", nrow(dm_raw), "rows x", ncol(dm_raw), "columns\n")

# Create SDTM DM dataset
DM <- dm_raw %>%
  dplyr::mutate(
    # Core SDTM variables
    DOMAIN = 'DM',
    USUBJID = paste0(STUDYID, '-', SUBJID),

    # Map date variables to ISO format
    DMDTC = dplyr::case_when(
      !is.na(DMDAT) & DMDAT != '' ~ format(as.Date(DMDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),

    # Handle race field - extract primary race if multiple values
    RACE = dplyr::case_when(
      grepl(",", RACE) ~ sub(",.*", "", RACE),  # Take first race if multiple
      TRUE ~ as.character(RACE)
    ),

    # Reference dates (placeholders - would need actual study dates)
    RFSTDTC = NA_character_,  # Reference start date
    RFENDTC = NA_character_,  # Reference end date
    RFXSTDTC = NA_character_, # First exposure date
    RFXENDTC = NA_character_, # Last exposure date
    RFICDTC = NA_character_,  # Date of informed consent
    RFPENDTC = NA_character_, # Date of end of participation

    # Treatment arms (placeholders)
    ARM = NA_character_,      # Planned arm
    ARMCD = NA_character_,    # Planned arm code
    ACTARM = NA_character_,   # Actual arm
    ACTARMCD = NA_character_, # Actual arm code

    # Additional demographics
    BRTHDTC = NA_character_,  # Birth date
    DTHDTC = NA_character_,   # Death date
    DTHFL = NA_character_,    # Death flag

    # Randomization
    RANDDT = NA_character_,   # Randomization date
    RANDTC = NA_character_,   # Randomization datetime

    # Disposition
    DMDTDIS = NA_character_,  # Date of disposition
    DSTERM = NA_character_,   # Disposition term
    DSDECOD = NA_character_,  # Disposition decode

    # Additional identifiers
    INVID = NA_character_,    # Investigator identifier
    INVNAM = NA_character_,   # Investigator name

    # Study participation
    DMDY = NA_integer_        # Study day of demographics collection
  ) %>%

  # Select final SDTM variables
  dplyr::select(
    # Core identifiers
    STUDYID, DOMAIN, USUBJID, SUBJID, SITEID,
    # Demographics
    AGE, AGEU, SEX, RACE, ETHNIC, COUNTRY,
    # Dates
    DMDTC, BRTHDTC, DTHDTC, DTHFL,
    # Reference dates
    RFSTDTC, RFENDTC, RFXSTDTC, RFXENDTC, RFICDTC, RFPENDTC,
    # Treatment arms
    ARM, ARMCD, ACTARM, ACTARMCD,
    # Randomization
    RANDDT, RANDTC,
    # Disposition
    DMDTDIS, DSTERM, DSDECOD,
    # Additional identifiers
    INVID, INVNAM,
    # Study day
    DMDY
  )

cat("Generated SDTM DM dataset: ", nrow(DM), "rows x", ncol(DM), "columns\n")

# Save as CSV
write.csv(DM, 'DM_from_sdtm_oak_codegen.csv', row.names = FALSE)
cat("✓ SDTM DM dataset CSV created: DM_from_sdtm_oak_codegen.csv\n")

# Save as XPT format
if (requireNamespace('haven', quietly = TRUE)) {
  haven::write_xpt(DM, 'DM_from_sdtm_oak_codegen.xpt')
  cat("✓ SDTM DM dataset XPT created: DM_from_sdtm_oak_codegen.xpt\n")
} else {
  cat("⚠ haven package not available - XPT export skipped\n")
  cat("  Install with: install.packages('haven')\n")
}

# Display summary
cat("\nDataset Summary:\n")
cat("Total subjects:", nrow(DM), "\n")
cat("Date range:", min(DM$DMDTC, na.rm = TRUE), "to", max(DM$DMDTC, na.rm = TRUE), "\n")
cat("Sex distribution:\n")
print(table(DM$SEX, useNA = "ifany"))
cat("Race distribution:\n")
print(table(DM$RACE, useNA = "ifany"))
cat("Ethnicity distribution:\n")
print(table(DM$ETHNIC, useNA = "ifany"))
cat("Age summary:\n")
print(summary(as.numeric(DM$AGE)))

cat("\n=== DM Dataset Generation Complete ===\n")