# Candidate ID Convention

Use deterministic candidate IDs so comparison results are easy to sort and reproduce.

Recommended format:

```text
{parameter_set_id}__{assumption_set_id}__{render_mode}
```

Examples:

```text
bp-core-burner-075in__baseline-e-axis-g-face-i-face__flash-sheet
bp-core-burner-075in__i-axis-no-flat__part-rammer-01
stinger-075in__i-face-flatlip-002A__i-focused
```

Recommended assumption shorthand:

```text
EAXIS       E measured from part axis
EPERP       E measured from perpendicular/radial face
EINCL       E is included angle
GFACE       G measured from shoulder face
GAXIS       G measured from axis
GSQ0        G=0 produces square shoulder
IFACE       I measured from working face
IAXIS       I measured from axis
IFLAT0      no flat before bore opening
IFLATX      small flat before bore opening
GMARK       no-pass line drawn mark only
GGROOVE     no-pass line rendered as physical groove
```
