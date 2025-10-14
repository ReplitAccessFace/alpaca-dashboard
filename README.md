# Alpaca Trading Dashboard - Local Development

A simple, localhost-first dashboard for monitoring your Alpaca trading performance. Perfect for development and testing before deploying to production.

## Features

- **Portfolio Overview**: Key metrics and current positions
- **Performance Charts**: Interactive charts showing portfolio performance
- **Trade History**: Complete trade log with filtering
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Mock Data**: Ready for Alpaca API integration

## Quick Start

### 1. Install Dependencies
```bash
cd "/Users/felixstrasser/development/Alpaca Dashboard"
npm install
```

### 2. Start Development Server
```bash
npm start
```

### 3. Open Dashboard
Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── components/
│   ├── PortfolioOverview.js    # Portfolio metrics and positions
│   ├── PerformanceChart.js      # Performance charts
│   └── TradeHistory.js         # Trade history table
├── App.js                       # Main application
├── App.css                      # Styling
└── index.js                     # Entry point
```

## Current Status

✅ **Dashboard UI Complete**
- Portfolio overview with mock data
- Interactive performance charts
- Trade history with filtering
- Responsive design

🔄 **Next Steps**
- Integrate with your existing Alpaca API code
- Replace mock data with real trading data
- Add real-time updates

## Integration with Your Alpaca Code

Your existing Alpaca code is in:
- `../alpaca_rest_api/` - Your Alpaca API integration
- `../Alpaca analysis 2/` - Your analysis scripts

To connect real data:
1. Copy your Alpaca API configuration
2. Create API endpoints to fetch portfolio data
3. Replace mock data in components with real API calls

## Development Notes

- Uses React 18 with Create React App
- Charts powered by Recharts
- Responsive CSS (no external frameworks)
- Ready for localhost development
- Easy to extend with new features

## Next Phase: Alpaca API Integration

When ready to connect real data:
1. Set up backend API (FastAPI recommended)
2. Integrate your existing Alpaca API code
3. Replace mock data with real portfolio data
4. Add real-time updates

## Deployment Options (Future)

- **Localhost**: Current setup for development
- **Subdomain**: `dashboard.bea-labs.com` (when ready)
- **Webflow Integration**: Embed in your existing site
- **Standalone**: Deploy as separate application

## Troubleshooting

If you encounter issues:
1. Make sure Node.js is installed (version 16+)
2. Clear npm cache: `npm cache clean --force`
3. Delete node_modules and reinstall: `rm -rf node_modules && npm install`
4. Check that port 3000 is available

## Ready for Development!

Your dashboard is ready to run locally. Start the development server and begin customizing for your Alpaca trading data.