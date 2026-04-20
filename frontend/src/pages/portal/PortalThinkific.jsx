import { useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { safeHref } from '@/utils/sanitize';

export default function PortalThinkific() {
  const [thinkificUrl, setThinkificUrl] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchThinkific = async () => {
      try {
        const res = await fetch(`${API_URL}/portal/thinkific`);
        if (res.ok) {
          const data = await res.json();
          setThinkificUrl(data.thinkific_url || '');
        }
      } catch (error) {
        console.error('Failed to load Thinkific:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchThinkific();
  }, []);

  return (
    <div className="portal-thinkific" data-testid="portal-thinkific-page">
      <div className="portal-thinkific-header">
        <div>
          <span className="portal-tag">External LMS</span>
          <h1>Thinkific</h1>
          <p>Jump into your church’s Thinkific classrooms without leaving Solomon AI.</p>
        </div>
        {thinkificUrl && (
          <a
            href={safeHref(thinkificUrl)}
            target="_blank"
            rel="noreferrer"
            className="portal-thinkific-link"
            data-testid="thinkific-open"
          >
            Open Thinkific
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>

      <div className="portal-thinkific-body">
        {loading ? (
          <div className="portal-thinkific-loading" data-testid="thinkific-loading">
            Loading Thinkific...
          </div>
        ) : thinkificUrl ? (
          <iframe
            title="Thinkific Player"
            src={thinkificUrl}
            className="portal-thinkific-iframe"
            data-testid="thinkific-iframe"
          />
        ) : (
          <div className="portal-thinkific-empty" data-testid="thinkific-empty">
            <p>Your church hasn’t connected Thinkific yet. Check back soon.</p>
          </div>
        )}
      </div>
    </div>
  );
}
