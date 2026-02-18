import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount, options = {}) {
  const { currency = 'USD', minimumFractionDigits = 0, maximumFractionDigits = 0 } = options;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(amount);
}

export function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(num >= 10000 ? 0 : 1) + 'K';
  }
  return num.toLocaleString();
}

export function formatDate(dateString, options = {}) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    ...options,
  });
}

export function formatDateTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function formatRelativeTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
}

export function getInitials(firstName, lastName) {
  const first = firstName?.charAt(0)?.toUpperCase() || '';
  const last = lastName?.charAt(0)?.toUpperCase() || '';
  return `${first}${last}`;
}

export function getStatusColor(status) {
  const colors = {
    member: 'bg-blue-50 text-blue-700',
    visitor: 'bg-amber-50 text-amber-700',
    regular: 'bg-emerald-50 text-emerald-700',
    inactive: 'bg-slate-100 text-slate-500',
    deceased: 'bg-slate-100 text-slate-400',
  };
  return colors[status] || colors.inactive;
}

export function getPaymentMethodIcon(method) {
  const icons = {
    card: 'CreditCard',
    check: 'FileText',
    cash: 'Banknote',
    ach: 'Building2',
    apple_pay: 'Apple',
    google_pay: 'Chrome',
    paypal: 'Wallet',
    venmo: 'Smartphone',
    zelle: 'Send',
    crypto: 'Bitcoin',
    stock: 'TrendingUp',
    real_estate: 'Home',
    vehicle: 'Car',
    online: 'Globe',
  };
  return icons[method] || 'DollarSign';
}

export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export function generateId() {
  return Math.random().toString(36).substring(2, 15);
}

export const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;
