import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Globe } from 'lucide-react';
import PlatformTransactions from './PlatformTransactions';

/**
 * Standalone page wrapper for PlatformTransactions.
 *
 * Renders the God-Mode CEO transaction feed at its own dedicated route
 * `/platform/transactions`, independent of the GodModeDashboard tab chrome.
 * This is the entry point the exec-level links, emails, and deep-link specs
 * use (/platform/transactions), and is the URL documented in reports.
 */
export default function PlatformTransactionsPage() {
  const navigate = useNavigate();
  const token = sessionStorage.getItem('session_token');

  return (
    <div className="min-h-screen bg-slate-50" data-testid="platform-transactions-page">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-screen-2xl mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate('/godmode')}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 transition-colors"
            data-testid="back-to-godmode"
          >
            <ChevronLeft className="w-4 h-4" /> God Mode
          </button>
          <div className="h-6 w-px bg-slate-200" />
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center">
              <Globe className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-slate-900">Platform Transactions</h1>
              <p className="text-xs text-slate-500">All Stripe activity across every connected church</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-6 py-6">
        <PlatformTransactions token={token} />
      </div>
    </div>
  );
}
