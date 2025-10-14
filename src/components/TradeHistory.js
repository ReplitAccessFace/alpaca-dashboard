import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TradeHistory = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [groupedTrades, setGroupedTrades] = useState({ windows: [], stats: {} });
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const initializeData = async () => {
      // Always try to download today's data on initial load
      const today = new Date().toISOString().split('T')[0];
      console.log(`Auto-downloading latest trades on load for today: ${today}`);
      
      try {
        // Download today's trades
        const todayResponse = await axios.post(`http://localhost:8000/api/performance/trades/download-all?start_date=${today}&days_back=1`);
        console.log('Auto-download trades response:', todayResponse.data);
      } catch (error) {
        console.log('Auto-download trades failed:', error.message);
      }
      
      // Then fetch the main data
      await fetchData();
    };
    
    initializeData();
  }, [selectedDate]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
      setLoading(true);
      }
      // Use the new orders-based API endpoint
      const ordersResponse = await axios.get(`http://localhost:8000/api/orders/db?date=${selectedDate}`);
      
      // Process and group trades from orders data
      const processedTrades = processOrders(ordersResponse.data);
      setGroupedTrades(processedTrades);
      setError(null);
    } catch (err) {
      setError('Failed to fetch trade data. Make sure the backend server is running.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const formatUtcDateTime = (ts) => {
    const d = new Date(ts);
    return d.toLocaleString('en-US', {
      timeZone: 'UTC',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };


  const processOrders = (orders) => {
    console.log('Processing orders:', orders.length);
    // Group orders by symbol only (no trading hours grouping)
    const tradesBySymbol = {};
    
    // Filter to only filled orders and process them
    orders.forEach(order => {
      if ((order.status === 'filled' || order.status === 'OrderStatus.FILLED') && order.symbol && order.filled_at) {
        const symbol = order.symbol;
        
        if (!tradesBySymbol[symbol]) {
          tradesBySymbol[symbol] = {
            symbol: symbol,
            trades: [],
            totalValue: 0
          };
        }
        
        // Convert order to trade format for processing
        // Map enum side values to simple strings
        let side = order.side;
        if (side === 'OrderSide.BUY') side = 'buy';
        else if (side === 'OrderSide.SELL') side = 'sell';
        else if (side === 'OrderSide.SELL_SHORT') side = 'sell_short';
        else if (side === 'OrderSide.BUY_TO_COVER') side = 'buy_to_cover';
        
        const trade = {
          id: order.order_id,
          symbol: order.symbol,
          side: side,
          qty: order.filled_qty || order.qty,
          price: order.filled_avg_price || 0,
          transaction_time: order.filled_at,
          activity_type: 'FILL',
          order_id: order.order_id
        };
        
        tradesBySymbol[symbol].trades.push(trade);
        tradesBySymbol[symbol].totalValue += parseFloat(trade.price) * parseFloat(trade.qty);
      }
    });

    // Calculate profit/loss for each symbol
    Object.keys(tradesBySymbol).forEach(symbol => {
      const symbolData = tradesBySymbol[symbol];
      const trades = symbolData.trades.sort((a, b) => new Date(a.transaction_time) - new Date(b.transaction_time));
      
      // Process trades with running profit calculation
      
      let profit = 0;
      let openQuantity = 0;
      let closedQuantity = 0;
      
      // Calculate profit using proper position tracking with running profit
      let position = 0;
      let avgEntryPrice = 0;
      let runningProfit = 0;
      
      // Add running profit to each trade
      for (let i = 0; i < trades.length; i++) {
        const trade = trades[i];
        const qty = parseFloat(trade.qty);
        const price = parseFloat(trade.price);
        let tradeProfit = 0;
        
        if (trade.side === 'buy' || trade.side === 'buy_to_cover') {
          if (position < 0) {
            // Covering short position - this generates profit/loss
            const coverQty = Math.min(qty, Math.abs(position));
            tradeProfit = (avgEntryPrice - price) * coverQty;
            profit += tradeProfit;
            runningProfit += tradeProfit;
            closedQuantity += coverQty;
            
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
          }
        } else if (trade.side === 'sell' || trade.side === 'sell_short') {
          if (position > 0) {
            // Closing long position - this generates profit/loss
            const closeQty = Math.min(qty, position);
            tradeProfit = (price - avgEntryPrice) * closeQty;
        profit += tradeProfit;
            runningProfit += tradeProfit;
            closedQuantity += closeQty;
            
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
          }
        }
        
        // Add running profit to the trade object
        trades[i].runningProfit = runningProfit;
        trades[i].tradeProfit = tradeProfit;
      }
      
      // Calculate remaining open position
      openQuantity = Math.abs(position);
      
      symbolData.profit = profit;
      symbolData.openQuantity = openQuantity;
      symbolData.closedQuantity = closedQuantity;
      symbolData.profitPercent = symbolData.totalValue > 0 ? (profit / symbolData.totalValue) * 100 : 0;
    });

    // Convert to array and sort by symbol name
    const sortedSymbols = Object.values(tradesBySymbol).sort((a, b) => 
      a.symbol.localeCompare(b.symbol)
    );

    // Calculate overall statistics for completed round-trip trades
    let totalRoundTrips = 0;
    let profitableRoundTrips = 0;
    let totalCapitalForRoundTrips = 0;
    let weightedProfit = 0;

    sortedSymbols.forEach(symbolData => {
      const trades = symbolData.trades.sort((a, b) => new Date(a.transaction_time) - new Date(b.transaction_time));
      
      // Track position to identify round trips
      let position = 0;
      let roundTripStart = null;
      
      trades.forEach(trade => {
        const qty = parseFloat(trade.qty);
        const price = parseFloat(trade.price);
        
        if (trade.side === 'buy' || trade.side === 'buy_to_cover') {
          if (position <= 0) {
            // Starting a new round trip (opening long position or covering short)
            roundTripStart = { trade, qty: Math.abs(qty), price };
          }
          position += qty;
        } else if (trade.side === 'sell' || trade.side === 'sell_short') {
          if (position >= 0 && roundTripStart) {
            // Completing a round trip (closing long position or opening short)
            const roundTripQty = Math.min(Math.abs(qty), roundTripStart.qty);
            const roundTripProfit = (price - roundTripStart.price) * roundTripQty;
            
            totalRoundTrips++;
            totalCapitalForRoundTrips += roundTripStart.price * roundTripQty;
            
            console.log('Found round trip:', symbolData.symbol, 'Profit:', roundTripProfit);
            
            if (roundTripProfit > 0) {
              profitableRoundTrips++;
              weightedProfit += roundTripProfit;
            }
            
            // Reset for next round trip
            roundTripStart = null;
          }
          position -= qty;
        }
      });
    });

    // Add overall statistics to the result
    const stats = {
      totalTrades: totalRoundTrips,
      profitableTrades: profitableRoundTrips,
      tradeWinRate: totalRoundTrips > 0 ? (profitableRoundTrips / totalRoundTrips) * 100 : 0,
      totalCapital: totalCapitalForRoundTrips,
      weightedWinRate: totalCapitalForRoundTrips > 0 ? (weightedProfit / totalCapitalForRoundTrips) * 100 : 0
    };
    
    console.log('Round Trip Statistics:', stats);
    console.log('Total round trips:', totalRoundTrips);
    console.log('Profitable round trips:', profitableRoundTrips);
    
    return {
      windows: sortedSymbols,
      stats: stats
    };
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const refreshData = async () => {
    console.log('Refreshing trade history data...');
    
    // Always try to download today's data first
    const today = new Date().toISOString().split('T')[0];
    console.log(`Auto-downloading latest trades for today: ${today}`);
    
    try {
      // Download today's trades
      const todayResponse = await axios.post(`http://localhost:8000/api/performance/trades/download-all?start_date=${today}&days_back=1`);
      console.log('Today\'s trades download response:', todayResponse.data);
    } catch (error) {
      console.log('Today\'s trades download failed:', error.message);
    }
    
    // Then try to download any missing historical trades for the selected date (if different from today)
    if (selectedDate !== today) {
      try {
        console.log(`Attempting to download historical trades for ${selectedDate}...`);
        const response = await axios.post(`http://localhost:8000/api/performance/trades/download-all?start_date=${selectedDate}&days_back=1`);
        console.log('Selected date trades download response:', response.data);
      } catch (error) {
        console.log('No additional trades to download or download failed:', error.message);
      }
    }
    
    // Then refresh the data
    await fetchData(true);
  };

  const formatPercent = (percent) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const generateCSV = () => {
    const headers = ['Symbol', 'Time (UTC)', 'Side', 'Qty', 'Price', 'Value', 'Trade P&L', 'Running P&L'];
    const rows = [];
    
    groupedTrades.windows.forEach(window => {
      window.trades.forEach(trade => {
        rows.push([
          window.symbol,
          formatUtcDateTime(trade.transaction_time),
          trade.side.toUpperCase(),
          Math.abs(parseFloat(trade.qty)),
          parseFloat(trade.price),
          parseFloat(trade.price) * Math.abs(parseFloat(trade.qty)),
          trade.tradeProfit || 0,
          trade.runningProfit || 0
        ]);
      });
    });
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  };

  const downloadCSV = (content, filename) => {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', color: '#666' }}>Loading trade history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ color: '#ef4444', fontSize: '1.2rem' }}>{error}</div>
        <button 
          onClick={fetchData}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#3b82f6',
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

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ margin: 0, color: '#1f2937' }}>Trading Windows - Open/Close Analysis</h1>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.9rem', color: '#666' }}>
            Date:
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              style={{
                marginLeft: '0.5rem',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '0.9rem'
              }}
            />
          </label>
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
            {refreshing ? 'Refreshing...' : '🔄 Refresh'}
          </button>
          <button 
            onClick={() => {
              const csvContent = generateCSV();
              downloadCSV(csvContent, `trade-history-${selectedDate}.csv`);
            }}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            Export CSV
          </button>
        </div>
      </div>

      {groupedTrades.windows.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
          <div style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>No trades found</div>
          <div>No trading activity for {selectedDate}</div>
        </div>
      ) : (
        <>
          {groupedTrades.windows.map((window, index) => (
            <div key={index} style={{ 
              marginBottom: '2rem', 
              border: '1px solid #e5e7eb', 
              borderRadius: '8px',
              overflow: 'hidden',
              backgroundColor: 'white'
            }}>
              <div style={{ 
                backgroundColor: '#f9fafb', 
                padding: '1rem', 
                borderBottom: '1px solid #e5e7eb',
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center'
              }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#1f2937' }}>
                    {window.symbol}
                  </h3>
                  <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.25rem' }}>
                    {window.trades.length} trades • Total Value: {formatCurrency(window.totalValue)}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ 
                    fontSize: '1.2rem', 
                    fontWeight: 'bold',
                    color: window.profit >= 0 ? '#10b981' : '#ef4444'
                  }}>
                    {formatCurrency(window.profit)}
                  </div>
                  <div style={{ 
                    fontSize: '0.9rem',
                    color: window.profit >= 0 ? '#10b981' : '#ef4444'
                  }}>
                    {formatPercent(window.profitPercent)}
                  </div>
                </div>
              </div>

              <div style={{ padding: '1rem' }}>
                <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
                  <div>
                  <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.25rem' }}>Open Position</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#1f2937' }}>
                      {window.openQuantity}
                    </div>
                </div>
                  <div>
                  <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.25rem' }}>Closed</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#1f2937' }}>
                      {window.closedQuantity}
                    </div>
                </div>
                  <div>
                  <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.25rem' }}>Total Qty</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#1f2937' }}>
                      {window.trades.reduce((sum, t) => sum + Math.abs(parseFloat(t.qty)), 0)}
                    </div>
                </div>
              </div>

              <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#1f2937' }}>Trade Details</h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                <tr style={{ backgroundColor: '#f9fafb' }}>
                  <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Time (UTC)</th>
                          <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Side</th>
                          <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Qty</th>
                          <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Price</th>
                          <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Value</th>
                          <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Trade P&L</th>
                          <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Running P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {window.trades.map((trade, tradeIndex) => (
                      <tr key={tradeIndex}>
                            <td style={{ padding: '0.5rem', borderBottom: '1px solid #f3f4f6' }}>
                              {formatUtcDateTime(trade.transaction_time)}
                            </td>
                            <td style={{ padding: '0.5rem', borderBottom: '1px solid #f3f4f6' }}>
                          <span style={{ 
                                padding: '0.25rem 0.5rem',
                                borderRadius: '4px',
                                fontSize: '0.8rem',
                            fontWeight: 'bold',
                                backgroundColor: (trade.side === 'buy' || trade.side === 'buy_to_cover') ? '#dcfce7' : '#fef2f2',
                                color: (trade.side === 'buy' || trade.side === 'buy_to_cover') ? '#166534' : '#991b1b'
                          }}>
                            {trade.side.toUpperCase()}
                          </span>
                        </td>
                            <td style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                              {Math.abs(parseFloat(trade.qty))}
                            </td>
                            <td style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                              {formatCurrency(parseFloat(trade.price))}
                            </td>
                            <td style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                              {formatCurrency(parseFloat(trade.price) * Math.abs(parseFloat(trade.qty)))}
                            </td>
                            <td style={{ 
                              padding: '0.5rem', 
                              textAlign: 'right', 
                              borderBottom: '1px solid #f3f4f6',
                              color: (trade.tradeProfit || 0) >= 0 ? '#10b981' : '#ef4444',
                              fontWeight: 'bold'
                            }}>
                              {trade.tradeProfit ? formatCurrency(trade.tradeProfit) : '-'}
                            </td>
                            <td style={{ 
                              padding: '0.5rem', 
                              textAlign: 'right', 
                              borderBottom: '1px solid #f3f4f6',
                              color: (trade.runningProfit || 0) >= 0 ? '#10b981' : '#ef4444',
                              fontWeight: 'bold'
                            }}>
                              {formatCurrency(trade.runningProfit || 0)}
                            </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                  </div>
                </div>
              </div>
            </div>
          ))}

      {/* Summary Stats */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '1rem',
            marginTop: '2rem'
          }}>
            <div style={{ 
              backgroundColor: 'white', 
              padding: '1.5rem', 
              borderRadius: '8px', 
              border: '1px solid #e5e7eb',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Total Windows</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>{groupedTrades.windows.length}</div>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>Trading sessions</div>
            </div>
            <div style={{ 
              backgroundColor: 'white', 
              padding: '1.5rem', 
              borderRadius: '8px', 
              border: '1px solid #e5e7eb',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Total Profit</div>
              <div style={{ 
                fontSize: '2rem', 
                fontWeight: 'bold',
                color: groupedTrades.windows.reduce((sum, w) => sum + w.profit, 0) >= 0 ? '#10b981' : '#ef4444'
              }}>
                {formatCurrency(groupedTrades.windows.reduce((sum, w) => sum + w.profit, 0))}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>All windows</div>
            </div>
            <div style={{ 
              backgroundColor: 'white', 
              padding: '1.5rem', 
              borderRadius: '8px', 
              border: '1px solid #e5e7eb',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Profitable Windows</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
                {groupedTrades.windows.filter(w => w.profit > 0).length}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>Out of {groupedTrades.windows.length}</div>
            </div>
            <div style={{ 
              backgroundColor: 'white', 
              padding: '1.5rem', 
              borderRadius: '8px', 
              border: '1px solid #e5e7eb',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Trade Win Rate</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
                {groupedTrades.stats.profitableTrades}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>
                {groupedTrades.stats.tradeWinRate.toFixed(1)}% of {groupedTrades.stats.totalTrades} trades
              </div>
          </div>
            <div style={{ 
              backgroundColor: 'white', 
              padding: '1.5rem', 
              borderRadius: '8px', 
              border: '1px solid #e5e7eb',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Weighted Win Rate</div>
              <div style={{ 
                fontSize: '2rem', 
                fontWeight: 'bold',
                color: groupedTrades.stats.weightedWinRate >= 0 ? '#10b981' : '#ef4444'
              }}>
                {groupedTrades.stats.weightedWinRate.toFixed(2)}%
        </div>
              <div style={{ fontSize: '0.8rem', color: '#666' }}>
                Based on capital used
          </div>
        </div>
      </div>
        </>
      )}
    </div>
  );
};

export default TradeHistory;