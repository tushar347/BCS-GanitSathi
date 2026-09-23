# 45th BCS: mathematics and reasoning JSON collection

## Contents

The nine topic pairs contain **26 included questions**, with one matching mistake-analysis record per question and **76 model-generated hypothetical mistake traces**. A further **3 source questions are extracted but held for review**, for a total of **29 extracted questions**. The supplied source has 19 pages; selected questions occur on PDF pages 14-18.

Each topic has `<topic>_questions.json` and `<topic>_answers.json`, using the same question and answer field names as the user's demo. All dataset files are UTF-8 JSON arrays. Bengali is stored as readable Unicode, not ASCII-escaped text.

## Important provenance distinction

The **question wording, option order, diagrams, and printed answer keys** come from the supplied PDF. The PDF does **not** contain the detailed solutions or error traces in these files.

**Topics/subskills, glossaries, difficulty ratings, estimated completion times, target quantities, worked solutions, and possible mistakes are model-generated annotations.** Difficulty and time values are estimates, not measured data. Mistake traces are hypothetical teaching examples, not observed student responses. Some generated wrong answers fall outside the supplied MCQ options; they are not additional source options. Q183 has only one meaningful visual-error example rather than fabricated arithmetic errors.

`correct_answer` retains the PDF's printed key. No source answer was silently replaced. `in_scope` means eligible for the selected taxonomy; it does not mean that a quarantined question is safe for training.

## Review-required records

Do not mix `review_required_questions.json` or `review_required_answers.json` into the nine topic datasets without reviewing the source issues:

- **Q164:** malformed printed identity; a plus sign is printed where an equality might have been intended, but no replacement is made.
- **Q178:** the referenced premises and conclusion are absent from the source.
- **Q186:** the printed mirror-image answer matches option b but appears inconsistent with a whole-word left-right reflection. The source key is preserved, not corrected.

These three records retain the same field names but use null difficulty/time estimates and empty `solution_steps` / `possible_mistakes`. Full notes and source-image evidence are in `quality_report.json` and `audit_assets/`.

## Diagram handling

Keep `assets/` next to the JSON files. Existing string fields contain Markdown image references, such as `![label](assets/Q181_option_a.png)`, so the sample's field types are preserved. `source_index.json` also lists image paths and visual transcriptions.

The included records **Q181, Q183, and Q187 require an image-aware reader**. Q186 is image-dependent but quarantined. For a strictly text-only dataset, filter out image-dependent records using `source_index.json`; do not discard the image links and pretend the question remains complete.

`audit_assets/` contains source excerpts that may include printed answers. **Never use these audit crops as model question inputs.** Only image paths explicitly referenced in the question/option fields are intended as question inputs.

## Source fidelity and assumptions

Broken embedded Bengali glyph mappings were resolved by inspecting rendered page images; no OCR was used. Spacing and mathematical typography are normalized, but source values, options, and operators are not repaired. Duplicated options in Q183 and octal distractors containing 8 in Q150 are preserved. The baseline `p2 + q2` in Q166 and `x2` in Q175 remain in their source form; their exponent interpretation is explicitly declared in the generated solutions.

Other conventions affecting memory addressing, natural pattern continuation, finite probability, digit reuse, signed-triad balance, and letter-position coding are documented per question in `source_index.json` and `quality_report.json`. Q170 is answered among the printed alternatives without claiming that its stated angle bound determines a unique real angle.

The allowed taxonomy is the demo's nine topics. Angle/trigonometry is mapped to geometry; elementary probability and digit-arrangement counting are mapped to broad arithmetic. These choices are documented. Factual questions are excluded even when their answers contain numbers. Pure IQ-category terminology and vocabulary recall are not treated as numerical/pattern reasoning.

## IDs and loading

`family_id` uses the original source question number, e.g. Q149. When combining PDFs, use `(source_id, family_id)` from `source_index.json` as the unique key, because another paper may use the same question numbers.

`<topic>_answers.json` contains **possible mistakes**, not the primary correct answer; the correct answer and generated worked solution are in `<topic>_questions.json`.

For an arithmetic mistake, `diverges_at_step` is the **1-based first erroneous step within that mistake's own `reasoning_steps`**, not an index into the correct solution.

## Validation

Run `python validate.py` in this folder. No third-party dependency is required for the delivered validator. `validation_report.json` records the checks performed during creation. The underlying source PDF is not duplicated in this package; its filename and SHA-256 digest are in `manifest.json`.
