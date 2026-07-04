# 06 — Suggested Manual Validation Workflow

## Goal

Use the harness to settle ambiguous conventions with the least amount of manual effort.

## Phase 1 — Confirm fixed known truths visually

Use all preset screenshots.

Review these as yes/no visual checks:

```text
Each preset shows one spindle plus H rammers.
All visible rammer bores are straight open-bottom cylindrical bore projections.
I appears only on the first/longest rammer where nonzero.
G = 0 presets show square collar shoulder behavior.
I = 0 presets suppress the first/longest rammer taper.
The no-pass line appears at ri = 1.5*A on all rammers.
```

Record each check in the review template.

## Phase 2 — E convention test

Use presets with long enough spindles and nonzero E:

```text
BP Core Burner
Long Winded Screamer
Strobe
Whistle Pusher
```

Render candidates:

```text
E from axis
E from perpendicular
E as included angle
```

Look mainly at:

```text
spindle taper side slope
derived tip diameter d2
alignment of D/root and d2/tip labels
```

Expected result: `E from axis` should dominate.

## Phase 3 — G convention test

Use presets with nonzero G and zero G:

```text
Nonzero G: BP Core Burner, BP End Burner, Whistle Standard, Long Winded Screamer, Stinger, Strobe
Zero G: Whistle Pusher, Fountain/Gerb
```

Render candidates:

```text
G from shoulder face using Flash formula points
G from axis
square shoulder when G=0
zero-slope taper when G=0
```

Look mainly at:

```text
collar transition position
small angled shoulder on spindle
whether G=0 collapses cleanly to a square shoulder
```

Expected result: Flash formula / shoulder-face convention with square `G=0` behavior.

## Phase 4 — I convention test

Use only presets with nonzero I first:

```text
BP Core Burner
BP End Burner
Stinger
Fountain/Gerb
```

Render candidates:

```text
I external backside nozzle taper, angle from face, ending at bore opening
I external backside nozzle taper, angle from axis, ending at bore opening
I external taper with small flat before bore opening
I internal chamfer to bore opening
```

Look mainly at:

```text
first/longest rammer working end
relationship between taper endpoint and bore opening
whether any flat land is visible or only implied by stroke/aliasing
whether I appears on any later rammer
```

Expected result based on known truths: external backside nozzle taper on the first/longest rammer, ending at the bore opening. The harness should decide the angle reference convention and whether the screenshot implies a visible flat.

## Phase 5 — Bore interpretation test

Use presets with multiple rammers:

```text
BP Core Burner, H = 4
Long Winded Screamer, H = 4
Strobe, H = 3
Whistle Standard, H = 3
Whistle Pusher, H = 3
```

Review:

```text
bore width progression
bore depth progression
open-bottom behavior
square hidden bore bottom
relationship of bore dimensions to C/(H-1) and hci
```

Expected result: the dashed rectangles match true open-bottom cylindrical blind bores shown in hidden-line style.

## Phase 6 — Groove/no-pass line test

Use every preset.

Render candidates:

```text
drawn mark only
shallow physical groove
shoulder step
```

The review question is not whether the line is meaningful; it is whether the original screenshot visually implies actual side-profile geometry.

Expected result: drawn mark only should match Flash. Production CAD may still choose to model a shallow engraved line if separately specified.

## Phase 7 — Produce a decision log

For every ambiguity, record:

```text
accepted convention
rejected alternatives
best supporting screenshots
remaining caveats
whether production CAD should match Flash exactly or apply additional manufacturing metadata
```

Use `templates/review-report-template.md` for each focused run.
