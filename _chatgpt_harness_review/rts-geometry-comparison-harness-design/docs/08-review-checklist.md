# 08 — Review Checklist

Use this checklist after each comparison run.

## Per-preset checks

```text
[ ] Correct preset parameters loaded.
[ ] Correct units loaded.
[ ] H rammers rendered.
[ ] Spindle length and collar height agree visually.
[ ] Spindle tip diameter visually plausible.
[ ] G shoulder behavior matches screenshot.
[ ] First/longest rammer has I taper only when I is nonzero.
[ ] I taper endpoint reaches bore opening.
[ ] Hollow rammer bores are open-bottom and straight.
[ ] Bore depths progress correctly across stages.
[ ] Bore diameters progress correctly across stages.
[ ] No-pass line appears at ri = 1.5*A.
[ ] Second practical change line is absent in Flash-like render.
[ ] Dimension annotations do not interfere with geometry comparison.
```

## Focused ambiguity decision fields

### E — spindle taper

```text
Accepted convention:
Rejected alternatives:
Best screenshots:
Reason:
Remaining caveat:
```

### G — collar taper

```text
Accepted convention:
Rejected alternatives:
Best screenshots:
Reason:
Remaining caveat:
```

### I — A/first/longest rammer taper

```text
Accepted convention:
Rejected alternatives:
Best screenshots:
Reason:
Remaining caveat:
```

### Groove/no-pass line

```text
Flash drawing representation:
Production solid representation:
Best screenshots:
Reason:
Remaining caveat:
```

## Candidate rejection reasons

```text
[ ] Wrong number of rammers.
[ ] Wrong spindle tip diameter.
[ ] Wrong G shoulder convention.
[ ] Wrong I taper placement.
[ ] Wrong I taper endpoint.
[ ] Shows I taper on wrong rammer.
[ ] Treats bore as closed-bottom when screenshot implies open-bottom.
[ ] Treats dashed rectangle as external geometry.
[ ] Adds second change line not shown in screenshot.
[ ] Makes no-pass line into visible shoulder/groove that screenshot does not show.
```
