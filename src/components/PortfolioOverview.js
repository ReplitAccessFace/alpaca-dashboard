import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PortfolioOverview = () => {
  const [accountData, setAccountData] = useState(null);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [accountResponse, positionsResponse] = await Promise.all([
        axios.get('http://localhost:8000/api/account'),
        axios.get('http://localhost:8000/api/positions')
      ]);
      
      setAccountData(accountResponse.data);
      setPositions(positionsResponse.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch data. Make sure the backend server is running.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercent = (percent) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', color: '#666' }}>Loading your portfolio data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', color: '#ef4444' }}>{error}</div>
        <button 
          onClick={fetchData}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!accountData) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', color: '#666' }}>No account data available</div>
      </div>
    );
  }

  const dayChange = accountData.equity - accountData.last_equity;
  const dayChangePercent = accountData.last_equity > 0 ? (dayChange / accountData.last_equity) * 100 : 0;

  return (
    <div>
      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total Portfolio Value</div>
          <div className="metric-value">{formatCurrency(accountData.portfolio_value)}</div>
          <div className={dayChange >= 0 ? 'positive' : 'negative'}>
            {formatCurrency(Math.abs(dayChange))} ({formatPercent(dayChangePercent)}) today
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Total Return</div>
          <div className="metric-value positive">{formatCurrency(accountData.equity - accountData.cash)}</div>
          <div className="positive">
            {accountData.cash > 0 ? formatPercent(((accountData.equity - accountData.cash) / accountData.cash) * 100) : '0.00%'} all time
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Buying Power</div>
          <div className="metric-value">{formatCurrency(accountData.buying_power)}</div>
          <div style={{ color: '#666' }}>Available for trading</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Active Positions</div>
          <div className="metric-value">{positions.length}</div>
          <div style={{ color: '#666' }}>Current holdings</div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="card">
        <h3>Current Positions</h3>
        {positions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
            No open positions
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Value</th>
                <th>Unrealized P&L</th>
                <th>P&L %</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position, index) => (
                <tr key={index}>
                  <td><strong>{position.symbol}</strong></td>
                  <td>{position.qty}</td>
                  <td>{formatCurrency(position.market_value)}</td>
                  <td className={position.unrealized_pl >= 0 ? 'positive' : 'negative'}>
                    {formatCurrency(position.unrealized_pl)}
                  </td>
                  <td className={position.unrealized_plpc >= 0 ? 'positive' : 'negative'}>
                    {formatPercent(position.unrealized_plpc * 100)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default PortfolioOverview;