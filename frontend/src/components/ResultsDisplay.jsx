import MonthlyRevenueChart from './MonthlyRevenueChart';

function ResultsDisplay({ results }) {
  if (!results) {
    return <div>No results available</div>;
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value) => {
    if (!value || isNaN(value)) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className="results-display">
      <h2>Optimization Results</h2>

      {/* Optimal Configuration */}
      <div className="results-section">
        <h3>Optimal Configuration</h3>
        <div className="results-grid">
          <div className="result-card">
            <div className="result-label">Optimal PV Size</div>
            <div className="result-value">{results.optimal_pv_size_mw.toFixed(2)} MW</div>
          </div>
          <div className="result-card">
            <div className="result-label">Optimal BESS Size</div>
            <div className="result-value">{results.optimal_bess_size_mwh.toFixed(2)} MWh</div>
          </div>
          <div className="result-card">
            <div className="result-label">Total CAPEX</div>
            <div className="result-value">{formatCurrency(results.capex_total)}</div>
          </div>
        </div>
      </div>

      {/* Financial Metrics */}
      <div className="results-section">
        <h3>Financial Metrics (25-Year Project Life)</h3>
        <div className="results-grid">
          <div className="result-card highlight">
            <div className="result-label">Net Present Value (NPV)</div>
            <div className="result-value large">{formatCurrency(results.npv)}</div>
          </div>
          <div className="result-card highlight">
            <div className="result-label">Internal Rate of Return (IRR)</div>
            <div className="result-value large">{formatPercent(results.irr)}</div>
          </div>
          <div className="result-card">
            <div className="result-label">Total Revenue (25 Years)</div>
            <div className="result-value">{formatCurrency(results.total_revenue_25_years)}</div>
          </div>
        </div>
      </div>

      {/* Monthly Revenue Chart */}
      {results.monthly_revenues && results.monthly_revenues.length > 0 && (
        <div className="results-section">
          <h3>Monthly Revenue Over 25 Years</h3>
          <MonthlyRevenueChart data={results.monthly_revenues} />
        </div>
      )}

      {/* Additional Info */}
      {results.representative_days_used && (
        <div className="results-section info">
          <p>
            <strong>Note:</strong> Optimization used {results.scale_factor?.toFixed(2)}x scaling 
            from 52 representative days to represent the full year.
          </p>
        </div>
      )}
    </div>
  );
}

export default ResultsDisplay;
