import { createTheme, alpha } from '@mui/material/styles';

// ─── Design Tokens ────────────────────────────────────────────────────────────
export const COLORS = {
  // Brand — Sage / Mint green family
  // NOTE: This is the BRAND accent. It is intentionally a muted, sophisticated
  // sage green. It must NOT be confused with PnL positive green below.
  accent: '#5E8B6E',   // sage green — sidebar, primary buttons, links
  accentLight: '#7DAD8C',   // lighter sage for hovers / highlights
  accentDark: '#4A7A5A',   // darker sage for pressed states
  accentSurface: '#EBF3ED',   // very light sage tint — hover backgrounds (light)
  accentSurfaceDark: '#1E3028', // deep sage tint for dark surfaces

  // Secondary accent palette — used ONLY for icon bubbles and decorative
  // highlights, never for financial data signals.
  secondaryA: '#F4A9A8',   // soft coral/rose
  secondaryB: '#C4B5FD',   // soft lavender
  secondaryC: '#FCD34D',   // soft amber
  secondaryD: '#93C5FD',   // soft sky blue
  secondaryE: '#6EE7B7',   // soft mint (lighter than sage)

  // Icon bubble backgrounds (light mode)
  bubbleGreen: 'rgba(94,139,110,0.12)',   // sage
  bubbleCoral: 'rgba(244,169,168,0.18)',  // coral
  bubbleLavender: 'rgba(196,181,253,0.20)',  // lavender
  bubbleAmber: 'rgba(252,211,77,0.18)',   // amber
  bubbleSky: 'rgba(147,197,253,0.18)',  // sky

  // ── PnL / Financial semantic colors ──────────────────────────────────────
  // CRITICAL: These are INTENTIONALLY more vivid/saturated than the sage brand
  // accent so traders can instantly distinguish "brand chrome" from "real gain".
  pnlGreen: '#22C55E',  // vivid positive
  pnlRed: '#EE5D5D',  // soft, eye-friendly matte crimson red

  // ── Light theme backgrounds ───────────────────────────────────────────────
  lightBg: '#F4F7F4',  // warm off-white with faint mint tint
  lightSurface: '#FFFFFF',  // card surface — pure white
  lightSurfaceAlt: '#EFF3F0',  // subtle alternate surface
  lightBorder: 'rgba(15,40,25,0.07)',  // very faint warm border (rarely used)

  // ── Dark theme backgrounds ────────────────────────────────────────────────
  // Warm charcoal — green undertone distinguishes it from cold blue-black.
  darkBg: '#181C1A',
  darkSurface: '#20261F',
  darkSurfaceAlt: '#262E25',
  darkBorder: 'rgba(255,255,255,0.05)',

  // ── Sidebar ───────────────────────────────────────────────────────────────
  sidebarLight: '#5E8B6E',  // sage green
  sidebarDark: '#2D4A38',  // deeper sage for dark mode

  // ── Text ─────────────────────────────────────────────────────────────────
  darkTextPrimary: '#E8EDE9',   // warm off-white, hint of green
  darkTextSecondary: '#8FA895',   // muted grey-green
  darkTextDisabled: '#4D6055',

  lightTextPrimary: '#1C2B1E',  // dark warm charcoal
  lightTextSecondary: '#6B7F70',  // muted grey-green

  // ── Chart helpers ─────────────────────────────────────────────────────────
  chartGridDark: 'rgba(255,255,255,0.04)',
  chartGridLight: 'rgba(15,40,25,0.05)',

  // ── Status chip semantics ─────────────────────────────────────────────────
  statusActive: '#22C55E',
  statusPaused: '#FCD34D',
  statusStopped: '#EE5D5D',
  statusConnected: '#22C55E',
  statusError: '#EE5D5D',
  statusDisabled: '#8FA895',
  statusPending: '#FCD34D',
  statusRunning: '#7DAD8C',
  statusCompleted: '#22C55E',
  statusFailed: '#EE5D5D',
  statusFilled: '#22C55E',
  statusCancelled: '#EE5D5D',
  statusLong: '#22C55E',
  statusShort: '#EE5D5D',
  statusNeutral: '#FCD34D',

  // ── Warning ───────────────────────────────────────────────────────────────
  warning: '#F59E0B',
};

// Icon bubble palette — cycles across StatCards for visual variety
export const ICON_BUBBLE_COLORS = [
  { bg: COLORS.bubbleGreen, icon: COLORS.accent },
  { bg: COLORS.bubbleCoral, icon: '#D97070' },
  { bg: COLORS.bubbleLavender, icon: '#8B5CF6' },
  { bg: COLORS.bubbleAmber, icon: '#D97706' },
  { bg: COLORS.bubbleSky, icon: '#3B82F6' },
  { bg: 'rgba(110,231,183,0.18)', icon: '#059669' },
  { bg: COLORS.bubbleCoral, icon: '#D97070' },
  { bg: COLORS.bubbleLavender, icon: '#8B5CF6' },
  { bg: COLORS.bubbleAmber, icon: '#D97706' },
  { bg: COLORS.bubbleSky, icon: '#3B82F6' },
];

export const GRADIENTS = {
  // Hero banner gradient — sage → mint → soft teal
  hero: 'linear-gradient(135deg, #4A7A5A 0%, #5E8B6E 35%, #7DAD8C 65%, #9ECFB0 100%)',
  heroDark: 'linear-gradient(135deg, #2D4A38 0%, #3A6048 35%, #4A7A5A 65%, #5E8B6E 100%)',

  // Subtle accent tint for cards/panels
  accentSubtle: 'linear-gradient(135deg, rgba(94,139,110,0.08) 0%, rgba(94,139,110,0.02) 100%)',
  greenSubtle: 'linear-gradient(135deg, rgba(34,197,94,0.08) 0%, rgba(34,197,94,0.02) 100%)',
  redSubtle: 'linear-gradient(135deg, rgba(244,63,94,0.08) 0%, rgba(244,63,94,0.02) 100%)',
  sidebar: 'linear-gradient(180deg, #638F73 0%, #5E8B6E 100%)',
  sidebarDark: 'linear-gradient(180deg, #334F3E 0%, #2D4A38 100%)',
};

// ─── Typography ───────────────────────────────────────────────────────────────
const sharedTypography = {
  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  h1: { fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em' },
  h2: { fontSize: '1.375rem', fontWeight: 600, letterSpacing: '-0.015em' },
  h3: { fontSize: '1.125rem', fontWeight: 600, letterSpacing: '-0.01em' },
  h4: { fontSize: '0.9375rem', fontWeight: 600 },
  h5: { fontSize: '0.875rem', fontWeight: 600 },
  h6: { fontSize: '0.8125rem', fontWeight: 600 },
  body1: { fontSize: '0.875rem', lineHeight: 1.6 },
  body2: { fontSize: '0.8125rem', lineHeight: 1.5 },
  caption: {
    fontSize: '0.6875rem',
    fontWeight: 600,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
  },
};

// ─── Component overrides ──────────────────────────────────────────────────────
const buildComponents = (mode) => {
  const isDark = mode === 'dark';
  const cardShadow = isDark
    ? '0 4px 24px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)'
    : '0 4px 18px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(0, 0, 0, 0.02)';

  return {
    MuiCssBaseline: {
      styleOverrides: {
        '*': { boxSizing: 'border-box' },
        body: {
          scrollbarWidth: 'thin',
          scrollbarColor: isDark
            ? `${COLORS.darkSurfaceAlt} ${COLORS.darkBg}`
            : `${COLORS.lightSurfaceAlt} ${COLORS.lightBg}`,
        },
        '::-webkit-scrollbar': { width: '6px', height: '6px' },
        '::-webkit-scrollbar-track': { background: isDark ? COLORS.darkBg : COLORS.lightBg },
        '::-webkit-scrollbar-thumb': {
          background: isDark ? COLORS.darkSurfaceAlt : '#C8D5CA',
          borderRadius: '3px',
        },
      },
    },

    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '20px',
          border: 'none',
          backgroundImage: 'none',
          boxShadow: cardShadow,
          transition: 'transform 200ms ease, box-shadow 200ms ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: isDark
              ? '0 8px 36px rgba(0,0,0,0.5), 0 0 0 1px rgba(94,139,110,0.12)'
              : '0 10px 30px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(94,139,110,0.15)',
          },
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderRadius: '20px',
          boxShadow: cardShadow,
        },
      },
    },

    // ── Pill buttons ──────────────────────────────────────────────────────
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '999px',  // full pill
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.8125rem',
          letterSpacing: '0.01em',
          padding: '8px 20px',
          transition: 'all 200ms ease',
          boxShadow: 'none',
        },
        containedPrimary: {
          background: `linear-gradient(135deg, ${COLORS.accent} 0%, ${COLORS.accentLight} 100%)`,
          color: '#FFFFFF',
          '&:hover': {
            background: `linear-gradient(135deg, ${COLORS.accentDark} 0%, ${COLORS.accent} 100%)`,
            boxShadow: `0 4px 16px ${alpha(COLORS.accent, 0.4)}`,
          },
        },
        outlinedPrimary: {
          borderColor: COLORS.accent,
          color: COLORS.accent,
          '&:hover': {
            background: COLORS.bubbleGreen,
            borderColor: COLORS.accent,
          },
        },
        textPrimary: {
          color: COLORS.accent,
          '&:hover': { background: COLORS.bubbleGreen },
        },
      },
    },

    // ── Soft pill chips ───────────────────────────────────────────────────
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '999px',
          fontSize: '0.6875rem',
          fontWeight: 600,
          height: '24px',
          letterSpacing: '0.03em',
          border: 'none',
        },
      },
    },

    // ── Inputs — rounded ─────────────────────────────────────────────────
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
            transition: 'border-color 150ms ease',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: isDark ? 'rgba(255,255,255,0.15)' : 'rgba(94,139,110,0.4)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: COLORS.accent,
            borderWidth: '1.5px',
          },
        },
      },
    },

    MuiInputBase: {
      styleOverrides: {
        root: { fontSize: '0.875rem' },
      },
    },

    MuiSelect: {
      styleOverrides: {
        root: { borderRadius: '12px' },
      },
    },

    // ── Tables — borderless, soft separation ─────────────────────────────
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            fontSize: '0.6875rem',
            fontWeight: 700,
            letterSpacing: '0.07em',
            textTransform: 'uppercase',
            color: isDark ? COLORS.darkTextSecondary : COLORS.lightTextSecondary,
            borderBottom: `2px solid ${isDark ? 'rgba(255,255,255,0.05)' : 'rgba(15,40,25,0.06)'}`,
            padding: '12px 16px',
            whiteSpace: 'nowrap',
            background: 'transparent',
          },
        },
      },
    },

    MuiTableBody: {
      styleOverrides: {
        root: {
          '& .MuiTableRow-root': {
            transition: 'background-color 150ms ease',
            // Soft zebra stripes instead of hard cell borders
            '&:nth-of-type(even)': {
              backgroundColor: isDark
                ? 'rgba(255,255,255,0.015)'
                : 'rgba(15,40,25,0.018)',
            },
            '&:hover': {
              backgroundColor: isDark
                ? 'rgba(94,139,110,0.07)'
                : 'rgba(94,139,110,0.06)',
            },
            '& .MuiTableCell-body': {
              borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.025)' : 'rgba(15,40,25,0.04)'}`,
              fontSize: '0.8125rem',
              padding: '14px 16px',
            },
          },
        },
      },
    },

    MuiTableContainer: {
      styleOverrides: {
        root: { borderRadius: '12px', overflow: 'hidden' },
      },
    },

    // ── Tabs ─────────────────────────────────────────────────────────────
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
          minHeight: '40px',
          borderRadius: '8px',
        },
      },
    },

    MuiTabs: {
      styleOverrides: {
        indicator: { height: '3px', borderRadius: '2px', backgroundColor: COLORS.accent },
      },
    },

    // ── Tooltip ───────────────────────────────────────────────────────────
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: '0.75rem',
          borderRadius: '8px',
          padding: '6px 10px',
          background: isDark ? COLORS.darkSurfaceAlt : '#2D3B30',
        },
      },
    },

    // ── Dialog ────────────────────────────────────────────────────────────
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: '24px',
          boxShadow: cardShadow,
          border: 'none',
        },
      },
    },

    // ── Drawer (wallet detail) ────────────────────────────────────────────
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRadius: '20px 0 0 20px',
          border: 'none',
          boxShadow: isDark
            ? '-8px 0 48px rgba(0,0,0,0.5)'
            : '-8px 0 48px rgba(15,40,25,0.12)',
        },
      },
    },

    // ── AppBar / Topbar ───────────────────────────────────────────────────
    MuiAppBar: {
      styleOverrides: {
        root: { boxShadow: 'none' },
      },
    },

    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: '4px',
          '& .MuiLinearProgress-bar': { borderRadius: '4px' },
        },
      },
    },

    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: '12px' },
      },
    },

    MuiSnackbar: {
      styleOverrides: {
        root: { '& .MuiPaper-root': { borderRadius: '12px' } },
      },
    },
  };
};

// ─── Light Theme ──────────────────────────────────────────────────────────────
export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    background: {
      default: COLORS.lightBg,
      paper: COLORS.lightSurface,
    },
    primary: {
      main: COLORS.accent,
      light: COLORS.accentLight,
      dark: COLORS.accentDark,
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: COLORS.secondaryA,
    },
    success: { main: COLORS.pnlGreen },
    error: { main: COLORS.pnlRed },
    warning: { main: COLORS.warning },
    text: {
      primary: COLORS.lightTextPrimary,
      secondary: COLORS.lightTextSecondary,
      disabled: '#A8BAAd',
    },
    divider: COLORS.lightBorder,
  },
  typography: sharedTypography,
  components: buildComponents('light'),
  shape: { borderRadius: 20 },
});

// ─── Dark Theme ───────────────────────────────────────────────────────────────
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: COLORS.darkBg,
      paper: COLORS.darkSurface,
    },
    primary: {
      main: COLORS.accentLight,   // lighter sage for better contrast on dark
      light: COLORS.accent,
      dark: COLORS.accentDark,
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: COLORS.secondaryA,
    },
    success: { main: COLORS.pnlGreen },
    error: { main: COLORS.pnlRed },
    warning: { main: COLORS.warning },
    text: {
      primary: COLORS.darkTextPrimary,
      secondary: COLORS.darkTextSecondary,
      disabled: COLORS.darkTextDisabled,
    },
    divider: COLORS.darkBorder,
  },
  typography: sharedTypography,
  components: buildComponents('dark'),
  shape: { borderRadius: 20 },
});
