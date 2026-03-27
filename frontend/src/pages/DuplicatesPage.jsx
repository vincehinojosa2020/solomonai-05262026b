import { useState, useEffect } from 'react';
import {
  Users, Merge, AlertTriangle, Loader2, ChevronRight, Check, X, Search
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';

export default function DuplicatesPage() {
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [merging, setMerging] = useState(null);
  const [showMerge, setShowMerge] = useState(null);

  const fetchDuplicates = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/people/duplicates`);
      if (res.ok) { const d = await res.json(); setDuplicates(d.duplicates || []); }
    } catch { toast.error('Failed to detect duplicates'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchDuplicates(); }, []);

  const handleMerge = async (keepId, mergeId) => {
    setMerging(keepId + mergeId);
    try {
      const res = await fetch(`${API_URL}/admin/people/merge`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keep_id: keepId, merge_id: mergeId })
      });
      if (res.ok) {
        toast.success('Profiles merged successfully');
        setShowMerge(null);
        fetchDuplicates();
      }
    } catch { toast.error('Merge failed'); }
    finally { setMerging(null); }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return { bg: '#fee2e2', text: '#dc2626', label: 'High' };
    if (score >= 50) return { bg: '#fef3c7', text: '#d97706', label: 'Medium' };
    return { bg: '#f0fdf4', text: '#16a34a', label: 'Low' };
  };

  return (
    <div className="page-container" data-testid="duplicates-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>Duplicate Detection</h1>
          <p style={{ fontSize: 14, color: '#64748b', marginTop: 4 }}>
            Find and merge duplicate member profiles to keep your database clean
          </p>
        </div>
        <Button onClick={fetchDuplicates} variant="outline" data-testid="scan-duplicates-btn">
          <Search className="w-4 h-4 mr-2" /> Scan Again
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Loader2 className="w-6 h-6 animate-spin" style={{ margin: '0 auto 12px', color: '#64748b' }} />
          <p style={{ fontSize: 13, color: '#94a3b8' }}>Scanning for duplicates...</p>
        </div>
      ) : duplicates.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
          <Check className="w-12 h-12" style={{ margin: '0 auto 12px', color: '#22c55e' }} />
          <p style={{ fontSize: 16, fontWeight: 700, color: '#0f172a' }}>No duplicates found</p>
          <p style={{ fontSize: 14, marginTop: 4 }}>Your member database is clean</p>
        </div>
      ) : (
        <>
          <div style={{ padding: '12px 16px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 10, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
            <AlertTriangle className="w-4 h-4" style={{ color: '#f59e0b' }} />
            <span style={{ fontSize: 13, color: '#92400e', fontWeight: 500 }}>
              Found {duplicates.length} potential duplicate{duplicates.length !== 1 ? 's' : ''}. Review and merge to keep your database clean.
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {duplicates.map((dup, idx) => {
              const scoreInfo = getScoreColor(dup.score);
              return (
                <div key={idx} data-testid={`duplicate-pair-${idx}`}
                  style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: '20px 24px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Merge className="w-4 h-4" style={{ color: '#f59e0b' }} />
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>Potential Duplicate</span>
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 100,
                        background: scoreInfo.bg, color: scoreInfo.text
                      }}>
                        {scoreInfo.label} ({dup.score}%)
                      </span>
                    </div>
                    <Button size="sm" onClick={() => setShowMerge(dup)} data-testid={`merge-btn-${idx}`}>
                      <Merge className="w-3.5 h-3.5 mr-1" /> Review & Merge
                    </Button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 12, alignItems: 'center' }}>
                    <PersonCard person={dup.person_a} />
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, color: '#d1d5db' }}>
                      <Merge className="w-5 h-5" />
                      <span style={{ fontSize: 10, fontWeight: 600 }}>MERGE</span>
                    </div>
                    <PersonCard person={dup.person_b} />
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Merge Dialog */}
      <Dialog open={!!showMerge} onOpenChange={() => setShowMerge(null)}>
        <DialogContent className="sm:max-w-[520px]">
          <DialogHeader>
            <DialogTitle>Merge Profiles</DialogTitle>
            <DialogDescription>Choose which profile to keep. The other profile's data will be merged in.</DialogDescription>
          </DialogHeader>
          {showMerge && (
            <div style={{ marginTop: 12 }}>
              <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>
                Click "Keep This" on the profile you want to keep. The other profile will be merged and deleted.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <MergeOption
                  person={showMerge.person_a}
                  other={showMerge.person_b}
                  onKeep={() => handleMerge(showMerge.person_a.user_id, showMerge.person_b.user_id)}
                  isProcessing={merging === showMerge.person_a.user_id + showMerge.person_b.user_id}
                />
                <MergeOption
                  person={showMerge.person_b}
                  other={showMerge.person_a}
                  onKeep={() => handleMerge(showMerge.person_b.user_id, showMerge.person_a.user_id)}
                  isProcessing={merging === showMerge.person_b.user_id + showMerge.person_a.user_id}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                <Button variant="outline" onClick={() => setShowMerge(null)}>Cancel</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PersonCard({ person }) {
  return (
    <div style={{ padding: 14, background: '#f8fafc', borderRadius: 10, border: '1px solid #e5e7eb' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%', background: '#e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: '#475569'
        }}>
          {(person.name || '?').charAt(0).toUpperCase()}
        </div>
        <div>
          <p style={{ fontSize: 14, fontWeight: 700, color: '#0f172a' }}>{person.name || 'No name'}</p>
          <p style={{ fontSize: 12, color: '#64748b' }}>{person.membership_status || 'Unknown'}</p>
        </div>
      </div>
      <div style={{ fontSize: 12, color: '#64748b', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {person.email && <span>{person.email}</span>}
        {person.phone && <span>{person.phone}</span>}
      </div>
    </div>
  );
}

function MergeOption({ person, other, onKeep, isProcessing }) {
  return (
    <div style={{ padding: 14, border: '2px solid #e5e7eb', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 40, height: 40, borderRadius: '50%', background: '#e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 700, color: '#475569'
        }}>
          {(person.name || '?').charAt(0).toUpperCase()}
        </div>
        <div>
          <p style={{ fontSize: 14, fontWeight: 700, color: '#0f172a' }}>{person.name}</p>
          <p style={{ fontSize: 12, color: '#64748b' }}>{person.email}</p>
        </div>
      </div>
      <Button size="sm" onClick={onKeep} disabled={isProcessing} data-testid={`keep-${person.user_id}`}>
        {isProcessing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Keep This'}
      </Button>
    </div>
  );
}
