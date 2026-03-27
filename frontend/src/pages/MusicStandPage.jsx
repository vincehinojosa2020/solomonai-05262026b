import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Music, ChevronLeft, ChevronRight, Maximize2, Minimize2, Clock, Hash
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export default function MusicStandPage() {
  const { planId } = useParams();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const res = await fetch(`${API_URL}/music-stand/${planId}`);
        if (res.ok) { const d = await res.json(); setPlan(d); }
      } catch {} finally { setLoading(false); }
    };
    fetchPlan();
  }, [planId]);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        setCurrentIndex(i => Math.min(i + 1, (plan?.items?.length || 1) - 1));
      } else if (e.key === 'ArrowLeft') {
        setCurrentIndex(i => Math.max(i - 1, 0));
      } else if (e.key === 'f') {
        toggleFullscreen();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [plan]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
        <p style={{ color: '#94a3b8', fontSize: 16 }}>Loading Music Stand...</p>
      </div>
    );
  }

  if (!plan) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
        <p style={{ color: '#94a3b8', fontSize: 16 }}>Plan not found</p>
      </div>
    );
  }

  const items = plan.items || [];
  const current = items[currentIndex];

  return (
    <div data-testid="music-stand-page" style={{ minHeight: '100vh', background: '#0f172a', color: '#e2e8f0', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 24px', borderBottom: '1px solid #1e293b', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Music className="w-5 h-5" style={{ color: '#3b82f6' }} />
          <div>
            <p style={{ fontSize: 16, fontWeight: 700 }}>{plan.title}</p>
            <p style={{ fontSize: 12, color: '#64748b' }}>{plan.date} | Music Stand</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: '#64748b' }}>
            {currentIndex + 1} / {items.length}
          </span>
          <Button size="sm" variant="outline" onClick={toggleFullscreen}
            style={{ color: '#e2e8f0', borderColor: '#334155' }}>
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Set list sidebar + content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Set list */}
        <div style={{ width: 220, borderRight: '1px solid #1e293b', overflowY: 'auto', flexShrink: 0 }}>
          {items.map((item, idx) => (
            <button key={item.id || idx} onClick={() => setCurrentIndex(idx)}
              data-testid={`ms-item-${idx}`}
              style={{
                width: '100%', padding: '12px 16px', textAlign: 'left', border: 'none',
                background: idx === currentIndex ? '#1e293b' : 'transparent',
                borderLeft: idx === currentIndex ? '3px solid #3b82f6' : '3px solid transparent',
                cursor: 'pointer', transition: 'all 0.1s'
              }}>
              <p style={{ fontSize: 13, fontWeight: idx === currentIndex ? 700 : 500, color: idx === currentIndex ? '#e2e8f0' : '#94a3b8' }}>
                {item.title || item.song?.title || 'Untitled'}
              </p>
              <div style={{ display: 'flex', gap: 8, marginTop: 3, fontSize: 11, color: '#475569' }}>
                <span>{item.type}</span>
                {item.duration && <span>{item.duration}min</span>}
                {(item.key || item.song?.default_key) && <span style={{ color: '#3b82f6' }}>{item.key || item.song?.default_key}</span>}
              </div>
            </button>
          ))}
        </div>

        {/* Main content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {current ? (
            <>
              {/* Song header */}
              <div style={{ padding: '20px 32px', borderBottom: '1px solid #1e293b', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>
                      {current.title || current.song?.title || 'Untitled'}
                    </h2>
                    {current.song?.artist && (
                      <p style={{ fontSize: 14, color: '#64748b' }}>{current.song.artist}</p>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    {(current.key || current.song?.default_key) && (
                      <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>KEY</p>
                        <p style={{ fontSize: 20, fontWeight: 800, color: '#3b82f6', fontFamily: 'monospace' }}>
                          {current.key || current.song?.default_key}
                        </p>
                      </div>
                    )}
                    {(current.bpm || current.song?.bpm) && (
                      <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>BPM</p>
                        <p style={{ fontSize: 20, fontWeight: 800, color: '#f59e0b', fontFamily: 'monospace' }}>
                          {current.bpm || current.song?.bpm}
                        </p>
                      </div>
                    )}
                    {current.duration && (
                      <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>TIME</p>
                        <p style={{ fontSize: 20, fontWeight: 800, color: '#22c55e', fontFamily: 'monospace' }}>
                          {current.duration}m
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Lyrics / Notes */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
                {(current.song?.lyrics || current.notes) ? (
                  <pre style={{
                    fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
                    fontSize: 18, lineHeight: 2.0, whiteSpace: 'pre-wrap', color: '#e2e8f0'
                  }}>
                    {current.song?.lyrics || current.notes}
                  </pre>
                ) : (
                  <div style={{ textAlign: 'center', padding: 60, color: '#475569' }}>
                    <Music className="w-10 h-10" style={{ margin: '0 auto 12px' }} />
                    <p style={{ fontSize: 15, fontWeight: 600 }}>No lyrics or notes for this item</p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#475569' }}>
              <p>No items in this service plan</p>
            </div>
          )}

          {/* Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 32px', borderTop: '1px solid #1e293b', flexShrink: 0 }}>
            <Button size="sm" variant="outline" onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0} style={{ color: '#e2e8f0', borderColor: '#334155' }}
              data-testid="ms-prev">
              <ChevronLeft className="w-4 h-4 mr-1" /> Previous
            </Button>
            <span style={{ fontSize: 12, color: '#475569' }}>
              Use arrow keys or spacebar to navigate | F for fullscreen
            </span>
            <Button size="sm" variant="outline" onClick={() => setCurrentIndex(Math.min(items.length - 1, currentIndex + 1))}
              disabled={currentIndex >= items.length - 1} style={{ color: '#e2e8f0', borderColor: '#334155' }}
              data-testid="ms-next">
              Next <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
