// Phase 8C -- Sign In page. Same visual design as SignUpPage (Part 6).
// After a successful sign-in, returns the user to whatever protected page
// they originally requested (`location.state.from`, set by
// frontend/src/auth/ProtectedRoute.jsx) rather than always landing on Home.
// UI-3 -- the default (no `from`, i.e. the user navigated here directly)
// changed from "/" to "/dashboard": "/" is now the public landing page
// (UI-2), and a person who just signed in almost certainly wants their
// authenticated dashboard, not to be sent back to the marketing page they
// signed in from. This is a routing-target change only -- signIn()/
// AuthContext/ProtectedRoute are untouched.

import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { describeAuthError } from "../auth/authErrors";
import { validateEmail, validatePassword } from "../auth/validateAuthForm";
import FormField from "../components/analysis/FormField";
import FormSection from "../components/analysis/FormSection";
import Button from "../components/common/Button";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";

function SignInPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || "/dashboard";

  const [formState, setFormState] = useState({ email: "", password: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [submission, setSubmission] = useState({ status: "idle", message: "" });

  function updateField(field) {
    return (event) => setFormState((prev) => ({ ...prev, [field]: event.target.value }));
  }

  function validate() {
    const errors = { email: validateEmail(formState.email), password: validatePassword(formState.password) };
    setFieldErrors(errors);
    return Object.values(errors).every((message) => !message);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    // Duplicate-submission guard, matching AnalysisForm's existing pattern.
    if (submission.status === "submitting") return;

    if (!validate()) {
      setSubmission({ status: "idle", message: "" });
      return;
    }

    setSubmission({ status: "submitting", message: "" });
    const { error } = await signIn(formState.email.trim(), formState.password);

    if (error) {
      setSubmission({ status: "error", message: describeAuthError(error, "Unable to sign in. Please try again.") });
      return;
    }

    // AuthContext's own onAuthStateChange listener has already updated
    // `user`/`session` by the time this promise resolves -- this
    // navigation only decides WHERE to go next, it does not itself grant
    // access to anything.
    navigate(redirectTo, { replace: true });
  }

  const isSubmitting = submission.status === "submitting";

  return (
    <>
      <PageHeader title="Sign In" description="Sign in to analyze procurement and view your run history." />

      <section className="page-section auth-page-section">
        <FormSection title="Sign in to your account">
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <FormField id="signin-email" label="Email" error={fieldErrors.email}>
              <input
                id="signin-email"
                type="email"
                autoComplete="email"
                value={formState.email}
                onChange={updateField("email")}
                disabled={isSubmitting}
              />
            </FormField>

            <FormField id="signin-password" label="Password" error={fieldErrors.password}>
              <input
                id="signin-password"
                type="password"
                autoComplete="current-password"
                value={formState.password}
                onChange={updateField("password")}
                disabled={isSubmitting}
              />
            </FormField>

            <div className="auth-form-actions">
              <Button type="submit" variant="primary" disabled={isSubmitting} aria-busy={isSubmitting}>
                {isSubmitting ? "Signing in…" : "Sign In"}
              </Button>
            </div>

            {submission.status === "error" && (
              <ErrorState title="Sign in failed" description={submission.message} />
            )}
          </form>

          <p className="text-small auth-switch-link">
            Don't have an account? <Button to="/signup" variant="outline">Sign Up</Button>
          </p>
        </FormSection>
      </section>
    </>
  );
}

export default SignInPage;
