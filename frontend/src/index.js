import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { injectThemeVariables } from "@/constants/theme";

// Inject design tokens as CSS variables
injectThemeVariables();

// Global fetch interceptor: strips credentials:'include' (CORS proxy breaks it)
// and auto-injects Bearer token for API calls
const _fetch = window.fetch.bind(window);
window.fetch = function(input, init) {
  const opts = init ? { ...init } : {};
  delete opts.credentials;

  const url = typeof input === 'string' ? input : (input instanceof Request ? input.url : '');
  const token = sessionStorage.getItem('session_token');
  if (token && url.includes('/api/')) {
    opts.headers = new Headers(opts.headers || {});
    if (!opts.headers.has('Authorization')) {
      opts.headers.set('Authorization', `Bearer ${token}`);
    }
  }

  return _fetch(input, opts);
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
