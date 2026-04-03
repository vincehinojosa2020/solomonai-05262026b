import { useRef, useCallback } from 'react';
import { Printer, AlertTriangle } from 'lucide-react';
import '@/styles/labels.css';

/**
 * LabelPrinter — renders child check-in labels and triggers window.print().
 * 
 * Props:
 *   children: array of { name, firstInitialLast, classroom, serviceTime, pickupCode, allergies, allergiesDetail, parentName }
 *   onClose: callback
 */
export function LabelPrinter({ checkins = [], onClose }) {
  const printRef = useRef();

  const handlePrint = useCallback(() => {
    // Inject the print root ID so CSS @media print only shows labels
    const original = document.body.innerHTML;
    const labelsHTML = printRef.current?.innerHTML || '';
    document.body.innerHTML = `<div id="print-label-root">${labelsHTML}</div>`;
    window.print();
    document.body.innerHTML = original;
    window.location.reload(); // restore React
  }, []);

  if (!checkins || checkins.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center" data-testid="label-printer-modal">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <Printer className="w-5 h-5 text-slate-700" />
            <h2 className="text-base font-semibold text-slate-900">Print Labels ({checkins.length} child{checkins.length > 1 ? 'ren' : ''})</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl no-print">&times;</button>
        </div>

        {/* Preview */}
        <div className="p-4" ref={printRef}>
          {checkins.map((c, i) => (
            <div key={i} className="mb-4">
              {/* Child Label */}
              <div className="label-sheet">
                <div className="label-child">
                  <div className="label-header">
                    <span>{c.serviceTime || 'Sunday 9:00 AM'}</span>
                    <span>Solomon AI</span>
                  </div>
                  <div className="label-body">
                    <div>
                      <div className="label-name">{c.firstInitialLast || c.name}</div>
                      <div className="label-room">{c.classroom || 'Children\'s Ministry'}</div>
                      {c.allergies && (
                        <div style={{ marginTop: 4, padding: '2px 6px', background: '#fef2f2', border: '1px solid #dc2626', borderRadius: 4, fontSize: '9pt', color: '#dc2626', fontWeight: 700 }}>
                          ALLERGY: {c.allergies}
                        </div>
                      )}
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className="label-code">{c.pickupCode}</div>
                      <div className="label-code-label">Pickup Code</div>
                    </div>
                  </div>
                </div>

                {/* Parent Receipt */}
                <div className="label-parent">
                  <div className="label-header">Parent Receipt — Keep This!</div>
                  <div className="label-body">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 700 }}>{c.name}</div>
                        <div style={{ fontSize: '9pt', color: '#6b7280' }}>{c.classroom} · {c.serviceTime}</div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div className="label-pickup-code">{c.pickupCode}</div>
                        <div style={{ fontSize: '7pt', color: '#6b7280', textTransform: 'uppercase' }}>Show to pick up</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Allergy Alert — only if child has allergies */}
                {c.allergies && (
                  <div className="label-allergy">
                    <div className="label-header">ALLERGY ALERT</div>
                    <div className="label-body">
                      <div className="label-name">{c.name}</div>
                      <div className="label-details">{c.allergiesDetail || c.allergies}</div>
                      {c.emergencyContact && (
                        <div style={{ fontSize: '9pt', color: '#6b7280', marginTop: 3 }}>Emergency: {c.emergencyContact}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-2 p-4 border-t border-slate-200 no-print">
          <button onClick={onClose} className="flex-1 py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Cancel</button>
          <button onClick={handlePrint} className="flex-1 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 flex items-center justify-center gap-1.5" data-testid="print-labels-btn">
            <Printer className="w-4 h-4" /> Print Labels
          </button>
        </div>
      </div>
    </div>
  );
}

/** TestLabelPrint — prints a single test label */
export function TestLabelPrint() {
  const demo = [{
    name: 'Emma Johnson',
    firstInitialLast: 'Emma J.',
    classroom: 'Kindergarten — Room 104',
    serviceTime: 'Sunday 9:00 AM',
    pickupCode: 'X7K2',
    allergies: 'Peanuts',
    allergiesDetail: 'Severe peanut allergy — use EpiPen',
    parentName: 'Sarah Johnson',
    emergencyContact: '(555) 234-5678',
  }];

  return <LabelPrinter checkins={demo} onClose={() => {}} />;
}
