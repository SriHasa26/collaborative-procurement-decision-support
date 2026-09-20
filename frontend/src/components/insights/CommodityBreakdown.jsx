// UI-7 -- Section 7: Commodity Analysis. Reuses the existing
// `.history-table`/`.history-table-wrapper` classes (components.css --
// already used by results/AllocationTable.jsx and
// results/VendorOutcomesTable.jsx) rather than a third table
// implementation. Commodity IDs (e.g. "POTATO_HYD_2026_09") are shown
// exactly as the backend returns them -- never rewritten into an
// invented human-friendly name. Sorted by run count only (a plain
// frequency count); no commodity is ever labeled "best".

import { formatCurrency } from "../results/resultHelpers";

function CommodityBreakdown({ commodityBreakdown }) {
  if (commodityBreakdown.length === 0) return null;

  return (
    <section className="page-section" aria-labelledby="commodity-breakdown-heading">
      <h2 id="commodity-breakdown-heading" className="section-title">
        Commodity Analysis
      </h2>
      <p className="text-small text-muted">Runs by commodity, ordered by number of analyzed runs.</p>

      <div className="history-table-wrapper">
        <table className="history-table">
          <thead>
            <tr>
              <th scope="col">Commodity</th>
              <th scope="col">Runs</th>
              <th scope="col">Expected savings</th>
            </tr>
          </thead>
          <tbody>
            {commodityBreakdown.map((row) => (
              <tr key={row.commodity}>
                <td>{row.commodity}</td>
                <td>{row.runCount}</td>
                <td>
                  {row.savingsRunCount > 0 ? (
                    <>
                      {formatCurrency(row.savingsTotal)}
                      {row.savingsRunCount < row.runCount && (
                        <span className="text-small text-muted"> (from {row.savingsRunCount} of {row.runCount} runs)</span>
                      )}
                    </>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default CommodityBreakdown;
