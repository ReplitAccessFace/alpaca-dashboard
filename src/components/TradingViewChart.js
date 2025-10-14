import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

const TradingViewChart = ({ symbol, priceData = [], trades = [], height = 500 }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!symbol || !chartContainerRef.current) return;

    setIsLoading(true);
    setError(null);

    try {
      console.log('Creating chart for symbol:', symbol);
      console.log('Price data available:', priceData?.length);

      // Create the chart
      const chart = createChart(chartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'white' },
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
        },
      });

      chartRef.current = chart;
      console.log('Chart created successfully');

      // Add candlestick series if we have price data
      if (priceData && priceData.length > 0) {
        console.log('Adding candlestick data:', priceData.length, 'points');
        console.log('Sample price data:', priceData[0]);
        
        // Convert price data to the correct format for TradingView
        const formattedData = priceData.map(item => ({
          time: item.time,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close
        }));
        
        console.log('Formatted data sample:', formattedData[0]);
        
        const candlestickSeries = chart.addCandlestickSeries({
          upColor: '#26a69a',
          downColor: '#ef5350',
          borderVisible: false,
          wickUpColor: '#26a69a',
          wickDownColor: '#ef5350',
        });

        candlestickSeries.setData(formattedData);
        console.log('Candlestick data set successfully');
        
        // Add trading markers if trades are provided
        if (trades && trades.length > 0) {
          console.log('Adding trade markers:', trades.length);
          const markers = trades.map((trade, index) => {
            const tradeTime = trade.time || new Date(trade.timestamp).getTime() / 1000;
            const isBuy = trade.side === 'buy' || trade.side === 'buy_to_cover';
            
            return {
              time: tradeTime,
              position: isBuy ? 'belowBar' : 'aboveBar',
              color: isBuy ? '#26a69a' : '#ef5350',
              shape: isBuy ? 'arrowUp' : 'arrowDown',
              text: `${isBuy ? 'BUY' : 'SELL'} ${trade.qty} @ $${trade.price}`,
              size: 1,
            };
          });

          // Add markers to the chart
          try {
            candlestickSeries.setMarkers(markers);
            console.log('Trade markers added successfully');
          } catch (error) {
            console.error('Error adding trade markers:', error);
          }
        }
      } else {
        console.log('No price data available, creating demo chart');
        // Create a simple line series with mock data if no price data
        const lineSeries = chart.addLineSeries({
          color: '#2962FF',
          lineWidth: 2,
        });
        
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

      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartRef.current) {
          chartRef.current.remove();
        }
      };
    } catch (err) {
      console.error('Chart creation error:', err);
      setError('Failed to create chart');
      setIsLoading(false);
    }
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

export default TradingViewChart;
