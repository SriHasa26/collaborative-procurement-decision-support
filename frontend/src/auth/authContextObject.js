// Phase 8C -- the bare context object, split into its own file purely so
// that AuthContext.jsx (a component) and useAuth.js (a hook) can each
// export exactly one kind of thing -- oxlint's react/only-export-components
// rule (Fast Refresh) flags a file that mixes a component export with a
// non-component export, which AuthContext.jsx originally did.

import { createContext } from "react";

export const AuthContext = createContext(undefined);
