import { createTheme, alpha } from '@mui/material/styles';

// ─── Premium Color Palette ────────────────────────────────────────────────────
const ACCENT_PURPLE  = '#7C3AED';
const ACCENT_VIOLET  = '#A78BFA';
const ACCENT_INDIGO  = '#6366F1';
const ACCENT_CYAN    = '#22D3EE';
const ACCENT_GREEN   = '#34D399';
const ACCENT_PINK    = '#F472B6';
const ACCENT_AMBER   = '#FBBF24';
const ACCENT_RED     = '#FB7185';
const ACCENT_BLUE    = '#60A5FA';

// ─── Shadow Presets ───────────────────────────────────────────────────────────
const GLOW_PURPLE = `0 0 20px ${alpha(ACCENT_PURPLE, 0.15)}, 0 8px 32px ${alpha(ACCENT_PURPLE, 0.1)}`;
const GLOW_PURPLE_HOVER = `0 0 30px ${alpha(ACCENT_PURPLE, 0.25)}, 0 12px 40px ${alpha(ACCENT_PURPLE, 0.15)}`;
const CARD_SHADOW_DARK = `0 4px 24px rgba(0,0,0,0.35), 0 0 0 1px ${alpha(ACCENT_PURPLE, 0.08)}`;
const CARD_SHADOW_LIGHT = `0 4px 24px rgba(124,58,237,0.08), 0 1px 4px rgba(0,0,0,0.05)`;

// Sidebar collapsed/expanded widths — exported for layout use
export const SIDEBAR_WIDTH_EXPANDED  = 260;
export const SIDEBAR_WIDTH_COLLAPSED = 72;

// ─── Shared component overrides ───────────────────────────────────────────────
const sharedComponents = {
  MuiTableHead: {
    styleOverrides: {
      root: {
        '& .MuiTableCell-root': {
          fontWeight: 700,
          fontSize: '0.7rem',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: { fontWeight: 700, fontSize: '0.72rem', borderRadius: 8 },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontWeight: 600,
        borderRadius: 12,
        padding: '8px 20px',
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: { borderRadius: 8, fontSize: '0.75rem', fontWeight: 500 },
    },
  },
};

// ─── Dark Theme ───────────────────────────────────────────────────────────────
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary:   { main: ACCENT_PURPLE, light: ACCENT_VIOLET },
    secondary: { main: ACCENT_CYAN },
    success:   { main: ACCENT_GREEN },
    warning:   { main: ACCENT_AMBER },
    error:     { main: ACCENT_RED },
    info:      { main: ACCENT_BLUE },
    background: {
      default: '#06070E',
      paper:   '#0C0D1A',
    },
    text: {
      primary:   '#EEF2FF',
      secondary: '#7C8DB5',
    },
    divider: alpha(ACCENT_PURPLE, 0.08),
    custom: {
      sidebarBg:   'rgba(8,9,18,0.96)',
      cardBg:      'rgba(14,15,30,0.75)',
      cardBorder:  alpha(ACCENT_PURPLE, 0.12),
      glowPurple:  GLOW_PURPLE,
      glowHover:   GLOW_PURPLE_HOVER,
      cardShadow:  CARD_SHADOW_DARK,
      surfaceGlow: `radial-gradient(ellipse at top, ${alpha(ACCENT_PURPLE, 0.08)} 0%, transparent 60%)`,
    },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    h4: { fontWeight: 800, letterSpacing: '-0.02em' },
    h5: { fontWeight: 700, letterSpacing: '-0.01em' },
    h6: { fontWeight: 700 },
    subtitle1: { fontWeight: 500 },
    subtitle2: { fontWeight: 600, letterSpacing: '0.01em' },
    caption: { fontWeight: 500, letterSpacing: '0.02em' },
  },
  shape: { borderRadius: 16 },
  components: {
    ...sharedComponents,
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          background: 'rgba(14,15,30,0.65)',
          border: `1px solid ${alpha(ACCENT_PURPLE, 0.1)}`,
          backdropFilter: 'blur(24px)',
          boxShadow: CARD_SHADOW_DARK,
          transition: 'transform 0.25s cubic-bezier(.4,0,.2,1), box-shadow 0.25s cubic-bezier(.4,0,.2,1)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${alpha(ACCENT_PURPLE, 0.06)}`,
          fontSize: '0.85rem',
        },
        head: {
          color: '#7C8DB5',
          background: alpha(ACCENT_PURPLE, 0.05),
          borderBottom: `1px solid ${alpha(ACCENT_PURPLE, 0.1)}`,
        },
      },
    },
  },
});

// ─── Light Theme ──────────────────────────────────────────────────────────────
export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary:   { main: '#6D28D9', light: ACCENT_VIOLET },
    secondary: { main: '#0891B2' },
    success:   { main: '#059669' },
    warning:   { main: '#D97706' },
    error:     { main: '#E11D48' },
    info:      { main: '#2563EB' },
    background: {
      default: '#F5F3FF',
      paper:   '#FFFFFF',
    },
    text: {
      primary:   '#1E1B4B',
      secondary: '#6B7280',
    },
    divider: 'rgba(109,40,217,0.08)',
    custom: {
      sidebarBg:   'rgba(255,255,255,0.95)',
      cardBg:      '#FFFFFF',
      cardBorder:  'rgba(109,40,217,0.1)',
      glowPurple:  'none',
      glowHover:   CARD_SHADOW_LIGHT,
      cardShadow:  CARD_SHADOW_LIGHT,
      surfaceGlow: `radial-gradient(ellipse at top, ${alpha('#6D28D9', 0.04)} 0%, transparent 60%)`,
    },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    h4: { fontWeight: 800, letterSpacing: '-0.02em' },
    h5: { fontWeight: 700, letterSpacing: '-0.01em' },
    h6: { fontWeight: 700 },
    subtitle1: { fontWeight: 500 },
    subtitle2: { fontWeight: 600, letterSpacing: '0.01em' },
    caption: { fontWeight: 500, letterSpacing: '0.02em' },
  },
  shape: { borderRadius: 16 },
  components: {
    ...sharedComponents,
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          background: '#FFFFFF',
          border: '1px solid rgba(109,40,217,0.08)',
          boxShadow: CARD_SHADOW_LIGHT,
          transition: 'transform 0.25s cubic-bezier(.4,0,.2,1), box-shadow 0.25s cubic-bezier(.4,0,.2,1)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(0,0,0,0.05)',
          fontSize: '0.85rem',
        },
        head: {
          color: '#6B7280',
          background: 'rgba(109,40,217,0.03)',
          borderBottom: '1px solid rgba(0,0,0,0.08)',
        },
      },
    },
  },
});

// Export accent colors for use in components
export const COLORS = {
  purple: ACCENT_PURPLE,
  violet: ACCENT_VIOLET,
  indigo: ACCENT_INDIGO,
  cyan:   ACCENT_CYAN,
  green:  ACCENT_GREEN,
  pink:   ACCENT_PINK,
  amber:  ACCENT_AMBER,
  red:    ACCENT_RED,
  blue:   ACCENT_BLUE,
};

// Gradient presets
export const GRADIENTS = {
  purple:    `linear-gradient(135deg, ${ACCENT_PURPLE} 0%, ${ACCENT_VIOLET} 100%)`,
  cyan:      `linear-gradient(135deg, ${ACCENT_CYAN} 0%, #06B6D4 100%)`,
  green:     `linear-gradient(135deg, ${ACCENT_GREEN} 0%, #10B981 100%)`,
  pink:      `linear-gradient(135deg, ${ACCENT_PINK} 0%, #EC4899 100%)`,
  amber:     `linear-gradient(135deg, ${ACCENT_AMBER} 0%, #F59E0B 100%)`,
  indigo:    `linear-gradient(135deg, ${ACCENT_INDIGO} 0%, #818CF8 100%)`,
  blue:      `linear-gradient(135deg, ${ACCENT_BLUE} 0%, #3B82F6 100%)`,
  purpleCyan:`linear-gradient(135deg, ${ACCENT_PURPLE} 0%, ${ACCENT_CYAN} 100%)`,
  sunset:    `linear-gradient(135deg, ${ACCENT_PINK} 0%, ${ACCENT_AMBER} 100%)`,
  ocean:     `linear-gradient(135deg, #0EA5E9 0%, ${ACCENT_CYAN} 100%)`,
};
