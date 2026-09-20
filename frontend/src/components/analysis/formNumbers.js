// Phase 7C -- shared numeric-string helpers for the analysis form.
//
// CRITICAL RULE (explicitly required by this phase's spec): an empty text
// input must never silently become the number 0. `Number("")` evaluates to
// `0` in JavaScript, which would corrupt the null/optional distinction the
// backend schema (backend/api/schemas.py) relies on -- every helper below
// checks for an empty/whitespace-only string FIRST and returns a distinct
// "empty" result before ever calling Number()/parseFloat().

export const EMPTY = Symbol("empty-numeric-input");
export const INVALID = Symbol("invalid-numeric-input");

// Parses one numeric text field. Returns EMPTY for "" / whitespace-only
// (the caller decides whether that means "send null" or "required field
// missing"), INVALID for non-numeric text, or the parsed finite number.
export function parseNumericField(rawValue) {
  if (rawValue === null || rawValue === undefined) return EMPTY;
  const trimmed = String(rawValue).trim();
  if (trimmed === "") return EMPTY;

  const parsed = Number(trimmed);
  if (Number.isNaN(parsed) || !Number.isFinite(parsed)) return INVALID;
  return parsed;
}

// Parses one numeric field for a REQUIRED backend value: returns null only
// to signal "empty" (caller must then raise a validation error -- required
// fields are never silently defaulted), INVALID for unparseable text, or
// the number.
export function parseRequiredNumber(rawValue) {
  return parseNumericField(rawValue);
}

// Parses one numeric field for an OPTIONAL backend value (Optional[float]/
// Optional[int] in backend/api/schemas.py): empty input maps to `null`
// (preserving the backend's real null/optional distinction), a parseable
// value maps to the number, and unparseable text is reported as INVALID so
// the caller can show a structural error instead of guessing.
export function parseOptionalNumber(rawValue) {
  const result = parseNumericField(rawValue);
  if (result === EMPTY) return null;
  return result; // number, or INVALID
}

// Parses a comma-separated list of numbers (diary_records / peer_q_values).
// An empty/untouched field maps to `null` (matching Optional[List[float]] =
// None in backend/api/schemas.py) -- there is no UI affordance in this
// phase for explicitly submitting an empty array `[]`, since no natural
// user action would produce that intent (documented as a known
// simplification in the Phase 7C report).
export function parseOptionalNumberList(rawValue) {
  if (rawValue === null || rawValue === undefined) return null;
  const trimmed = String(rawValue).trim();
  if (trimmed === "") return null;

  const parts = trimmed.split(",").map((part) => part.trim()).filter((part) => part !== "");
  const numbers = [];
  for (const part of parts) {
    const value = Number(part);
    if (Number.isNaN(value) || !Number.isFinite(value)) return INVALID;
    numbers.push(value);
  }
  return numbers;
}
