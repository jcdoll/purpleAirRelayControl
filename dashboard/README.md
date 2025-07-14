# Air Quality Dashboard

This React dashboard visualizes air quality data from the PurpleAir sensor connected via Arduino.

## Requirements

### Core Constraints
- **GitHub Pages hosting** - Static file deployment only (hard requirement)
- Client-side only - No server-side processing, everything runs in browser
- Google Sheets data source - CSV export from Google Sheets with 5-minute auto-refresh
- Mobile responsive - Must work effectively on mobile devices

### Technical Requirements
- Real-time updates - Auto-refresh data every 5 minutes using browser fetch()
- Multiple chart types - Support for heatmaps, timelines, correlation plots, annual calendars
- Data filtering - Date range controls, timezone handling, category filtering
- Performance - Fast loading, small bundle size, smooth interactions
- Cross-browser compatibility - Works in modern browsers (Chrome, Firefox, Safari, Edge)

### Operational Requirements  
- Zero maintenance deployment - Deploy once, runs automatically
- Timezone flexibility - Support for different source/display timezones
- Data resilience - Graceful handling of missing/malformed data
- Easy customization - Simple to modify charts, colors, and data sources


## Features

- Heat Map: Visualize AQI patterns by hour across days
- Hourly Analysis: Identify which hours typically have highest AQI
- Timeline View: Explore historical data with zoom and pan
- Correlation Analysis: Compare indoor vs outdoor air quality
- Annual Heatmap: GitHub-style calendar view of year-round air quality patterns
- Timezone Support: Configure source and display timezones


## Technologies

Technologies:
- React
- Plotly.js for interactive charts
- PapaParse for CSV parsing
- GitHub Pages for hosting 
- Microcontroller sends data to 

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Update configuration values for your project:
   - `CSV_URL` in `src/constants/app.js` - your Google Sheets CSV export URL
   - `GITHUB_URL` in `src/constants/app.js` - your GitHub repository URL  
   - `homepage` in `package.json` - your GitHub Pages URL

3. Run locally:
   ```bash
   npm start
   ```

## Testing

The project includes comprehensive tests for utility functions and chart data processors.

### Running Tests

```bash
# Run all tests (interactive watch mode)
# Cursor or other AI clients should never do this - they should use non-interactive mode below
npm test

# Run tests in non-interactive mode (useful for CI) - Windows
$env:CI="true"; npm test

# Run tests in non-interactive mode (useful for CI) - Linux/Mac
CI=true npm test

# Run tests with coverage report
npm test -- --coverage --watchAll=false

# Run specific test file
npm test aqiUtils.test.js
npm test chartDataProcessors.test.js

# Run tests in verbose mode
npm test -- --verbose --watchAll=false
```

### Test Structure

- **`src/__tests__/utils/`** - Unit tests for utility functions
  - `aqiUtils.test.js` - Tests for AQI color/category functions
  - `chartDataProcessors.test.js` - Tests for chart data processing functions

### Test Coverage

The tests cover:
- AQI color and category classification
- Chart data processing for all visualization types (heatmap, timeline, hourly, correlation, annual)
- Edge cases like empty data, null values, and invalid inputs
- Data filtering and aggregation logic

### Continuous Integration

Tests should be run as part of CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: npm test -- --coverage --watchAll=false
```

## Deployment to GitHub Pages

### Automated Deployment

This project uses GitHub Actions for automated deployment. The deployment process is completely automated:

1. **Push to master branch** triggers the deployment workflow
2. **GitHub Actions** automatically:
   - Installs dependencies (`npm ci`)
   - Builds the project (`npm run build`)
   - Deploys to GitHub Pages

### Configure GitHub Repository

1. Go to your GitHub repository settings
2. Navigate to **Pages** in the left sidebar
3. Set source to **GitHub Actions**
4. The workflow file `.github/workflows/deploy.yml` handles the rest

### Live Site

Your dashboard will be available at: `https://jcdoll.github.io/purpleAirRelayControl`

Wait 2-10 minutes after first deployment for the site to become available.

### Future Updates

To update your live site:
```bash
git add .
git commit -m "Update dashboard"
git push origin master
```

The GitHub Actions workflow will automatically build and deploy the latest changes.