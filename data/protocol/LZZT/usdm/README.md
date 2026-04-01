# README
A new USDM JSON file has been created for the CDISC Pilot Study (LZZT) - `CDISC_Pilot_Study_v4.json`

The new USDM has been updated to address issues reported by CORE.


```bash
python core.py validate -s USDM -v 4-0 -dp CDISC_Pilot_Study_v4.json -o CDISC_Pilot_Study_v4_report.xlsx
```

Conformance reports have been attached to display the rules executed against each of the USDM files.

## Deprecated 

The file **pilot_LLZT_protocol.json** was created from **pilot_LLZT_protocol.xlsx** with the following script:

[test_simple.py](https://github.com/data4knowledge/usdm_data/blob/main/test_simple.py) at [https://github.com/data4knowledge/usdm_data](https://github.com/data4knowledge/usdm_data).

The file **pilot_LLZT_protocol_bc.xlsx** is a static view of **pilot_LLZT_protocol.xlsx** and contains the results of an API lookup to find the BC C-codes for the Biomedical Concepts in the timelines.

This file is included only to support older applications and projects that are still using the file.
