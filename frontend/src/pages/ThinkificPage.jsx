import { useEffect, useState } from 'react';
import { ExternalLink, Link2, Save } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';

export default function ThinkificPage() {
  const [thinkificUrl, setThinkificUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchThinkific = async () => {
      try {
        const res = await fetch(`${API_URL}/admin/thinkific`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          setThinkificUrl(data.thinkific_url || '');
        }
      } catch (error) {
        console.error('Failed to load Thinkific settings:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchThinkific();
  }, []);

  const handleSave = async () => {
    if (!thinkificUrl.trim()) {
      toast.error('Please enter a Thinkific URL');
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/admin/thinkific`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ thinkific_url: thinkificUrl.trim() })
      });
      if (res.ok) {
        toast.success('Thinkific updated');
      } else {
        toast.error('Failed to save Thinkific URL');
      }
    } catch (error) {
      toast.error('Failed to save Thinkific URL');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="thinkific-page" data-testid="thinkific-admin-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Thinkific</h1>
          <p className="page-subtitle">Launch your external LMS directly inside Solomon AI.</p>
        </div>
      </div>

      <div className="thinkific-grid">
        <div className="thinkific-card" data-testid="thinkific-settings-card">
          <div className="thinkific-card-header">
            <Link2 className="w-4 h-4" />
            <div>
              <h3>Thinkific URL</h3>
              <p>Paste the Thinkific site or course player URL you want members to see.</p>
            </div>
          </div>
          <div className="thinkific-form">
            <Input
              value={thinkificUrl}
              onChange={(e) => setThinkificUrl(e.target.value)}
              placeholder="https://yourchurch.thinkific.com"
              data-testid="thinkific-url-input"
            />
            <Button
              onClick={handleSave}
              disabled={saving}
              className="thinkific-save-btn"
              data-testid="thinkific-save-btn"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
          <div className="thinkific-helper">
            <span>Need the embed URL? Use the Thinkific site or course player URL that opens the curriculum.</span>
          </div>
        </div>

        <div className="thinkific-preview" data-testid="thinkific-preview">
          <div className="thinkific-preview-header">
            <h3>Member Preview</h3>
            {thinkificUrl && (
              <a
                href={thinkificUrl}
                target="_blank"
                rel="noreferrer"
                className="thinkific-external"
                data-testid="thinkific-open-link"
              >
                Open Thinkific
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
          {loading ? (
            <div className="thinkific-loading">Loading preview...</div>
          ) : thinkificUrl ? (
            <iframe
              title="Thinkific Preview"
              src={thinkificUrl}
              className="thinkific-iframe"
              data-testid="thinkific-iframe"
            />
          ) : (
            <div className="thinkific-empty" data-testid="thinkific-empty">
              <p>Add a Thinkific URL to enable the embedded player.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
