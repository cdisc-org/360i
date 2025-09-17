###############################################################################
# Program Name            : create_dht_step_count.R
# Program Purpose         : Creation of synthetic DHT step count data
# Program Author          : Rie Ichihashi (Rie.Ichihashi@sanofi.com)
# Date Completed          : 08SEP2025
###############################################################################

### BEGGINING OF CODE #########################################################

# Load required packages
library(lubridate)
library(tidyverse)
library(haven)
library(readxl)
library(purrr)

# Read in the sample DHT Step Count data
file_path_step_count <- "~/360i/data/source/DHT/activity_12_c44c725b-6686-4915-84a5-63e1aa29da48_activitydaily16.csv"
df_step_count <- read_csv(file_path_step_count)

# Read in SV domain from LZZT study
file_path_sv <- "~/360i/data/source/LZZT/sdtm/sv.xpt"
df_sv <- read_xpt(file_path_sv) %>%
  filter(VISITNUM %% 1 == 0) %>% # Remove unscheduled visit
  arrange(USUBJID, VISITNUM) %>%
  group_by(USUBJID) %>%
  mutate(
    SVSTDT = ymd(SVSTDTC),
    dur_visit = as.numeric(lead(SVSTDT) - SVSTDT) # calculate duration until next visit start date in days
  ) %>%
  ungroup()

# Create date sequence for each visit using rowwise
df_sv_date <- df_sv %>%
  filter(is.finite(dur_visit) & dur_visit > 0) %>%
  rowwise() %>%
  mutate(
    dates_visit = list(seq(SVSTDT, by = "day", length.out = dur_visit))
  ) %>%
  ungroup() %>%
  unnest(dates_visit)

# Filter for VISITNUM == 1 and create DHT source columns
df_dates_visit <- df_sv_date %>%
  filter(VISITNUM == 1) %>%
  mutate(
    STUDYNAME = STUDYID,
    SITEIDENTIFIER = str_sub(USUBJID, 4, 6),
    SUBJECT = str_sub(USUBJID, 8, 11),
    DEVICEID = str_c("STM2D4323", SUBJECT),
    DATE = format(dates_visit, "%d/%m/%Y")
  ) %>%
  select(STUDYNAME, SITEIDENTIFIER, SUBJECT, DEVICEID, DATE)

# Sample step count data to match visit dates
sample_size <- nrow(df_dates_visit)

set.seed(123)  # Set seed for reproducibility
df_step_count_sampled <- df_step_count %>%
  select(-STUDYNAME, -SITEIDENTIFIER, -SUBJECT, -DATE, -DEVICEID) %>%
  sample_n(size = sample_size)

# Combine visit dates and step count data
df_synthetic_step_count_data <- cbind(df_dates_visit, df_step_count_sampled)

# Export to CSV file
df_synthetic_step_count_data %>%
  write_csv("~/360i/data/source/DHT/synthetic_step_count_data.csv")

### END OF CODE #########################################################
