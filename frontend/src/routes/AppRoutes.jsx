// Phase 7A -- routing foundation only. Every page below is a placeholder;
// no real workflow is wired up yet.

import { Route, Routes } from "react-router-dom";
import Layout from "../components/layout/Layout";
import AnalysisPage from "../pages/AnalysisPage";
import HistoryPage from "../pages/HistoryPage";
import HomePage from "../pages/HomePage";
import NotFoundPage from "../pages/NotFoundPage";
import ResultsPage from "../pages/ResultsPage";

function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/analyze" element={<AnalysisPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default AppRoutes;
