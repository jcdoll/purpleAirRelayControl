% Simple model to estimate your home leak rate based on indoor/outdoor AQI
% Based on smoke mass balance at steady-state
%
% Model = steady-state mass balance
% Removal rate = filterFlowRate * filterEfficiency * pmInterior
% Influx rate = (pmExterior - pmInterior) * leakageRate
% pmInterior / pmExterior = 1 / (filterFlowRate * filterEfficiency / leakRate + 1);
%
% Note that the model is for PM2.5, not AQI
% AQI is a nonlinear function of PM2.5
% The nonlinearity is most signicant in the 20-60 range
% This is why the outdoor/indoor values might jump from 150/15 to 200/35
%
% If you have indoor/outdoor AQI data you can enter them into aqiData and
% adjust the model parameters until it is a decent fit

close all
clear
clc

% Plot settings
set(0, 'DefaultLineLineWidth', 1.5);
set(0, 'DefaultAxesLineWidth', 1.5);
set(0, 'DefaultLineMarkerSize', 8);

% Settings
filterEfficiency = 0.9; % -
filterFlowRate = 1800; % cfm
leakRate = 100; % cfm
nPoints = 801; % -
pmExteriorMax = 1000; % ug/m^3

% EPA conversion from PM2.5 to AQI
pmLookup = [0 12 35.4 55.4 150.4 250.4 350.4 500.4]; % ug/m^3
aqiLookup = [0 50 100 150 200 300 400 500]; % -
aqiCalc = @(x) interp1(pmLookup, aqiLookup, x, 'linear');

% Measured data for fitting
aqiData = [421 79; 380 68; 250 45; 207 40; 200 30; 178 20; 124 6; 99 4; 50 3];

pmExterior = linspace(0, pmExteriorMax, nPoints);
pmInterior = pmExterior / (filterFlowRate * filterEfficiency / leakRate + 1);
aqiInterior = aqiCalc(pmInterior);
aqiExterior = aqiCalc(pmExterior);

% Plot results
figure('position', [150 450 3*400 300]);
subplot(1,3,1);
plot(pmExterior, pmInterior);
xlabel('Exterior PM2.5');
ylabel('Interior PM2.5');

subplot(1,3,2);
hold all;
plot(aqiExterior, aqiInterior);
plot(aqiData(:,1), aqiData(:,2), 'o', 'MarkerFaceColor', 'w');
xlabel('Exterior AQI');
ylabel('Interior AQI');
legend('Model', 'Data');
box on;

subplot(1,3,3);
hold all;
plot(aqiExterior, (1 - aqiInterior ./ aqiExterior) * 1e2);
xlabel('Exterior AQI');
ylabel('Apparent reduction (%)');
box on;
