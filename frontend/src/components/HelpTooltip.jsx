import { useState, useRef, useEffect } from 'react';
import { HelpCircle, X, ChevronRight, Lightbulb, MessageCircle, Mail } from 'lucide-react';
import { HELP_CONTENT } from '@/lib/helpContent';

/**
 * HelpTooltip — reusable contextual help button.
 * 
 * Usage: <HelpTooltip featureKey="giving" />
 * Or: <HelpTooltip title="Custom Title" what="..." howTo={[]} proTip="..." />
 */
export function HelpTooltip({ featureKey, title, what, howTo, proTip, className = '' }) {
  const [open, setOpen] = useState(false);
  const panelRef = useRef();

  // Resolve content from registry or direct props
  const content = featureKey ? HELP_CONTENT[featureKey] : null;
  const resolvedTitle = title || content?.title || 'Help';
  const resolvedWhat = what || content?.what || '';
  const resolvedHowTo = howTo || content?.howTo || [];
  const resolvedTip = proTip || content?.proTip || '';
  const showSupport = content?.support !== false;

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div className={`relative inline-flex items-center ${className}`} data-testid={`help-${featureKey || 'custom'}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-5 h-5 rounded-full border border-slate-300 bg-white text-slate-400 hover:text-blue-600 hover:border-blue-400 flex items-center justify-center transition-all"
        title={`Help: ${resolvedTitle}`}
        data-testid={`help-btn-${featureKey || 'custom'}`}
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          {/* Panel */}
          <div
            ref={panelRef}
            className="fixed right-4 top-20 z-50 w-80 bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden"
            data-testid={`help-panel-${featureKey || 'custom'}`}
            style={{ maxHeight: 'calc(100vh - 100px)', overflowY: 'auto' }}
          >
            {/* Header */}
            <div className="bg-slate-900 text-white p-4 flex items-start justify-between">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <h3 className="font-semibold text-sm leading-snug">{resolvedTitle}</h3>
              </div>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white ml-2 flex-shrink-0">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* What is this */}
              {resolvedWhat && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">What this is</p>
                  <p className="text-sm text-slate-700 leading-relaxed">{resolvedWhat}</p>
                </div>
              )}

              {/* How to use it */}
              {resolvedHowTo.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">How to use it</p>
                  <ol className="space-y-1.5">
                    {resolvedHowTo.map((step, i) => (
                      <li key={i} className="flex gap-2 text-sm text-slate-600">
                        <span className="flex-shrink-0 w-4 h-4 rounded-full bg-blue-100 text-blue-600 text-[10px] font-bold flex items-center justify-center mt-0.5">
                          {i + 1}
                        </span>
                        <span className="leading-snug">{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Pro Tip */}
              {resolvedTip && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs font-semibold text-amber-700 mb-0.5">Pro tip</p>
                      <p className="text-xs text-amber-700 leading-snug">{resolvedTip}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Need help */}
              {showSupport && (
                <div className="border-t border-slate-100 pt-3">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Need help?</p>
                  <div className="space-y-1.5">
                    <button
                      onClick={() => {
                        setOpen(false);
                        // Open Solomon chat
                        document.dispatchEvent(new CustomEvent('openSolomon', { detail: { message: `How do I use ${resolvedTitle}?` } }));
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 bg-slate-50 hover:bg-blue-50 rounded-lg text-sm text-slate-700 transition-colors"
                      data-testid={`help-ask-solomon-${featureKey}`}
                    >
                      <MessageCircle className="w-3.5 h-3.5 text-blue-500" />
                      Ask Solomon AI
                    </button>
                    <a
                      href="mailto:support@solomonai.us?subject=Help with Solomon AI"
                      className="w-full flex items-center gap-2 px-3 py-2 bg-slate-50 hover:bg-slate-100 rounded-lg text-sm text-slate-700 transition-colors"
                    >
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      support@solomonai.us
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
