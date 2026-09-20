// Phase 8C -- the useAuth() hook, split from AuthContext.jsx (see
// authContextObject.js's comment for why).

import { useContext } from "react";
import { AuthContext } from "./authContextObject";

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
