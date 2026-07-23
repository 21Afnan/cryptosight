import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box, Typography } from '@mui/material';
import { darkTheme, lightTheme, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED } from './theme/theme';

import Sidebar   from './components/Layout/Sidebar';
import Topbar    from './components/Layout/Topbar';
import Dashboard from './pages/Dashboard';

// ─── Placeholder page for routes not yet built ────────────────────────────────
const ComingSoon = ({ title }) => (
  <Box
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    height="50vh"
    gap={1.5}
  >
    <Typography variant="h5" fontWeight={700} color="text.secondary">
      {title}
    </Typography>
    <Typography variant="body2" color="text.secondary">
      This page is coming soon.
    </Typography>
  </Box>
);

// ─── Layout wrapper ───────────────────────────────────────────────────────────
const Layout = ({ mode, onToggleMode, sidebarCollapsed, onToggleSidebar, children }) => {
  const sidebarW = sidebarCollapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED;

  return (
    <Box display="flex" minHeight="100vh" sx={{ background: 'background.default' }}>
      <Sidebar collapsed={sidebarCollapsed} onToggle={onToggleSidebar} />

      <Box
        flexGrow={1}
        display="flex"
        flexDirection="column"
      >
        <Topbar mode={mode} onToggleMode={onToggleMode} sidebarCollapsed={sidebarCollapsed} />

        <Box
          component="main"
          sx={{
            mt: '64px',
            p: { xs: 2, md: 3 },
            flexGrow: 1,
            minHeight: 'calc(100vh - 64px)',
            /* subtle radial glow at the top */
            backgroundImage: (t) => t.palette.custom?.surfaceGlow || 'none',
            backgroundRepeat: 'no-repeat',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

// ─── App root ─────────────────────────────────────────────────────────────────
const App = () => {
  const [mode, setMode] = useState('dark');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleMode    = () => setMode((m) => (m === 'dark' ? 'light' : 'dark'));
  const toggleSidebar = () => setSidebarCollapsed((c) => !c);

  return (
    <ThemeProvider theme={mode === 'dark' ? darkTheme : lightTheme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout
          mode={mode}
          onToggleMode={toggleMode}
          sidebarCollapsed={sidebarCollapsed}
          onToggleSidebar={toggleSidebar}
        >
          <Routes>
            <Route path="/"               element={<Dashboard />} />
            <Route path="/strategies/:id" element={<ComingSoon title="Strategy Details" />} />
            <Route path="/wallets"        element={<ComingSoon title="Wallet Management" />} />
            <Route path="/deployment"     element={<ComingSoon title="Live Deployment" />} />
            <Route path="/deployment/:id" element={<ComingSoon title="Execution Details" />} />
            <Route path="/backtests"      element={<ComingSoon title="Backtests" />} />
            <Route path="/backtests/:id"  element={<ComingSoon title="Backtest Details" />} />
            <Route path="/ml"             element={<ComingSoon title="Machine Learning" />} />
            <Route path="/ml/:id"         element={<ComingSoon title="Model Details" />} />
            <Route path="/sentiment"      element={<ComingSoon title="NLP & Sentiment" />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
