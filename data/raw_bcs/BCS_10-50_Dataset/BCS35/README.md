# BCS 35 Math JSON Collection

This package keeps the earlier demo-compatible question/answer JSON format and adds a research-benchmark layer based on the GonitSathi RA guideline.

## Main set
- In-scope solved items: 10
- Core items needing review: 1
- Authored controlled histories: 40 (4 per main item)

## Scope
Only the six initial topic groups are in the main set: percentages/profit-loss; ratios/proportions; work/time; speed/distance; averages/mixtures; elementary algebra/number relations. Geometry, set theory, probability, combinatorics, and mental-ability-only items are logged in `excluded_out_of_scope.json`.

## Important research note
The source questions/options/printed answers come from the supplied PDF. Solutions, possible mistakes, controlled histories, evaluator labels, probes, difficulty and timing annotations are model-authored drafts. They must be independently reviewed by mathematically competent Bengali-speaking annotators before being used as gold test labels. Ambiguous or defective source questions are kept in `review_required.json` rather than forced into the main data.
