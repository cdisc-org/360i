# ==============================================================================
# Simple AE Dataset Generator
# ==============================================================================

library(dplyr)

# Load raw data
ae_raw <- read.csv('AE.csv', stringsAsFactors = FALSE)
cat("Loaded AE data: ", nrow(ae_raw), "rows x", ncol(ae_raw), "columns\n")

# Create SDTM AE dataset
AE <- ae_raw %>%
  dplyr::mutate(
    # Core SDTM variables
    DOMAIN = 'AE',
    USUBJID = paste0(STUDYID, '-', SUBJID),

    # Map AESOC to AEBODSYS
    AEBODSYS = AESOC,

    # Convert numeric severity to text
    AESEV = dplyr::case_when(
      AESEV == '1' ~ 'MILD',
      AESEV == '2' ~ 'MODERATE',
      AESEV == '3' ~ 'SEVERE',
      TRUE ~ as.character(AESEV)
    ),

    # Map date variables to ISO format
    AESTDTC = dplyr::case_when(
      !is.na(AESTDAT) & AESTDAT != '' ~ format(as.Date(AESTDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),
    AEENDTC = dplyr::case_when(
      !is.na(AEENDAT) & AEENDAT != '' ~ format(as.Date(AEENDAT, "%d-%b-%Y"), "%Y-%m-%d"),
      TRUE ~ NA_character_
    ),

    # Study day calculation (placeholder)
    AEDY = NA_integer_
  ) %>%

  # Create sequence numbers
  dplyr::group_by(STUDYID, USUBJID) %>%
  dplyr::mutate(AESEQ = dplyr::row_number()) %>%
  dplyr::ungroup() %>%

  # Select final SDTM variables
  dplyr::select(
    STUDYID, DOMAIN, USUBJID, AESEQ, AETERM, AEDECOD, AEBODSYS,
    AESEV, AESER, AEREL, AEACN, AEOUT, AESTDTC, AEENDTC, AEDY,
    # MedDRA hierarchy
    AELLT, AELLTCD, AEHLT, AEHLTCD, AEHLGT, AEHLGTCD, AESOCCD, AEPTCD,
    # AE-specific variables
    AEYN, AESPID, AEONGO
  )

cat("Generated SDTM AE dataset: ", nrow(AE), "rows x", ncol(AE), "columns\n")

# Save as CSV
write.csv(AE, 'AE_from_sdtm_oak_codegen.csv', row.names = FALSE)
cat("✓ SDTM AE dataset CSV created: AE_from_sdtm_oak_codegen.csv\n")

# Save as XPT format
if (requireNamespace('haven', quietly = TRUE)) {
  haven::write_xpt(AE, 'AE_from_sdtm_oak_codegen.xpt')
  cat("✓ SDTM AE dataset XPT created: AE_from_sdtm_oak_codegen.xpt\n")
} else {
  cat("⚠ haven package not available - XPT export skipped\n")
  cat("  Install with: install.packages('haven')\n")
}

# Display summary
cat("\nDataset Summary:\n")
cat("Unique subjects:", length(unique(AE$USUBJID)), "\n")
cat("Total AE records:", nrow(AE), "\n")
cat("Date range:", min(AE$AESTDTC, na.rm = TRUE), "to", max(AE$AESTDTC, na.rm = TRUE), "\n")
cat("Severity distribution:\n")
print(table(AE$AESEV, useNA = "ifany"))

cat("\n=== AE Dataset Generation Complete ===\n")