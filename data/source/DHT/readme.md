# Digital Health Technology (DHT)

The DHT sub-team is creating synthetic data for the 360i LZZT amendment.

## "DHT 360i - Physical Activity - Step Count - activity daily.csv"

This provides activity (step count) for 2 subjects.

This data was reviewed and approved; subsequently, the DHT sub-team will provide additional activity data for 30-50 more subjects.

It is expected that they will also be able to provide Continuous Glucose Monitoring (CGM) data.

## DHT 360i - Glucose Level - CGM - example data 09FEB2024 (2).xlsx

This file provides 7 CGM records for Glucose monitoring.

## "activity_12_c44c725b-6686-4915-84a5-63e1aa29da48_activitydaily16.csv"

This provides activity (step count) for 40 subjects.
Downloaded the zip file (Ametris Activity Daily Sample for 360i.zip) from https://wiki.cdisc.org/display/DHTT/360i+DHT+File+List, and unzipped.

## synthetic_step_count_data.csv

Synthetic data generated based on the following scenario: Amount of physical activity collected using a wearable, sensor-based digital health technology, measured in number of steps per day, from LZZT Visit 1 to the day before Visit 2. This scenario will be updated according to the specifications provided by the design team.
Step count data is randomly sampled from the file: activity_12_c44c725b-6686-4915-84a5-63e1aa29da48_activitydaily16.csv

## create_dht_step_count.R

This is R code used to create synthetic_step_count_data.csv
