import React, { useState } from 'react';
import PortfolioOverview from './components/PortfolioOverview';
import PerformanceChart from './components/PerformanceChart';
import TradeHistory from './components/TradeHistory';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="app">
      <header className="app-header">
        <h1>📈 Alpaca Trading Dashboard</h1>
        <p>Local Development - Monitor your trading performance</p>
      </header>

      <nav className="tab-navigation">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Portfolio Overview
        </button>
        <button 
          className={activeTab === 'performance' ? 'active' : ''}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
        <button 
          className={activeTab === 'trades' ? 'active' : ''}
          onClick={() => setActiveTab('trades')}
        >
          Trade History
        </button>
      </nav>

      <main className="app-main">
        <ErrorBoundary>
          {activeTab === 'overview' && <PortfolioOverview />}
          {activeTab === 'performance' && <PerformanceChart />}
          {activeTab === 'trades' && <TradeHistory />}
        </ErrorBoundary>
      </main>

      <footer className="app-footer">
        <p>Running on localhost - Ready for Alpaca API integration</p>
      </footer>
    </div>
  );
}

export default App;