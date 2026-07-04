import type { FieldMeta } from "./types";

export const fieldMeta: FieldMeta[] = [
  { key: "a", code: "A", label: "Tube I.D.", hint: "Finished tube inner diameter." },
  { key: "b", code: "B", label: "Tube length", hint: "Overall loaded tube length." },
  { key: "c", code: "C", label: "Spindle length", hint: "Length of the nozzle-forming spindle." },
  { key: "d", code: "D", label: "Spindle width", hint: "Spindle root width and full-depth bore diameter." },
  { key: "e", code: "E", label: "Spindle taper", hint: "Spindle side taper angle." },
  { key: "f", code: "F", label: "Collar height", hint: "Base collar height on the spindle." },
  { key: "g", code: "G", label: "Collar taper", hint: "Shoulder taper between tube diameter and spindle root." },
  { key: "h", code: "H", label: "# of rammers", hint: "Number of separate rammer tools." },
  { key: "i", code: "I", label: "'A' rammer taper", hint: "First full-length rammer nozzle-back taper." },
];
