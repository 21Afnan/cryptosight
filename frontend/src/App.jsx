import React, { createContext, useState, useMemo, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { darkTheme, lightTheme } from './theme/theme';
import Sidebar from './components/layout/Sidebar';
import ErrorBoundary from './components/ui/ErrorBoundary';
import { SidebarProvider } from './context/SidebarContext';
import { SearchProvider } from './context/SearchContext';

// Pages — all imported at top level
import Dashboard from './pages/Dashboard';
import StrategyDetails from './pages/StrategyDetails';
import Wallets from './pages/Wallets';
import Deployment from './pages/Deployment';
import ExecutionDetails from './pages/ExecutionDetails';
import BacktestRequests from './pages/BacktestRequests';
import BacktestDetails from './pages/BacktestDetails';
import StrategyBuilder from './pages/StrategyBuilder';
import MachineLearning from './pages/MachineLearning';
import ModelDetails from './pages/ModelDetails';
import Sentiment from './pages/Sentiment';

// Theme context — exposes toggleTheme() to Topbar and any other consumer
export const ThemeContext = createContext({ mode: 'dark', toggleTheme: () => {} });

const THEME_STORAGE_KEY = 'cryptosight_theme';

export default function App() {
  const [mode, setMode] = useState(() => {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY) || 'dark';
    } catch {
      return 'dark';
    }
  });

  const toggleTheme = useCallback(() => {
    setMode((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem(THEME_STORAGE_KEY, next);
      } catch {
        // localStorage unavailable — fall back to in-memory only
      }
      return next;
    });
  }, []);

  const theme = useMemo(() => (mode === 'dark' ? darkTheme : lightTheme), [mode]);
  const ctxValue = useMemo(() => ({ mode, toggleTheme }), [mode, toggleTheme]);

  return (
    <ThemeContext.Provider value={ctxValue}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ErrorBoundary>
          <SidebarProvider>
            <SearchProvider>
            <BrowserRouter>
              <Sidebar />
              <Routes>
                <Route path="/"                   element={<Dashboard />} />
                <Route path="/strategies"         element={<StrategyDetails />} />
                <Route path="/strategies/:id"     element={<StrategyDetails />} />
                <Route path="/wallets"            element={<Wallets />} />
                <Route path="/deployment"         element={<Deployment />} />
                <Route path="/deployment/:id"     element={<ExecutionDetails />} />
                <Route path="/execution"          element={<Deployment />} />
                <Route path="/execution/:id"      element={<ExecutionDetails />} />
                <Route path="/backtests"          element={<BacktestRequests />} />
                <Route path="/backtests/:id"      element={<BacktestDetails />} />
                <Route path="/strategy-builder"   element={<StrategyBuilder />} />
                <Route path="/ml"                 element={<MachineLearning />} />
                <Route path="/ml/:id"             element={<ModelDetails />} />
                <Route path="/sentiment"          element={<Sentiment />} />
              </Routes>
            </BrowserRouter>
            </SearchProvider>
          </SidebarProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </ThemeContext.Provider>
  );
}
