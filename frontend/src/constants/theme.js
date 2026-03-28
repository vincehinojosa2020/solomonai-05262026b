/**
 * Solomon AI — Go-To-Market Design Token System
 * Single source of truth for all design decisions.
 * Aligned with CSS custom properties in index.css
 */

export const theme = {
  colors: {
    // Primary brand blue
    primary50:  '#EFF6FF',
    primary100: '#DBEAFE',
    primary200: '#BFDBFE',
    primary300: '#93C5FD',
    primary400: '#60A5FA',
    primary500: '#3B82F6',
    primary600: '#2563EB',
    primary700: '#1D4ED8',
    primary800: '#1E40AF',
    primary900: '#1E3A8A',

    // Semantic
    success:      '#10B981',
    successLight: '#D1FAE5',
    warning:      '#F59E0B',
    warningLight: '#FEF3C7',
    danger:       '#EF4444',
    dangerLight:  '#FEE2E2',
    info:         '#3B82F6',
    infoLight:    '#DBEAFE',

    // Neutrals
    gray50:  '#F9FAFB',
    gray100: '#F3F4F6',
    gray200: '#E5E7EB',
    gray300: '#D1D5DB',
    gray400: '#9CA3AF',
    gray500: '#6B7280',
    gray600: '#4B5563',
    gray700: '#374151',
    gray800: '#1F2937',
    gray900: '#111827',

    // Legacy aliases
    primary:      '#2563EB',
    primaryDark:  '#1D4ED8',
    primaryLight: '#60A5FA',
    background:   '#F9FAFB',
    surface:      '#FFFFFF',
    darkNavy:     '#0f172a',
    navy:         '#1e293b',
    slate:        '#4B5563',
    gray:         '#6B7280',
    lightGray:    '#9CA3AF',
    border:       '#E5E7EB',
    borderLight:  '#F3F4F6',
    green:        '#10B981',
    greenLight:   '#D1FAE5',
    orange:       '#F59E0B',
    orangeLight:  '#FEF3C7',
    red:          '#EF4444',
    redLight:     '#FEE2E2',
    purple:       '#8B5CF6',
    purpleLight:  '#F5F3FF',
    pink:         '#EC4899',
    gold:         '#F59E0B',
    goldLight:    '#FFFBEB',
    teal:         '#14B8A6',
    tealLight:    '#F0FDFA',
  },
  fonts: {
    sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
    mono: "'JetBrains Mono', 'SF Mono', ui-monospace, monospace",
  },
  fontSizes: {
    xs:   '0.75rem',
    sm:   '0.875rem',
    base: '1rem',
    lg:   '1.125rem',
    xl:   '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  fontWeights: {
    normal:   400,
    medium:   500,
    semibold: 600,
    bold:     700,
  },
  radius: {
    sm:   '4px',
    md:   '8px',
    lg:   '12px',
    xl:   '16px',
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
    sm:  '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md:  '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
    lg:  '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
    xl:  '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
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
