# Air Quality Dashboard

This React dashboard visualizes air quality data from the PurpleAir sensor connected via Arduino.

## Features

- **Heat Map**: Visualize AQI patterns by hour across days
- **Hourly Analysis**: Identify which hours typically have highest AQI
- **Timeline View**: Explore historical data with zoom and pan
- **Correlation Analysis**: Compare indoor vs outdoor air quality
- **Annual Heatmap**: GitHub-style calendar view of year-round air quality patterns
- **Timezone Support**: Configure source and display timezones
- **Auto-refresh**: Data updates every 5 minutes from Google Sheets

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Update the Google Sheets CSV URL in `src/App.js`

3. Run locally:
   ```bash
   npm start
   ```

## Deployment to GitHub Pages

### Initial Setup

1. **Install gh-pages package**:
   ```bash
   npm install --save-dev gh-pages
   ```

2. **Update package.json** (already configured in this project):
   ```json
   {
     "homepage": "https://yourusername.github.io/yourrepository",
     "scripts": {
       "predeploy": "npm run build",
       "deploy": "gh-pages -d build"
     }
   }
   ```

3. **Deploy to GitHub Pages**:
   ```bash
   npm run deploy
   ```

### Configure GitHub Repository

1. Go to your GitHub repository settings
2. Navigate to **Pages** in the left sidebar
3. Set source to **Deploy from a branch**
4. Select **gh-pages** branch
5. Select **/ (root)** folder
6. Click **Save**

### Live Site

Your dashboard will be available at: `https://yourusername.github.io/yourrepository`

Wait 2-10 minutes after first deployment for the site to become available.

### Future Updates

To update your live site, simply run:
```bash
npm run deploy
```

This will automatically build and deploy the latest changes.

## Data Source

Data is fetched from a Google Sheets CSV file that's updated in real-time by the Arduino logger.

## Technologies

- React
- Plotly.js for interactive charts
- PapaParse for CSV parsing
- GitHub Pages for hosting 