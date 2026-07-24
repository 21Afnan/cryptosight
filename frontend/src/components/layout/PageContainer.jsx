import React from 'react';
import Box from '@mui/material/Box';
import Topbar from './Topbar';
import { useSidebar } from '../../context/SidebarContext';

/**
 * PageContainer — wraps every page with consistent layout:
 * - Dynamic margin-left offset for fixed sidebar (240px vs 76px when collapsed)
 * - Fixed topbar offset
 * - Smooth transition when expanding/collapsing sidebar
 */
export default function PageContainer({ title, breadcrumbs, children, maxWidth = '1600px' }) {
  const { sidebarWidth } = useSidebar();

  return (
    <Box
      sx={{
        ml: `${sidebarWidth}px`,
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        transition: 'margin-left 220ms cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      <Topbar title={title} breadcrumbs={breadcrumbs} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          pt: '84px',
          px: 3,
          pb: 4,
          maxWidth,
          width: '100%',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
