# Recent feedback resulting in the new script generation for these datasets.

The `../scripts/cdisc_generation_functions.py` file hass been changed in accrodance with the feedback below. All CSV files in this direcetory have been generated with the latest `../scripts/cdisc_generation_functions.py`.

## DS Domain contains values not expected

| DSDECOD Value | Comment   |
|---------------|-----------|
| RANDOMIZED    | This is a value in the Protocol Milestone codelist.  The `DSCAT` for the record would be "PROTOCOL MILESTONE" |
| TREATMENT     | I don't understand what a record this value is supposed to mean.  This is not a value in any of the codelists for `DSDECOD`. Dates are between those for "RANDOMIZED" records and records with other `DSDECOD` values, but are anywhere from a few weeks to a few months after the "RANDOMIZED" record. |
| PROGRESSIVE DISEASE | This is a value in the Completion/Reason for Non-Completion code.  The `DSCAT` for the record would be "DISPOSITION EVENT".  We would also expect a `DSSCAT` value, probably "STUDY TREATMENT", since in this study, subjects are followed (ideally) until death, even if they've stopped treatment. Most subjects seem to two have records for the same date with  `DSDECOD = "PROGESSIVE DISEASE"`, one with `EPOCH = "TREATMENT"` and one with `EPOCH = "FOLLOW-UP"`.  This doesn't make sense since any particular date falls into only on EPOCH, and there is only one disposition event of ending treatment for progressive disease.  Actually, since there are two treatments in the study, if the treatments were stopped at different times, it would be possible to have two disposition events for ending treatment, one with `DSSCAT = "FULVESTRANT"` and one with `DSSCAT = "EVEROLIMUS"`. |
| COMPLETED     | This is a term in the Completion/Reason for Non-Completion codelist, used for records with `DSCAT = "DISPOSITION EVENT"`. For patients with records with this value, the record is always the third record, after records for "RANDOMIZED" and "TREATED".  This doesn't make sense in this trial, where it's not clear what normal completion of the trial would be, since subjects are supposed to be followed until death.  If a subject does die, one would expect DSDECOD to be "DEATH". |
| WITHDRAWAL BY SUBJECT | This is a term in the Completion/Reason for Non-Completion codelist, used for records with DSCAT = "DISPOSITION EVENT".  For patients with records with this value, the record is always the third record, after records for "RANDOMIZED" and "TREATED". |


I compared `DS` with `DM` and saw that everyone in the trial has the same `RFSTDTC`, and that this matches the date of the DS record with `DSDECOD = "RANDOMIZED"` for every subject.  It's not realistic that all subjects would have started treatment on the same day.  It's possible that some subjects started treatment a day or two after randomization, though one would try to start treatment as soon as a subject is randomized. So the fact that `RFSTDTC` is always the same as the date of randomization in `DS` doesn't bother me.

Reviewers would expect to have `DTHFL` included in the `DM` dataset and `DTHDTC` to be populated if `DTHFL = "Y"`. Admittedly, the fact that a patient died is usually collected in some other domain (probably `DS`), and added to `DM`.

`TRT01A` is an ADaM variable, not an SDTM variable.  the arm to which a subject was randomized would be represented in some combination of `ARMCD`, `ARM`, `ACTARMCD`, and `ACTARM`.  `ARMCD` and `ARM` are code and text for an arm, as are `ACTARMCD` and `ACTARM`.  `ARMCD/ARM` are the same as `ACTARMCD/ACTARM` unless a subject receives no treatment (in which case `ACTARMCD/ACTARM` are null) a subject receives a treatment other than that to which they were randomized.  I don't think we need to build the treated-wrong situation into the synthetic data, although I think the study included a couple of subjects who were never treated.  What's currently in `TRT01A` would probably be in `ACTARM` and `ARM`.

`EXSEQ` is incorrectly populated. `--SEQ` distinguishes between records for a subject.


The `EX`  dataset is missing `EXFREQ`.
`EXFREQ` for fulvestrant injections would likely be "ONCE" with a record for each injection, and `EXSTDTC = EXENDTC`. Given the dosing schedule (Cycle 1 Day 1, Cycle 1 Day 15, then Day 1 of every subsequent cycle), the minimum number of records  would be two, one for the first two doses given at a frequence of every 14 days, and a second for all the remaining injections, with a frequency of every 28 days.  Practically, since patient visits drift off-schedule the one record per dose approach is probably more practical. 
A single record could be used for everolimus with `EXFREQ = "OD"` for everolimus and `EXSTDTC` and `EXENDTC` the start and end dates of the series of tablets.


The `EXTRT` value `"STUDY DRUG"` is wrong.  `EXTRT` would have the actual study drug. A blinded representation is possible in the EC dataset. However, neither of the two study drugs is given at 100 mg.  Fulvestrant is given as injections of 250 or 500 mg on particular days.  Everolimus or matching placebo pills are given every day.  The `ECTRT` value would probably be something like "Everolimus/Placebo" with a unit of "TABLET".


It is likely that this study, which is blinded, would have both `EC` and `EX`.  For analysis, `EX` is the one needed.  The true drug names would be in `EXTRT` and dose would be expressed in mg for both drugs.
In the current dataset, the dates in `EXSTDTC` and `EXENDTC` might be meant as the first and last dates of any treatment.  Those dates are derived from `EX` and represented in the DM dataset in `RFXSTDTC` and `RFXENDTC`.
