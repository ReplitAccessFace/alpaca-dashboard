import React, { useState, useEffect } from 'react';
import SimpleTradingViewChart from './SimpleTradingViewChart';
import axios from 'axios';

const PerformanceChart = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('all');
  const [selectedDate, setSelectedDate] = useState(() => {
    // Default to today (October 14th, 2025) to show trades
    return '2025-10-14';
  });
  const [symbols, setSymbols] = useState([]);
  const [tradesData, setTradesData] = useState({});
  const [marketData, setMarketData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const initializeData = async () => {
      // Always try to download today's data on initial load
      const today = new Date().toISOString().split('T')[0];
      console.log(`Auto-downloading latest data on load for today: ${today}`);
      
      try {
        // Download today's market data
        const marketResponse = await axios.post(`http://localhost:8000/api/performance/market-data/download-all?date=${today}`);
        console.log('Auto-download market data response:', marketResponse.data);
      } catch (error) {
        console.log('Auto-download market data failed:', error.message);
      }
      
      try {
        // Download today's trades
        const tradesResponse = await axios.post(`http://localhost:8000/api/performance/trades/download-all?start_date=${today}&days_back=1`);
        console.log('Auto-download trades response:', tradesResponse.data);
      } catch (error) {
        console.log('Auto-download trades failed:', error.message);
      }
      
      // Then fetch the main data
      await fetchTradesWithPrices();
    };
    
    initializeData();
  }, []);

  useEffect(() => {
    if (selectedSymbol && selectedSymbol !== 'all') {
      fetchMarketDataWithTrades(selectedSymbol, selectedDate).then(data => {
        if (data) {
          console.log('Market data received:', data);
          setMarketData(prev => ({
            ...prev,
            [selectedSymbol]: data
          }));
        }
      });
    }
  }, [selectedSymbol, selectedDate]);

  const fetchTradesWithPrices = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      console.log('Fetching trades with prices...');
      const response = await axios.get('http://localhost:8000/api/performance/trades-with-prices');
      
      if (!response.data) {
        throw new Error('No data received from API');
      }
      
      console.log('Fetched data:', response.data);
      console.log('Symbols:', response.data.symbols);
      
      // Validate response data structure
      if (!Array.isArray(response.data.symbols)) {
        console.warn('Invalid symbols array:', response.data.symbols);
        setSymbols([]);
      } else {
        setSymbols(response.data.symbols);
      }
      
      if (!response.data.data) {
        console.warn('No data object in response');
        setTradesData({});
      } else {
        setTradesData(response.data.data);
      }
      
      setError(null);
      
      // Auto-select first symbol if available
      if (response.data.symbols && Array.isArray(response.data.symbols) && response.data.symbols.length > 0) {
        console.log('Auto-selecting first symbol:', response.data.symbols[0]);
        setSelectedSymbol(response.data.symbols[0]);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch trading data. Make sure the backend server is running.');
      setSymbols([]);
      setTradesData({});
    } finally {
      console.log('Setting loading to false');
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchMarketDataWithTrades = async (symbol, date, isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      }
      
      if (!symbol || !date) {
        throw new Error('Symbol and date are required');
      }
      
      console.log('Fetching market data with trades for:', symbol, 'on date:', date);
      const response = await axios.get(`http://localhost:8000/api/performance/market-data/${symbol}/with-trades?start_date=${date}`);
      
      if (!response.data) {
        throw new Error('No data received from API');
      }
      
      console.log('Market data response:', response.data);
      
      // Validate response structure
      const data = response.data;
      if (!data.market_data) {
        console.warn('No market_data in response');
        data.market_data = [];
      }
      if (!data.trades) {
        console.warn('No trades in response');
        data.trades = [];
      }
      if (!data.trade_markers) {
        console.warn('No trade_markers in response');
        data.trade_markers = [];
      }
      
      // Check if we have data
      if (data.market_data && data.market_data.length === 0) {
        console.warn(`No market data found for ${symbol} on ${date}`);
        return { ...data, noData: true };
      }
      
      // Note: We now show all historical trades regardless of date
      // So we don't need to check for noTrades anymore
      
      return data;
    } catch (err) {
      console.error('Error fetching market data:', err);
      return { 
        error: err.message,
        market_data: [],
        trades: [],
        trade_markers: []
      };
    } finally {
      if (isRefresh) {
        setRefreshing(false);
      }
    }
  };

  const downloadAllMarketData = async () => {
    try {
      setLoading(true);
      console.log('Downloading market data for all symbols...');
      const response = await axios.post('http://localhost:8000/api/performance/market-data/download-all');
      
      console.log('Download results:', response.data);
      alert(`Downloaded market data for ${response.data.total_symbols} symbols!`);
      
      // Refresh the symbols list
      fetchTradesWithPrices();
    } catch (err) {
      console.error('Error downloading all market data:', err);
      alert('Failed to download market data. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const downloadAllHistoricalTrades = async () => {
    try {
      setLoading(true);
      console.log('Downloading all historical trades...');
      const response = await axios.post('http://localhost:8000/api/performance/trades/download-all');
      
      console.log('Download results:', response.data);
      alert(`Downloaded ${response.data.total_trades} historical trades from ${response.data.date_range.earliest_date} to ${response.data.date_range.latest_date}!`);
      
      // Refresh the data
      fetchTradesWithPrices();
    } catch (err) {
      console.error('Error downloading historical trades:', err);
      alert('Failed to download historical trades. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    console.log('Refreshing all data...');
    
    // Always try to download today's data first
    const today = new Date().toISOString().split('T')[0];
    console.log(`Auto-downloading latest data for today: ${today}`);
    
    try {
      // Download today's market data
      const marketResponse = await axios.post(`http://localhost:8000/api/performance/market-data/download-all?date=${today}`);
      console.log('Today\'s market data download response:', marketResponse.data);
    } catch (error) {
      console.log('Market data download failed:', error.message);
    }
    
    try {
      // Download today's trades
      const tradesResponse = await axios.post(`http://localhost:8000/api/performance/trades/download-all?start_date=${today}&days_back=1`);
      console.log('Today\'s trades download response:', tradesResponse.data);
    } catch (error) {
      console.log('Trades download failed:', error.message);
    }
    
    // Refresh the main data
    await fetchTradesWithPrices(true);
    
    // Also refresh market data for current symbol if selected
    if (selectedSymbol && selectedSymbol !== 'all') {
      const data = await fetchMarketDataWithTrades(selectedSymbol, selectedDate, true);
      if (data) {
        setMarketData(prev => ({
          ...prev,
          [selectedSymbol]: data
        }));
      }
    }
    
    // Try to download missing market data for the selected date (if different from today)
    if (selectedDate !== today) {
      try {
        console.log(`Attempting to download market data for ${selectedSymbol} on ${selectedDate}...`);
        const response = await axios.post(`http://localhost:8000/api/performance/market-data/download-all?date=${selectedDate}`);
        console.log('Selected date market data download response:', response.data);
        
        // Refresh the data after potential download
        if (selectedSymbol && selectedSymbol !== 'all') {
          const updatedData = await fetchMarketDataWithTrades(selectedSymbol, selectedDate, true);
          if (updatedData) {
            setMarketData(prev => ({
              ...prev,
              [selectedSymbol]: updatedData
            }));
          }
        }
      } catch (error) {
        console.log('No additional market data to download or download failed:', error.message);
      }
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Normalize a trade object to a timestamp in milliseconds
  const getTradeTimestampMs = (trade) => {
    // Common fields: time (seconds or ms), transaction_time (ISO)
    if (trade.time !== undefined && trade.time !== null) {
      const n = Number(trade.time);
      if (!Number.isNaN(n)) {
        return n > 1e12 ? n : n * 1000; // seconds -> ms if needed
      }
    }
    if (trade.transaction_time) {
      const t = Date.parse(trade.transaction_time);
      if (!Number.isNaN(t)) return t;
    }
    if (trade.filled_at) {
      const t = Date.parse(trade.filled_at);
      if (!Number.isNaN(t)) return t;
    }
    return undefined;
  };

  // Filter trades to the selected UTC date [start, end)
  const filterTradesByDate = (trades, dateStr) => {
    if (!trades || trades.length === 0) return [];
    if (!dateStr) return trades;
    const start = new Date(`${dateStr}T00:00:00Z`).getTime();
    const end = new Date(`${dateStr}T23:59:59.999Z`).getTime();
    return trades.filter((tr) => {
      const ts = getTradeTimestampMs(tr);
      return ts !== undefined && ts >= start && ts <= end;
    });
  };

  const calculateTradePerformance = (trades) => {
    if (!trades || trades.length === 0) return { totalTrades: 0, totalProfit: 0, winRate: 0 };

    // Sort trades by timestamp, handling both time (seconds) and transaction_time (ISO string)
    const sortedTrades = trades.sort((a, b) => {
      const timeA = a.time || (a.transaction_time ? new Date(a.transaction_time).getTime() / 1000 : 0);
      const timeB = b.time || (b.transaction_time ? new Date(b.transaction_time).getTime() / 1000 : 0);
      return timeA - timeB;
    });

    console.log('DEBUG: Calculating performance for trades:', sortedTrades.map(t => ({ side: t.side, qty: t.qty, price: t.price, time: t.time })));

    // Use the same logic as TradeHistory.js
    let profit = 0;
    let position = 0;
    let avgEntryPrice = 0;
    let completedTrades = 0;
    let winningTrades = 0;

    for (let i = 0; i < sortedTrades.length; i++) {
      const trade = sortedTrades[i];
      const qty = parseFloat(trade.qty) || 0;
      const price = parseFloat(trade.price) || 0;
      let tradeProfit = 0;
      
      console.log(`Processing trade: ${trade.side} ${qty} @ $${price}, position: ${position}, avgEntryPrice: ${avgEntryPrice}`);
      
      if (trade.side === 'buy' || trade.side === 'buy_to_cover') {
        if (position < 0) {
          // Covering short position - this generates profit/loss
          const coverQty = Math.min(qty, Math.abs(position));
          tradeProfit = (avgEntryPrice - price) * coverQty;
          profit += tradeProfit;
          completedTrades++;
          if (tradeProfit > 0) winningTrades++;
          
          console.log(`Covered short: ${coverQty} shares, profit: $${tradeProfit.toFixed(2)}`);
          
          position += qty;
          if (position > 0) {
            // Position flipped to long
            avgEntryPrice = price;
          } else if (position === 0) {
            avgEntryPrice = 0;
          }
        } else {
          // Adding to long position or opening new long
          if (position === 0) {
            avgEntryPrice = price;
          } else {
            // Average down/up
            avgEntryPrice = ((avgEntryPrice * position) + (price * qty)) / (position + qty);
          }
          position += qty;
          console.log(`Added to long position: ${qty} shares, new avg: $${avgEntryPrice.toFixed(2)}`);
        }
      } else if (trade.side === 'sell' || trade.side === 'sell_short') {
        if (position > 0) {
          // Closing long position - this generates profit/loss
          const closeQty = Math.min(qty, position);
          tradeProfit = (price - avgEntryPrice) * closeQty;
          profit += tradeProfit;
          completedTrades++;
          if (tradeProfit > 0) winningTrades++;
          
          console.log(`Closed long position: ${closeQty} shares, profit: $${tradeProfit.toFixed(2)}`);
          
          position -= qty;
          if (position < 0) {
            // Position flipped to short
            avgEntryPrice = price;
          } else if (position === 0) {
            avgEntryPrice = 0;
          }
        } else {
          // Opening short position or adding to short
          if (position === 0) {
            avgEntryPrice = price;
          } else {
            // Average down/up for short position
            avgEntryPrice = ((avgEntryPrice * Math.abs(position)) + (price * qty)) / (Math.abs(position) + qty);
          }
          position -= qty;
          console.log(`Added to short position: ${qty} shares, new avg: $${avgEntryPrice.toFixed(2)}`);
        }
      }
    }

    const winRate = completedTrades > 0 ? (winningTrades / completedTrades) * 100 : 0;
    const currentPosition = Math.abs(position);

    console.log(`Final result: completedTrades=${completedTrades}, winningTrades=${winningTrades}, totalProfit=$${profit.toFixed(2)}, winRate=${winRate.toFixed(1)}%`);

    return {
      totalTrades: trades.length,
      completedTrades,
      totalProfit: profit,
      winRate,
      currentPosition,
      entryPrice: avgEntryPrice
    };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', color: '#666' }}>Loading trading data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', color: '#ef4444' }}>{error}</div>
        <button 
          onClick={fetchTradesWithPrices}
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

  if (symbols.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', color: '#666' }}>No trading data available</div>
      </div>
    );
  }

  // Calculate performance based on selected symbol and date
  const currentSymbolData = selectedSymbol !== 'all' ? tradesData[selectedSymbol] : null;
  const chartTradeData = selectedSymbol !== 'all' && marketData[selectedSymbol] ? marketData[selectedSymbol].trades : null;
  
  // Debug logging
  console.log('Performance calculation debug:', {
    selectedSymbol,
    selectedDate,
    hasCurrentSymbolData: !!currentSymbolData,
    hasChartTradeData: !!chartTradeData,
    chartTradeDataLength: chartTradeData ? chartTradeData.length : 0,
    marketDataKeys: Object.keys(marketData),
    marketDataForSymbol: marketData[selectedSymbol]
  });
  
  // Use chart trade data if available (from orders table), otherwise fall back to old data
  const tradeDataForCalculation = chartTradeData || (currentSymbolData ? currentSymbolData.trades : null);
  const performance = tradeDataForCalculation 
    ? calculateTradePerformance(filterTradesByDate(tradeDataForCalculation, selectedDate))
    : null;
  
  // For "All Symbols" view, calculate aggregate performance
  const allSymbolsPerformance = selectedSymbol === 'all' ? (() => {
    let totalTrades = 0;
    let totalCompletedTrades = 0;
    let totalProfit = 0;
    let totalWinningTrades = 0;
    let currentPosition = 0;
    let entryPrice = 0;
    
    symbols.forEach(symbol => {
      const symbolData = tradesData[symbol];
      if (symbolData) {
        const symbolPerformance = calculateTradePerformance(
          filterTradesByDate(symbolData.trades, selectedDate)
        );
        totalTrades += symbolPerformance.totalTrades;
        totalCompletedTrades += symbolPerformance.completedTrades;
        totalProfit += symbolPerformance.totalProfit;
        totalWinningTrades += Math.round((symbolPerformance.winRate / 100) * symbolPerformance.completedTrades);
        currentPosition += symbolPerformance.currentPosition;
        if (symbolPerformance.currentPosition > 0) {
          entryPrice = symbolPerformance.entryPrice; // Use the last symbol's entry price
        }
      }
    });
    
    const winRate = totalCompletedTrades > 0 ? (totalWinningTrades / totalCompletedTrades) * 100 : 0;
    
    return {
      totalTrades,
      completedTrades: totalCompletedTrades,
      totalProfit,
      winRate,
      currentPosition,
      entryPrice
    };
  })() : null;

  return (
    <div>
      {/* Symbol Selection */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label style={{ fontWeight: 'bold' }}>Select Symbol:</label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                style={{
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '0.9rem',
                  minWidth: '150px'
                }}
              >
                <option value="all">All Symbols</option>
                {symbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label style={{ fontWeight: 'bold' }}>Select Date:</label>
                     <input
                       type="date"
                       value={selectedDate}
                       onChange={(e) => setSelectedDate(e.target.value)}
                       min="2025-10-06"
                       max="2025-10-14"
                       style={{
                         padding: '0.5rem',
                         border: '1px solid #ccc',
                         borderRadius: '4px',
                         fontSize: '0.9rem',
                         minWidth: '150px'
                       }}
                     />
                     <span style={{ fontSize: '0.8rem', color: '#666' }}>
                       (Market data: Oct 6-10, 13-14, 2025 + auto-download for latest date | All historical trades will be displayed)
                     </span>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={refreshData}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
              disabled={refreshing || loading}
            >
              {refreshing ? 'Refreshing...' : '🔄 Refresh Data'}
            </button>
            
            <button
              onClick={downloadAllMarketData}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
              disabled={loading}
            >
              {loading ? 'Downloading...' : 'Download Market Data'}
            </button>
            
            <button
              onClick={downloadAllHistoricalTrades}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
              disabled={loading}
            >
              {loading ? 'Downloading...' : 'Download All Historical Trades'}
            </button>
          </div>
          
          {/* Date filter will be added later */}
          {/* <label style={{ fontWeight: 'bold', marginLeft: '1rem' }}>Select Date:</label>
          <select
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{
              padding: '0.5rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '0.9rem',
              minWidth: '150px'
            }}
          >
            <option value="all">All Dates</option>
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select> */}
        </div>

        {/* Performance Summary */}
        {(performance || allSymbolsPerformance) && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>Total Trades</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                {(performance || allSymbolsPerformance).totalTrades}
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>Completed</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                {(performance || allSymbolsPerformance).completedTrades}
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>Total Profit</div>
              <div style={{ 
                fontSize: '1.2rem', 
                fontWeight: 'bold',
                color: (performance || allSymbolsPerformance).totalProfit >= 0 ? '#10b981' : '#ef4444'
              }}>
                {formatCurrency((performance || allSymbolsPerformance).totalProfit)}
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>Win Rate</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                {(performance || allSymbolsPerformance).winRate.toFixed(1)}%
              </div>
            </div>
            {(performance || allSymbolsPerformance).currentPosition > 0 && (
              <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>Open Position</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                  {(performance || allSymbolsPerformance).currentPosition}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>
                  @ {formatCurrency((performance || allSymbolsPerformance).entryPrice)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* TradingView Chart */}
      {selectedSymbol !== 'all' && (
        <div className="card">
          <h3>TradingView Chart - {selectedSymbol}</h3>
          <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: '#666' }}>
            Professional TradingView chart with real market data and your trading markers
            <br />
            <strong>Date (UTC):</strong> {new Date(`${selectedDate}T00:00:00Z`).toLocaleDateString('en-US', { 
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              timeZone: 'UTC'
            })}
          </div>
          
                 {/* Show message if no data available */}
                 {marketData[selectedSymbol] && marketData[selectedSymbol].noData && (
                   <div style={{ 
                     padding: '2rem', 
                     textAlign: 'center', 
                     color: '#666',
                     backgroundColor: '#f8f9fa',
                     borderRadius: '8px',
                     marginBottom: '1rem'
                   }}>
                     <h4>No Market Data Available</h4>
                     <p>No market data found for <strong>{selectedSymbol}</strong> on <strong>{new Date(`${selectedDate}T00:00:00Z`).toLocaleDateString('en-US', { timeZone: 'UTC' })}</strong></p>
                     <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                       Available dates: <strong>October 6, 7, 8, 9, 10, 13, and 14, 2025</strong>
                     </p>
                   </div>
                 )}
                 
          
          {/* Show chart if market data is available */}
          {(currentSymbolData || (marketData[selectedSymbol] && !marketData[selectedSymbol].noData && marketData[selectedSymbol].market_data)) && (
            <div>
              <SimpleTradingViewChart 
                key={`${selectedSymbol}-${selectedDate}-${marketData[selectedSymbol]?.market_data?.length || 0}`}
                symbol={selectedSymbol}
                priceData={marketData[selectedSymbol]?.market_data || currentSymbolData?.price_data || []}
                trades={marketData[selectedSymbol]?.trades || currentSymbolData?.trades || []}
                height={600}
              />
            </div>
          )}
        </div>
      )}

      {/* All Symbols Overview */}
      {selectedSymbol === 'all' && (
        <div className="card">
          <h3>All Symbols Overview</h3>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {symbols.map(symbol => {
              const symbolData = tradesData[symbol];
              const symbolPerformance = calculateTradePerformance(
                filterTradesByDate(symbolData.trades, selectedDate)
              );
              
              return (
                <div key={symbol} style={{
                  padding: '1rem',
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px',
                  backgroundColor: '#fafafa'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <h4 style={{ margin: 0, color: '#333' }}>{symbol}</h4>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ 
                        fontSize: '1.1rem', 
                        fontWeight: 'bold',
                        color: symbolPerformance.totalProfit >= 0 ? '#10b981' : '#ef4444'
                      }}>
                        {formatCurrency(symbolPerformance.totalProfit)}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>
                        {symbolPerformance.completedTrades} completed trades
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.5rem' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>Total Trades</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold' }}>{symbolPerformance.totalTrades}</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>Win Rate</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold' }}>{symbolPerformance.winRate.toFixed(1)}%</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>Current Position</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold' }}>
                        {symbolPerformance.currentPosition > 0 ? symbolPerformance.currentPosition : 'None'}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceChart;
