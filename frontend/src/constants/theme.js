/**
 * Solomon AI - Design Token System
 * Centralized theme for Figma handoff readiness.
 * Update this ONE file when designer delivers new Figma.
 */

export const theme = {
  colors: {
    primary:      '#4f6ef7',
    primaryDark:  '#3b5bdb',
    primaryLight: '#748ffc',
    background:   '#f8fafc',
    surface:      '#ffffff',
    darkNavy:     '#0f172a',
    navy:         '#1e293b',
    slate:        '#475569',
    gray:         '#64748b',
    lightGray:    '#94a3b8',
    border:       '#e2e8f0',
    borderLight:  '#f1f5f9',
    green:        '#22c55e',
    greenLight:   '#dcfce7',
    orange:       '#f97316',
    orangeLight:  '#fff7ed',
    red:          '#ef4444',
    redLight:     '#fef2f2',
    purple:       '#8b5cf6',
    purpleLight:  '#f5f3ff',
    pink:         '#ec4899',
    gold:         '#f59e0b',
    goldLight:    '#fffbeb',
    teal:         '#14b8a6',
    tealLight:    '#f0fdfa',
  },
  fonts: {
    sans:   "'Inter', 'SF Pro Display', system-ui, -apple-system, sans-serif",
    mono:   "'JetBrains Mono', 'SF Mono', monospace",
  },
  fontSizes: {
    xs:     '0.75rem',
    sm:     '0.875rem',
    base:   '1rem',
    lg:     '1.125rem',
    xl:     '1.25rem',
    '2xl':  '1.5rem',
    '3xl':  '1.875rem',
    '4xl':  '2.25rem',
  },
  fontWeights: {
    normal:   400,
    medium:   500,
    semibold: 600,
    bold:     700,
  },
  radius: {
    sm:   '6px',
    md:   '10px',
    lg:   '14px',
    xl:   '20px',
    full: '9999px',
  },
  spacing: {
    xs:  '4px',
    sm:  '8px',
    md:  '16px',
    lg:  '24px',
    xl:  '32px',
    xxl: '48px',
  },
  shadows: {
    sm:   '0 1px 2px rgba(0,0,0,0.05)',
    md:   '0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)',
    lg:   '0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04)',
    xl:   '0 20px 25px -5px rgba(0,0,0,0.08), 0 8px 10px -6px rgba(0,0,0,0.03)',
  },
  breakpoints: {
    sm:  '640px',
    md:  '768px',
    lg:  '1024px',
    xl:  '1280px',
  },
};

// CSS variable injector — call once at app mount
export function injectThemeVariables() {
  const root = document.documentElement;
  Object.entries(theme.colors).forEach(([key, value]) => {
    root.style.setProperty(`--color-${key}`, value);
  });
  Object.entries(theme.radius).forEach(([key, value]) => {
    root.style.setProperty(`--radius-${key}`, value);
  });
  Object.entries(theme.spacing).forEach(([key, value]) => {
    root.style.setProperty(`--spacing-${key}`, value);
  });
  Object.entries(theme.shadows).forEach(([key, value]) => {
    root.style.setProperty(`--shadow-${key}`, value);
  });
  root.style.setProperty('--font-sans', theme.fonts.sans);
  root.style.setProperty('--font-mono', theme.fonts.mono);
}
