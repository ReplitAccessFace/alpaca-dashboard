import React, { useEffect, useRef, useState } from 'react';

const SimpleTradingViewChart = ({ symbol, priceData = [], trades = [], height = 500 }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  console.log(`SimpleTradingViewChart rendered for ${symbol} with ${priceData?.length || 0} data points`);

  useEffect(() => {
    if (!symbol || !chartContainerRef.current) return;

    // Clean up any existing chart
    if (chartRef.current) {
      try {
        chartRef.current.remove();
        chartRef.current = null;
      } catch (error) {
        console.warn('Error removing existing chart:', error);
      }
    }

    setIsLoading(true);
    setError(null);

    // Load TradingView Lightweight Charts from CDN
    const loadChart = async () => {
      try {
        console.log('Creating simple chart for symbol:', symbol);
        console.log('Price data available:', priceData?.length);
        console.log('Price data sample:', priceData?.[0]);
        console.log('Trades available:', trades?.length);
        console.log('Trades sample:', trades?.[0]);
        
        // Check if chart already exists for this symbol
        if (chartRef.current) {
          console.log('Chart already exists, skipping creation');
          setIsLoading(false);
          return;
        }

        // Check if LightweightCharts is already loaded
        if (window.LightweightCharts) {
          createChart();
        } else {
          // Load the script
          const script = document.createElement('script');
          script.src = 'https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js';
          script.onload = () => {
            try {
              createChart();
            } catch (error) {
              console.error('Error creating chart after script load:', error);
              setError('Failed to create chart');
              setIsLoading(false);
            }
          };
          script.onerror = () => {
            setError('Failed to load TradingView library');
            setIsLoading(false);
          };
          document.head.appendChild(script);
        }
      } catch (err) {
        console.error('Chart creation error:', err);
        setError('Failed to create chart');
        setIsLoading(false);
      }
    };

    const createChart = () => {
      try {
        if (!window.LightweightCharts) {
          throw new Error('LightweightCharts library not loaded');
        }
        
        if (!chartContainerRef.current) {
          throw new Error('Chart container not available');
        }
        
        // Create the chart
        const chart = window.LightweightCharts.createChart(chartContainerRef.current, {
          layout: {
            background: { type: window.LightweightCharts.ColorType.Solid, color: 'white' },
            textColor: 'black',
          },
          width: chartContainerRef.current.clientWidth,
          height: height,
          grid: {
            vertLines: { color: '#f0f0f0' },
            horzLines: { color: '#f0f0f0' },
          },
          crosshair: {
            mode: 1,
          },
          rightPriceScale: {
            borderColor: '#cccccc',
          },
          timeScale: {
            borderColor: '#cccccc',
            timeVisible: true,
            secondsVisible: false,
            rightOffset: 5,
            barSpacing: 3,
            fixLeftEdge: false,
            lockVisibleTimeRangeOnResize: false,
            rightBarStaysOnScroll: false,
            shiftVisibleRangeOnNewBar: false,
            tickMarkFormatter: (time, tickMarkType, locale) => {
              const date = new Date(time * 1000);
              return date.toLocaleTimeString("en-US", { 
                hour: '2-digit', 
                minute: '2-digit',
                timeZone: 'UTC'
              });
            }
          },
        });

        chartRef.current = chart;
        console.log('Chart created successfully');

        // Add candlestick series if we have price data
        let mainSeries = null;
        if (priceData && priceData.length > 0) {
          console.log('Adding candlestick data:', priceData.length, 'points');
          
          // Convert price data to the correct format for TradingView
          const formattedData = priceData.map(item => {
            try {
              return {
                time: item.time, // Already in Unix timestamp format
                open: parseFloat(item.open) || 0,
                high: parseFloat(item.high) || 0,
                low: parseFloat(item.low) || 0,
                close: parseFloat(item.close) || 0
              };
            } catch (error) {
              console.warn('Error processing price data item:', item, error);
              return null;
            }
          }).filter(item => item !== null);
          
          console.log('Formatted data sample:', formattedData[0]);
          console.log('Time range (UTC):', {
            first: new Date(formattedData[0].time * 1000).toLocaleString("en-US", {timeZone: "UTC"}),
            last: new Date(formattedData[formattedData.length - 1].time * 1000).toLocaleString("en-US", {timeZone: "UTC"})
          });
          console.log('Sample time values (UTC):', formattedData.slice(0, 3).map(d => ({
            time: d.time,
            date: new Date(d.time * 1000).toLocaleString("en-US", {timeZone: "UTC"})
          })));
          
          const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
          });
          mainSeries = candlestickSeries;

                 try {
                   candlestickSeries.setData(formattedData);
                   console.log('Candlestick data set successfully');
                   
                   // Add markers immediately after setting data if trades are available
                   if (trades && trades.length > 0) {
                     console.log('Adding markers immediately after data set');
                     
                     // First, try with a simple test marker at the current time
                     const testMarker = [{
                       time: Math.floor(Date.now() / 1000),
                       position: 'belowBar',
                       color: '#ff0000',
                       shape: 'arrowUp',
                       text: 'TEST MARKER',
                       size: 3
                     }];
                     
                     try {
                       console.log('Adding test marker:', testMarker);
                       candlestickSeries.setMarkers(testMarker);
                       console.log('✅ Test marker added');
                       
                       // Now try with actual trade markers
                       const markers = trades.map((trade, index) => {
                         try {
                           const tradeTime = trade.time || new Date(trade.timestamp).getTime() / 1000;
                           const isBuy = trade.side === 'buy' || trade.side === 'buy_to_cover';
                           
                           console.log(`Trade ${index}: time=${tradeTime}, side=${trade.side}, price=${trade.price}`);
                           
                           return {
                             time: tradeTime,
                             position: isBuy ? 'belowBar' : 'aboveBar',
                             color: isBuy ? '#26a69a' : '#ef5350',
                             shape: isBuy ? 'arrowUp' : 'arrowDown',
                             text: `${isBuy ? 'BUY' : 'SELL'} ${trade.qty} @ $${trade.price}`,
                             size: 2,
                           };
                         } catch (error) {
                           console.warn('Error processing trade marker:', trade, error);
                           return null;
                         }
                       }).filter(marker => marker !== null);
                       
                       console.log('Adding trade markers:', markers);
                       candlestickSeries.setMarkers(markers);
                       console.log('✅ Trade markers added');
                       
                     } catch (error) {
                       console.error('❌ Error adding markers:', error);
                       console.error('Error details:', error.stack);
                     }
                   }
                   
                   // Fit the chart to the data range, but include trade times if available
                   if (formattedData.length > 0) {
                     let firstTime = formattedData[0].time;
                     let lastTime = formattedData[formattedData.length - 1].time;
                     
                     // If we have trades, extend the range to include them
                     if (trades && trades.length > 0) {
                       const tradeTimes = trades.map(trade => trade.time || new Date(trade.timestamp).getTime() / 1000);
                       const minTradeTime = Math.min(...tradeTimes);
                       const maxTradeTime = Math.max(...tradeTimes);
                       
                       console.log('Trade time range:', { min: minTradeTime, max: maxTradeTime });
                       console.log('Market data range:', { first: firstTime, last: lastTime });
                       
                       // Extend the range to include trades
                       firstTime = Math.min(firstTime, minTradeTime - 3600); // 1 hour before first trade
                       lastTime = Math.max(lastTime, maxTradeTime + 3600); // 1 hour after last trade
                     }
                     
                     // Set visible range to fit the data
                     chart.timeScale().setVisibleRange({
                       from: firstTime,
                       to: lastTime
                     });
                     
                    console.log('Chart fitted to data range (UTC):', {
                      from: new Date(firstTime * 1000).toLocaleString("en-US", {timeZone: "UTC"}),
                      to: new Date(lastTime * 1000).toLocaleString("en-US", {timeZone: "UTC"})
                    });
                   }
                 } catch (error) {
                   console.error('Error setting candlestick data:', error);
                   setError('Failed to set chart data');
                   setIsLoading(false);
                   return;
                 }
        } else {
          console.log('No price data available, creating demo chart');
          // Create a simple line series with mock data if no price data
          const lineSeries = chart.addLineSeries({
            color: '#2962FF',
            lineWidth: 2,
          });
          mainSeries = lineSeries;
          
          // Generate some mock data for demonstration
          const mockData = [];
          const now = Date.now() / 1000;
          for (let i = 0; i < 30; i++) {
            mockData.push({
              time: now - (30 - i) * 86400, // 30 days ago
              value: 200 + Math.sin(i * 0.1) * 20 + Math.random() * 10
            });
          }
          lineSeries.setData(mockData);
          console.log('Demo chart created with mock data');
        }

        // Add trading markers if trades are provided
        if (trades && trades.length > 0) {
          console.log('=== MARKER DEBUG START ===');
          console.log('Adding trade markers:', trades.length);
          console.log('Sample trade data:', trades[0]);
          console.log('All trades:', trades);
          
          // Check chart time range
          const timeScale = chart.timeScale();
          const visibleRange = timeScale.getVisibleRange();
          console.log('Chart visible range:', visibleRange);
          
          
          const markers = trades.map((trade, index) => {
            const tradeTime = trade.time || new Date(trade.timestamp).getTime() / 1000;
            const isBuy = trade.side === 'buy' || trade.side === 'buy_to_cover';
            
            console.log(`Trade ${index}: time=${tradeTime}, side=${trade.side}, price=${trade.price}`);
            console.log(`Trade time ${tradeTime} is within visible range:`, 
              visibleRange ? tradeTime >= visibleRange.from && tradeTime <= visibleRange.to : 'No visible range');
            
            return {
              time: tradeTime,
              position: isBuy ? 'belowBar' : 'aboveBar',
              color: isBuy ? '#26a69a' : '#ef5350',
              shape: isBuy ? 'arrowUp' : 'arrowDown',
              text: `${isBuy ? 'BUY' : 'SELL'} ${trade.qty} @ $${trade.price}`,
              size: 2, // Increased size for better visibility
            };
          });

          console.log('Generated markers:', markers);

          // Add markers to the chart with a small delay to ensure chart is ready
          setTimeout(() => {
            try {
              console.log('=== ATTEMPTING TO ADD MARKERS ===');
              const series = mainSeries;
              console.log('Series found:', !!series);
              console.log('Markers to add:', markers);
              
              if (series) {
                series.setMarkers(markers);
                console.log('✅ Trade markers added successfully');
                console.log('=== MARKER DEBUG END ===');
              } else {
                console.warn('❌ No series found to add markers to');
                console.log('No series reference available');
              }
            } catch (error) {
              console.error('❌ Error adding trade markers:', error);
              console.error('Error details:', error.stack);
            }
          }, 500);
        } else {
          console.log('No trades provided for markers');
        }

        // Handle resize
        const handleResize = () => {
          if (chartRef.current && chartContainerRef.current) {
            chartRef.current.applyOptions({
              width: chartContainerRef.current.clientWidth,
            });
          }
        };

        window.addEventListener('resize', handleResize);
        setIsLoading(false);
        console.log('Chart setup completed successfully');

        // Return cleanup function
        return () => {
          console.log('Cleaning up chart...');
          window.removeEventListener('resize', handleResize);
          if (chartRef.current) {
            try {
              chartRef.current.remove();
              chartRef.current = null;
            } catch (error) {
              console.warn('Error removing chart:', error);
            }
          }
        };
      } catch (err) {
        console.error('Chart creation error:', err);
        setError('Failed to create chart');
        setIsLoading(false);
      }
    };

    loadChart();
  }, [symbol, priceData, trades, height]);

        if (error) {
          return (
            <div style={{ 
              height: `${height}px`, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              backgroundColor: '#f8f9fa',
              borderRadius: '4px',
              border: '1px solid #e0e0e0',
              flexDirection: 'column',
              gap: '1rem'
            }}>
              <div style={{ fontSize: '2rem' }}>📈</div>
              <div style={{ color: '#666', textAlign: 'center' }}>
                <div style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>TradingView Chart</div>
                <div style={{ fontSize: '0.9rem' }}>Failed to load {symbol}</div>
                <div style={{ fontSize: '0.8rem', color: '#999', marginTop: '0.5rem' }}>
                  Error: {error}
                </div>
              </div>
            </div>
          );
        }

  return (
    <div style={{ position: 'relative' }}>
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          zIndex: 1
        }}>
          <div style={{ textAlign: 'center', color: '#666' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📈</div>
            <div>Loading TradingView chart...</div>
          </div>
        </div>
      )}
      <div 
        ref={chartContainerRef}
        style={{ 
          width: '100%', 
          height: `${height}px`,
          border: '1px solid #e0e0e0',
          borderRadius: '4px'
        }}
      />
    </div>
  );
};

export default SimpleTradingViewChart;
