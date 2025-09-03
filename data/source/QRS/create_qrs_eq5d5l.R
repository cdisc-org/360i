
### BEGGINING OF CODE #########################################################

# Load required packages
library(tidyverse)
library(haven)
library(labelled)
library(xportr)
library(readxl)

#################################################################################
# Function to add a random integer column with optional NA values
# Arguments:
#   input_df: The input data frame to which the new column will be added.
#   column_name: The name of the new column to be added. This should be a string.
#   min_val: The minimum value for the randomly generated integers.
#   max_val: The maximum value for the randomly generated integers.
#   na_percent: The percentage of NA values to be inserted into the new column.
#                This should be a decimal between 0 and 100
#   seed: 	(Optional) A seed value for random number generation to ensure 
#             reproducibility. Default is 123.
#################################################################################

add_random_column <- function(input_df, column_name, min_val, max_val, na_percent, seed = 123) {
  if (na_percent < 0 || na_percent > 100) {
    stop("na_percent must be between 0 and 100.")
  }
  if (min_val > max_val) {
    stop("min_val must be less than or equal to max_val.")
  }
  if (column_name %in% names(input_df)) {
    warning(paste("Column", column_name, "already exists and will be overwritten."))
  }
  
  set.seed(seed)
  n <- nrow(input_df)
  values <- sample(min_val:max_val, n, replace = TRUE)
  
  na_count <- round(n * na_percent/100)
  if (na_count > 0) {
    na_indices <- sample(1:n, na_count)
    values[na_indices] <- NA
  }
  
  input_df[[column_name]] <- values
  return(input_df)
}


#############################################################################
# Function to create a data frame with column names and max string lengths
# Arguments:
#   input_df: name of the input data frame
#   result_name: name of the output data frame. This should be a string.
#############################################################################

create_length_df <- function(input_df, result_name) {
  # Function to get the maximum string length in a column
  get_max_length <- function(column) {
    if (all(is.na(column))) {
      return(1)
    }
    if (is.numeric(column)) {
      return(8)
    }
    return(max(nchar(as.character(na.omit(column)))))
  }
  
  lengths <- sapply(input_df, get_max_length)
  
  length_df <- data.frame(
    variable = names(lengths),
    length = as.integer(lengths),
    row.names = NULL
  )
  
  assign(result_name, length_df, envir = .GlobalEnv)
  return(length_df)
}

########################################################################
### Read in the specification files
########################################################################

# Read in R12_BC_SDTM_QRS_EQ5D.xlsx to retrieve Controlled Terminology for QSTEST/QSTESTCD and QSORRES values
file_path_bc_sdtm <- "~/360i/data/source/QRS/R12_BC_SDTM_QRS_EQ5D.xlsx"
sdtm_eq5d5l <- read_xlsx(file_path_bc_sdtm, sheet = "SDTM_EQ5D5L")

# Read in CDISC SDTM metadata
file_path_sdtm_metadata <- "~/360i/data/source/QRS/SDTMIG_v3.4.xlsx"
metadata <- read_xlsx(
  file_path_sdtm_metadata, sheet = "Variables"
) %>%
  rename(
    order = `Variable Order`,
    dataset = `Dataset Name`,
    variable = `Variable Name`,
    label = `Variable Label`,
    type = `Type`)

########################################################################
### Create QS domaint for EQ-5D-5L based on the SV domain
########################################################################

# Read in SV domain from LZZT study
file_path_sv <- "~/360i/data/source/LZZT/sdtm/sv.xpt"
sv <- read_xpt(file_path_sv)

qs1 <- sv %>%
  select(-SVENDTC, -DOMAIN) %>% # Remove unnecessary variables
  filter(VISITNUM %in% c(1, 3, 8) ) %>% # Keep only Visit Number 1, 3, and 8
  rename(QSDTC = SVSTDTC, QSDY = VISITDY) %>% # Assessment date is the same date with Visit date
  mutate(
    DOMAIN = "QS",
    QSCAT = "EQ-5D-5L",
    QSEVINTX = "TODAY"
  )

# Retrieve the Controlled Terminologies for QSTEST and QSTESTCD
ct_eq5d5l_qstest <- sdtm_eq5d5l %>%
  filter(sdtm_variable == "QSTEST") %>%
  rename(QSTESTCD = vlm_group_id, QSTEST = assigned_value)

ct_eq5d5l_qstest <- ct_eq5d5l_qstest %>%
  select(QSTESTCD, QSTEST)

# Create 6 records per subject per visit for 6 Questionnaires of EQ-5D-5L
qs2 <- tidyr::crossing(qs1, ct_eq5d5l_qstest)

# Filter only the 5 level scale records
qs_scale <- qs2 %>%
  filter(QSTESTCD != "EQ5D0206")

# Add QSSTRESN with the random values from 1 to 5 and 1% NA
qs_scale2 <- add_random_column(qs_scale, column_name = "QSSTRESN", min_val = 1, max_val = 5, na_percent = 1, seed = 456)

# Retrieve the Controlled Terminologies for QSORRES of 5 level scales
eq5d5l_qsorres <- sdtm_eq5d5l %>%
  filter(sdtm_variable == "QSORRES" & vlm_group_id != "EQ5D0206") 

# Split the strings in 'value_list' by semicolon and expand into new rows,
# then add an index indicating the original position of each value within each vlm_group_id
eq5d5l_qsorres_expanded <- eq5d5l_qsorres %>%
  separate_rows(value_list, sep = ";") %>%
  group_by(vlm_group_id) %>%
  mutate(value_index = row_number()) %>%
  ungroup() %>%
  select(vlm_group_id, value_list, value_index) %>%
  rename(QSTESTCD = vlm_group_id, QSORRES = value_list, QSSTRESN = value_index)

# Merge with qs_scale2 to add QSORRES value
qs_scale3 <- left_join(qs_scale2, eq5d5l_qsorres_expanded, by = c("QSTESTCD", "QSSTRESN"))

# Filter only VAS records
qs_vas <- qs2 %>%
  filter(QSTESTCD == "EQ5D0206")

# Add QSSTRESN with the random values from 1 to 100 and 1% NA
qs_vas2 <- add_random_column(qs_vas, column_name = "QSSTRESN", min_val = 0, max_val = 100, na_percent = 1, seed = 789)

# Derive QSORRES
qs_vas3 <- qs_vas2 %>%
  mutate(
    QSORRES = case_when(
      QSSTRESN == 0   ~ "THE WORST HEALTH YOU CAN IMAGINE",
      QSSTRESN == 100 ~ "THE BEST HEALTH YOU CAN IMAGINE",
      TRUE            ~ as.character(QSSTRESN)
    )
  )

# Combine two datasets
qs3 <- bind_rows(qs_scale3, qs_vas3) %>%
  mutate(
    # Add necessary variables
    QSSTRESC = as.character(QSSTRESN),
    QSMETHOD = if_else(QSTESTCD == "EQ5D0206", "VISUAL ANALOG SCALE (0-100)", NA_character_),
    QSLOBXFL = if_else(VISITNUM == 3, "Y", NA_character_),
    QSSTAT = if_else(is.na(QSSTRESN), "NOT DONE", NA_character_)
  )

# Derive QSSEQ
qs_exportr <- qs3 %>%
  arrange(USUBJID, VISITNUM, QSTESTCD) %>%
  group_by(USUBJID) %>%
  mutate(QSSEQ = row_number()) %>%
  ungroup()

# Create the data frame with variable names and max lengths of the variable
create_length_df(input_df = qs_exportr, result_name = "length_qs")

# Filter the SDTM metadata data frame to keep only QS variables
metadata_qs <- metadata %>%
  filter(dataset == "QS")

# Merge length_qs with metadata_qs to retrieve variable length 
var_spec_qs <- left_join(metadata_qs, length_qs, by = "variable")

# Generate qs.xpt
qs_exportr %>%
  xportr_type(var_spec_qs, "QS", "message") %>%
  xportr_length(var_spec_qs, "QS", verbose = "message") %>%
  xportr_label(var_spec_qs, "QS", "message") %>%
  xportr_order(var_spec_qs, "QS", "message") %>%
#  xportr_format(var_spec_qs, "QS") %>%
  xportr_write("~/360i/data/source/QRS/qs.xpt")

########################################################################
### Create SUPPQS
########################################################################

suppqs1 <- tribble(
  ~QNAM, ~QLABEL, ~QVAL,
  "QSANTXLO", "Anchor Text Low", "THE WORST HEALTH YOU CAN IMAGINE",
  "QSANTXHI", "Anchor Text High", "THE BEST HEALTH YOU CAN IMAGINE",
  "QSANVLLO", "Anchor Value Low", "0",
  "QSANVLHI", "Anchor Value High", "100"
) %>%
  mutate(
    STUDYID = "CDISCPILOT01",
    RDOMAIN = "QS",
    IDVAR = "QSTESTCD",
    IDVARVAL = "EQ5D0206",
    QORIG = "CRF",
    QEVAL = NA_character_
  )

# For the subjects who have VAS assessment, retrieve unique USUBJID value
usubjid_vas <- qs_exportr %>%
  filter(QSTESTCD == "EQ5D0206") %>%
  select(USUBJID) %>%
  arrange(USUBJID) %>%
  distinct()

# Merge with other Suppqual variables
suppqs2 <- tidyr::crossing(suppqs1, usubjid_vas)
suppqs_exportr <- suppqs2 %>%
  arrange(STUDYID, RDOMAIN, USUBJID, IDVAR, IDVARVAL, QNAM)

# Create the data frame with variable names and max lengths of the variable
create_length_df(input_df = suppqs_exportr, result_name = "length_suppqs")

# Filter the SDTM metadata data frame to keep only SUPPQUAL variables
metadata_suppqual <- metadata %>%
  filter(dataset == "SUPPQUAL")

# Merge length_suppqs with metadata_suppqual to retrieve variable length 
var_spec_suppqs <- left_join(metadata_suppqual, length_suppqs, by = "variable")

# Generate suppqs.xpt
suppqs_exportr %>%
  xportr_type(var_spec_suppqs, "SUPPQUAL", "message") %>%
  xportr_length(var_spec_suppqs, "SUPPQUAL", verbose = "message") %>%
  xportr_label(var_spec_suppqs, "SUPPQUAL", "message") %>%
  xportr_order(var_spec_suppqs, "SUPPQUAL", "message") %>%
#  xportr_format(var_spec_suppqs, "SUPPQUAL") %>%
  xportr_write("~/360i/data/source/QRS/suppqs.xpt")

### END OF CODE #########################################################
