# ==============================================================================
# AE Domain Code Generation Test Script
# ==============================================================================

# Set working directory to AE domain implementation folder
setwd("/Users/siddharthlokineni/Documents/Oak implementation/AE domain implementation")

# Source the code generator
source("emit_events_oak_from_spec.R")

# Run AE domain code generation
cat("Starting AE domain code generation...\n")
cat("Working directory:", getwd(), "\n\n")

# Generate AE mapping code
result <- emit_events_oak_from_spec(
  spec_path = "cdisc_collection_dataset_specializations_draft.xlsx",
  raw_csv_path = "AE.csv",
  ct_csv_path = "study_ct.csv",
  domain = "AE",
  out_r_path = "generated_ae_mapping.R"
)

cat("\n=== AE Code Generation Test Complete ===\n")