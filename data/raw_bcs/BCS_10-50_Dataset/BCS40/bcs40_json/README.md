# 40th BCS - topic JSON collection

This folder follows the supplied demo schema and is separate from the other PDFs.

## Contents

18 topic files (one questions/answers pair per topic), containing 21 annotated questions. Another 7 source questions are isolated in the two review_required files. Empty topic files are valid [] arrays.

The assets folder contains input figures and graphical options. Keep it beside the JSON. The audit_assets folder contains source excerpts INCLUDING printed keys: for human auditing only, never question-model inputs.

source_index.json records the source page, original key, evidence crop and interpretation notes for every selected question. manifest.json, quality_report.json and asset_index.json document counts, provenance and caveats. validate.py and validation_report.json provide reproducible structural checks.

## Language and annotations

Questions retain their source language, predominantly Bangla. Existing English terms and formulae are not translated into English questions. Graphical content uses ![label](assets/filename.png) inside the existing string fields. JSON is UTF-8 with readable Bangla.

correct_answer preserves the PDF's printed key. Solutions, subskills, classifications, glossaries, difficulty ratings, time estimates and mistake traces are MODEL-GENERATED annotations, not extracted printed explanations. Estimates are not empirically calibrated.

The answers files contain hypothetical mistakes linked by family_id, not a second list of correct answers. These are synthetic examples, not observed learner responses. Wrong answers may be outside the multiple-choice alternatives. diverges_at_step is the first erroneous step within that mistake's own trace (1-based). Only meaningful mistake types are supplied for a question, not an artificial fixed number of types.

## Review and fidelity

Review questions are excluded from topic files. They retain source wording/options/keys but have empty solution and mistake arrays and null difficulty/time. Missing keys remain null. Do not treat their source keys as verified labels. Read quality_report.json and source_index.json before training or assessment use.

Spacing and mathematical layout are normalized for JSON readability; exact typography remains in the audit crop. No substantive typo, missing dimension, incorrect key or missing instruction has been silently repaired. Original diagram markings, including crossed-out marks, are retained.

Only the nine requested math/reasoning topics are collected, not the whole exam. Out-of-scope source question numbers are in the manifest. Topic follows the main solving skill, not merely a word or number in the stem.

## IDs and leakage

Q### is unique only within this PDF. Use the folder or source_uid to join across exams. Repeated source occurrences are retained; group duplicates and near-duplicates before splitting training/evaluation data.

Use only question_bn and answer_options as question inputs. Do not include correct_answer, solution_steps, mistake files, source-index keys or audit crops in evaluation inputs.

## Validate

Run python validate.py in this folder. The checks cover JSON/schema validity, paired IDs, review isolation and referenced files. A passing structural check does not guarantee every source key or pedagogical annotation is correct.
