# 07 — What to Automate vs Human Review

## Automate

### Parameter and derived-value checks

Automate:

```text
ri = 1.5*A
d2 computation
hci computation
stage bore depths
stage bore diameters
stage total lengths
H rammer count
I present/suppressed based on nonzero I
G square shoulder when G=0
```

These are deterministic and should not need visual judgment.

### Candidate rendering

Automate all candidate renders from parameter + assumption set.

### Basic alignment

Automate scale/translate alignment once manual anchors are provided.

### Feature measurements

Automate:

```text
outer bounding boxes
endpoint errors
line angle errors
bore rectangle width/depth errors
number of rammers
presence/absence of I taper
presence/absence of G shoulder taper
presence/absence of no-pass line
```

### Contact sheets and reports

Automate:

```text
candidate/reference overlay
difference image
ranked score table
per-feature flag list
review report stub
```

## Keep human-reviewed

### Final interpretation of ambiguous features

Human review should decide:

```text
E angle convention if candidates are visually close
G angle convention if Flash drawing is too low-res
I angle reference convention
whether a tiny flat exists at the bore opening or is rasterization
whether groove should be modeled physically in final solids
whether dimension placement matters for compatibility mode
```

### Screenshot annotations

Manual annotation is acceptable and probably faster than building a fully automatic detector.

Human should provide:

```text
region boxes for spindle and each rammer
anchor points
feature endpoint points for E/G/I when needed
notes about ambiguous aliasing or cropping
```

### Rejection of false positives

Automated scores can be fooled by large matching areas. Human review should reject candidates that match overall outline but get the target ambiguity wrong.

## Avoid automating initially

Do not initially automate:

```text
OCR of labels
perfect Flash font matching
automatic detection of all dimension arrows
automatic part segmentation for every screenshot
production CAD model decisions
```

Those are expensive and not required for the first-pass geometry convention decision.

## Decision standard

A convention should be accepted only when:

```text
it wins on multiple presets
it wins on the focused feature score
it is visually plausible in overlays
it does not require preset-specific hacks
it agrees with known truths and formulas
```

A convention should remain unresolved when:

```text
only one screenshot supports it
candidate differences are below screenshot resolution
text/dimension clutter obscures the feature
two conventions produce visually indistinguishable results
```
