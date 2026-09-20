// Phase 8C -- Sign Up page. Uses the existing design system (PageHeader,
// Card, FormField/FormSection from the Phase 7C analysis form, Button,
// ErrorState) -- no new visual style is introduced.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { describeAuthError } from "../auth/authErrors";
import { validateConfirmPassword, validateEmail, validatePassword } from "../auth/validateAuthForm";
import FormField from "../components/analysis/FormField";
import FormSection from "../components/analysis/FormSection";
import Button from "../components/common/Button";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";

function SignUpPage() {
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const [formState, setFormState] = useState({ email: "", password: "", confirmPassword: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  // status: "idle" | "submitting" | "confirm-email" | "error". There is no
  // lingering "success-with-session" state -- that case navigates away
  // immediately, matching AnalysisForm's existing submission pattern.
  const [submission, setSubmission] = useState({ status: "idle", message: "" });

  function updateField(field) {
    return (event) => setFormState((prev) => ({ ...prev, [field]: event.target.value }));
  }

  function validate() {
    const errors = {
      email: validateEmail(formState.email),
      password: validatePassword(formState.password),
      confirmPassword: validateConfirmPassword(formState.password, formState.confirmPassword),
    };
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
    const { data, error } = await signUp(formState.email.trim(), formState.password);

    if (error) {
      setSubmission({ status: "error", message: describeAuthError(error, "Unable to create your account. Please try again.") });
      return;
    }

    // Supabase returns a session immediately only when email confirmation
    // is disabled for this project; otherwise `data.session` is null and
    // `data.user` exists unconfirmed -- both are genuine, normal outcomes
    // (Part 5). Never treat the user as signed in when no session exists.
    // UI-3: routes to /dashboard rather than "/" (the public landing page)
    // for the same reason as SignInPage's own redirect -- a freshly
    // authenticated user belongs on their dashboard.
    if (data.session) {
      navigate("/dashboard", { replace: true });
      return;
    }

    setSubmission({
      status: "confirm-email",
      message: "Account created. Please check your email to confirm your address before signing in.",
    });
  }

  const isSubmitting = submission.status === "submitting";

  return (
    <>
      <PageHeader title="Sign Up" description="Create an account to run and save your own procurement analyses." />

      <section className="page-section auth-page-section">
        <FormSection title="Create your account">
          {submission.status === "confirm-email" ? (
            <p className="text-body" role="status">
              {submission.message}
            </p>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit} noValidate>
              <FormField id="signup-email" label="Email" error={fieldErrors.email}>
                <input
                  id="signup-email"
                  type="email"
                  autoComplete="email"
                  value={formState.email}
                  onChange={updateField("email")}
                  disabled={isSubmitting}
                />
              </FormField>

              <FormField id="signup-password" label="Password" error={fieldErrors.password}>
                <input
                  id="signup-password"
                  type="password"
                  autoComplete="new-password"
                  value={formState.password}
                  onChange={updateField("password")}
                  disabled={isSubmitting}
                />
              </FormField>

              <FormField id="signup-confirm-password" label="Confirm password" error={fieldErrors.confirmPassword}>
                <input
                  id="signup-confirm-password"
                  type="password"
                  autoComplete="new-password"
                  value={formState.confirmPassword}
                  onChange={updateField("confirmPassword")}
                  disabled={isSubmitting}
                />
              </FormField>

              <div className="auth-form-actions">
                <Button type="submit" variant="primary" disabled={isSubmitting} aria-busy={isSubmitting}>
                  {isSubmitting ? "Creating account…" : "Sign Up"}
                </Button>
              </div>

              {submission.status === "error" && (
                <ErrorState title="Could not create your account" description={submission.message} />
              )}
            </form>
          )}

          <p className="text-small auth-switch-link">
            Already have an account? <Button to="/signin" variant="outline">Sign In</Button>
          </p>
        </FormSection>
      </section>
    </>
  );
}

export default SignUpPage;
