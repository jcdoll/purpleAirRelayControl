import React from 'react';

const TimezoneControls = ({ 
  sourceTimezone, 
  setSourceTimezone, 
  selectedTimezone, 
  setSelectedTimezone 
}) => {
  // Common timezone options
  const timezoneOptions = [
    { value: -12, label: 'UTC-12 (Baker Island)' },
    { value: -11, label: 'UTC-11 (Samoa)' },
    { value: -10, label: 'UTC-10 (Hawaii)' },
    { value: -9, label: 'UTC-9 (Alaska)' },
    { value: -8, label: 'UTC-8 (Pacific Standard)' },
    { value: -7, label: 'UTC-7 (Mountain/Pacific Daylight)' },
    { value: -6, label: 'UTC-6 (Central)' },
    { value: -5, label: 'UTC-5 (Eastern)' },
    { value: -4, label: 'UTC-4 (Atlantic)' },
    { value: -3, label: 'UTC-3 (Argentina)' },
    { value: -2, label: 'UTC-2 (Mid-Atlantic)' },
    { value: -1, label: 'UTC-1 (Azores)' },
    { value: 0, label: 'UTC (GMT)' },
    { value: 1, label: 'UTC+1 (Central European)' },
    { value: 2, label: 'UTC+2 (Eastern European)' },
    { value: 3, label: 'UTC+3 (Moscow)' },
    { value: 4, label: 'UTC+4 (Gulf)' },
    { value: 5, label: 'UTC+5 (Pakistan)' },
    { value: 6, label: 'UTC+6 (Bangladesh)' },
    { value: 7, label: 'UTC+7 (Indochina)' },
    { value: 8, label: 'UTC+8 (China)' },
    { value: 9, label: 'UTC+9 (Japan)' },
    { value: 10, label: 'UTC+10 (Australia East)' },
    { value: 11, label: 'UTC+11 (Solomon Islands)' },
    { value: 12, label: 'UTC+12 (Fiji)' }
  ];

  return (
    <div className="timezone-controls">
      <div className="timezone-row">
        <div className="timezone-selector">
          <label>Source:</label>
          <select 
            value={sourceTimezone} 
            onChange={(e) => setSourceTimezone(Number(e.target.value))}
          >
            {timezoneOptions.map(tz => (
              <option key={tz.value} value={tz.value}>
                {tz.label}
              </option>
            ))}
          </select>
        </div>
        
        <div className="timezone-selector">
          <label>Display:</label>
          <select 
            value={selectedTimezone} 
            onChange={(e) => setSelectedTimezone(Number(e.target.value))}
          >
            {timezoneOptions.map(tz => (
              <option key={tz.value} value={tz.value}>
                {tz.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default TimezoneControls; 