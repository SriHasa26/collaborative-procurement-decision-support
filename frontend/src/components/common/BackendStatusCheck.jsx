// Phase 7A -- TEMPORARY, CLEARLY-LABELED development connectivity check
// only (Step 9 of Phase 7A). This is NOT a status dashboard, NOT a health
// monitoring UI, and is not meant to survive as real product UI -- it
// exists solely to prove "React frontend -> FastAPI backend" works, by
// calling the real GET /health endpoint through the centralized API
// client. A later phase (7C onward) will replace or remove this.

import { useEffect, useState } from "react";
import { healthCheck } from "../../api/procurementApi";
import { API_BASE_URL } from "../../config/env";

function BackendStatusCheck() {
  const [state, setState] = useState({ status: "checking", detail: "" });

  useEffect(() => {
    let cancelled = false;

    healthCheck()
      .then((body) => {
        if (!cancelled) setState({ status: "ok", detail: JSON.stringify(body) });
      })
      .catch((error) => {
        if (!cancelled) setState({ status: "error", detail: error.message });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="backend-status-check">
      <p>
        <strong>Phase 7A development connectivity check (temporary)</strong>
      </p>
      <p>Backend base URL: {API_BASE_URL}</p>
      <p>GET /health status: {state.status}</p>
      {state.detail && <p>Detail: {state.detail}</p>}
    </div>
  );
}

export default BackendStatusCheck;
