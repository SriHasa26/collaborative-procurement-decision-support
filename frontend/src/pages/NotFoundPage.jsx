import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <section>
      <h1>404 — Page Not Found</h1>
      <p>
        <Link to="/">Return to the Home Page</Link>
      </p>
    </section>
  );
}

export default NotFoundPage;
