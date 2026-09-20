// UI-7 -- Section 8: Vendor Participation. Only ever derived from runs
// whose full detail was fetched (input.vendor_submissions) -- the scope
// note below states this plainly rather than hiding it. No vendor is
// ever labeled "best"/"top"/"most reliable" -- only "most frequently
// observed", a plain frequency description the data actually supports.
//
// Unlike DecisionDistribution.jsx/GroupSizeAnalysis.jsx (a proportional
// bar chart of ONE run would visually overstate a single data point as a
// real distribution, per Rule 4), this is a plain factual TABLE -- one
// row per vendor actually observed, exactly the same kind of listing as
// CommodityBreakdown.jsx -- so it is shown starting at 1 considered run,
// not gated behind MIN_RUNS_FOR_DISTRIBUTION_VISUAL. A "most frequently
// observed vendor" SUPERLATIVE claim is a separate, stronger statement --
// that one IS gated behind the same threshold, inside
// insightsMetrics.js's buildEvidenceObservations().

import LimitedDataState from "./LimitedDataState";

function VendorParticipation({ vendorParticipation }) {
  const { vendors, consideredRunCount } = vendorParticipation;

  return (
    <section className="page-section" aria-labelledby="vendor-participation-heading">
      <h2 id="vendor-participation-heading" className="section-title">
        Vendor Participation
      </h2>

      {consideredRunCount === 0 ? (
        <LimitedDataState
          title="Not enough historical data"
          description="Vendor participation requires at least one run with detailed result data available."
          availableCount={0}
        />
      ) : (
        <>
          <p className="text-small text-muted">
            Calculated from {consideredRunCount} run(s) for which detailed result data is available.
          </p>
          <div className="history-table-wrapper">
            <table className="history-table">
              <thead>
                <tr>
                  <th scope="col">Vendor ID</th>
                  <th scope="col">Observed in runs</th>
                  <th scope="col">Selected-group appearances</th>
                </tr>
              </thead>
              <tbody>
                {vendors.map((vendor) => (
                  <tr key={vendor.vendorId}>
                    <td>{vendor.vendorId}</td>
                    <td>{vendor.submittedCount}</td>
                    <td>{vendor.selectedCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

export default VendorParticipation;
