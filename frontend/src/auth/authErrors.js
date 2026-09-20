// Phase 8C -- converts a Supabase Auth error into a friendly, honest
// message. Mirrors frontend/src/components/analysis/AnalysisForm.jsx's
// existing describeSubmissionError() pattern: match on the message
// Supabase actually returns, never invent a more specific cause than it
// actually provides, never surface a raw stack trace.

export function describeAuthError(error, fallback = "Something went wrong. Please try again.") {
  if (!error) return fallback;
  const message = typeof error.message === "string" ? error.message : String(error);

  if (/invalid login credentials/i.test(message)) {
    return "Incorrect email or password. Please try again.";
  }
  if (/email not confirmed/i.test(message)) {
    return "Please confirm your email address before signing in — check your inbox for a confirmation link.";
  }
  if (/already registered|already exists/i.test(message)) {
    return "An account with this email already exists. Try signing in instead.";
  }
  if (/password should be at least/i.test(message)) {
    // Supabase's own message already states the exact minimum length --
    // genuinely more specific/useful than any fallback we could write.
    return message;
  }
  if (/rate limit|too many requests/i.test(message)) {
    return "Too many attempts. Please wait a moment and try again.";
  }
  if (/failed to fetch|network/i.test(message)) {
    return "Unable to reach the authentication service. Please check your connection and try again.";
  }
  if (/not configured/i.test(message)) {
    return message;
  }

  return fallback;
}
