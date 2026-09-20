// Phase 8C -- minimal, shared client-side validation for the Sign Up/Sign
// In forms. Deliberately does NOT invent a password-strength rule --
// Supabase's own project configuration is the actual authority on password
// requirements (e.g. minimum length), and its response message is passed
// through as-is when it rejects one (see authErrors.js).

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email) {
  if (!email.trim()) return "Email is required.";
  if (!EMAIL_PATTERN.test(email.trim())) return "Enter a valid email address.";
  return "";
}

export function validatePassword(password) {
  if (!password) return "Password is required.";
  return "";
}

export function validateConfirmPassword(password, confirmPassword) {
  if (!confirmPassword) return "Please confirm your password.";
  if (password !== confirmPassword) return "Passwords do not match.";
  return "";
}
