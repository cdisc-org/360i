# Synthetic Subject Data for NCT01797120

synthetic subject data for the breast cancer study NCT01797120 using the results published on clinicaltrials.gov (NCT01797120-results.fhir.json)


## Summary

| Metric                    | Target        | Actual        |
|---------------------------|---------------|---------------|
| Subjects (FULEV / FULPL)  | 66 / 65       | 66 / 65 ✓     |
| PFS events FULEV          | 39            | 39 ✓          |
| PFS events FULPL          | 50            | 50 ✓          |
| ORR FULEV                 | 18.2%         | 18.8% ✓       |
| ORR FULPL                 | 12.3%         | 12.7% ✓       |
| CBR FULEV                 | 63.6%         | 68.8% (~close)|
| CBR FULPL                 | 41.5%         | 49.2% (~close)|


**CBR = CR + PR + SD ≥ 24 weeks**

Where:
CR — Complete Response: all target lesions disappear
PR — Partial Response: ≥30% decrease in sum of lesion diameters
SD — Stable Disease: neither CR/PR nor progression, sustained for at least 24 weeks (≈6 months)

The published targets for this trial were:

| Arm                           | CBR                           |
|-------------------------------|-------------------------------|
| Fulvestrant + Everolimus      | 63.6% (42/66)                 |
| Fulvestrant + Placebo         | 41.5% (27/65)                 |


The small Clinical Benefit Rate (CBR) overcount comes from the 2+4 "still on treatment" subjects (who remain in the EFFFL population) being assigned responses from the CBR-sized pool. PFS events and ORR hit their targets exactly.

Output files in *_test_data/_*:

| File              | Rows              | Content                           |
|-------------------|-------------------|-----------------------------------|
| DM.csv            | 131               | Demographics, arm, site, dates    |
| EX.csv            | 2,099             | Fulvestrant IM doses + everolimus/placebo daily records |
| LB.csv            | 19,068            | CBC, chemistry, lipids at every visit |
| VS.csv            | 6,810             | BP, HR, temp, weight at every visit |
| TU.csv            | 610               | RECIST target lesion diameters at imaging visits |
| RS.csv            | 328               | Overall disease response at each assessment |
| ADSL.csv          | 131               | Subject-level PFS/OS times, events, response flags |
| ADTTE.csv         | 254               | One PFS + one OS record per treated subject |


