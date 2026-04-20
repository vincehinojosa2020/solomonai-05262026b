import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, User, Users, Calendar, X, ArrowRight } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { safeImgSrc } from '@/utils/sanitize';

export default function CommandPalette({ onClose }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && results[selectedIndex]) {
        handleSelect(results[selectedIndex]);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [results, selectedIndex, onClose]);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const searchDebounced = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        setResults(data);
        setSelectedIndex(0);
      } catch (error) {
        console.error('Search failed:', error);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(searchDebounced);
  }, [query]);

  const handleSelect = (item) => {
    if (item.type === 'person') {
      navigate(`/people/${item.id}`);
    } else if (item.type === 'group') {
      navigate(`/groups/${item.id}`);
    } else if (item.type === 'event') {
      navigate(`/events`);
    }
    onClose();
  };

  const getIcon = (type) => {
    switch (type) {
      case 'person': return User;
      case 'group': return Users;
      case 'event': return Calendar;
      default: return Search;
    }
  };

  const quickActions = [
    { title: 'Add Person', path: '/people?action=add', icon: User },
    { title: 'Record Donation', path: '/giving?action=add', icon: Search },
    { title: 'View Dashboard', path: '/dashboard', icon: ArrowRight },
  ];

  return (
    <div 
      className="command-palette-overlay" 
      onClick={onClose}
      data-testid="command-palette-overlay"
    >
      <div 
        className="command-palette" 
        onClick={(e) => e.stopPropagation()}
        data-testid="command-palette"
      >
        <div className="command-input">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search people, groups, events..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            data-testid="command-search-input"
          />
          <button 
            onClick={onClose}
            className="p-1 rounded hover:bg-slate-100"
            data-testid="command-close-btn"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        <div className="command-results">
          {query.length < 2 && (
            <>
              <div className="command-group">
                <div className="command-group-label">Quick Actions</div>
                {quickActions.map((action, idx) => (
                  <div
                    key={action.path || action.title}
                    className="command-item cursor-pointer"
                    onClick={() => { navigate(action.path); onClose(); }}
                    data-testid={`quick-action-${idx}`}
                  >
                    <action.icon className="icon" />
                    <span className="title">{action.title}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {loading && (
            <div className="p-4 text-center text-slate-400 text-sm">
              Searching...
            </div>
          )}

          {!loading && query.length >= 2 && results.length === 0 && (
            <div className="p-8 text-center text-slate-400 text-sm">
              No results found for "{query}"
            </div>
          )}

          {!loading && results.length > 0 && (
            <div className="command-group">
              <div className="command-group-label">Results</div>
              {results.map((item, idx) => {
                const Icon = getIcon(item.type);
                return (
                  <div
                    key={item.id}
                    className={`command-item cursor-pointer ${idx === selectedIndex ? 'active' : ''}`}
                    onClick={() => handleSelect(item)}
                    data-testid={`search-result-${idx}`}
                  >
                    {item.photo_url ? (
                      <img src={safeImgSrc(item.photo_url)} alt="" className="w-8 h-8 rounded-full" />
                    ) : (
                      <Icon className="icon" />
                    )}
                    <span className="title">{item.title}</span>
                    <span className="subtitle">{item.subtitle}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
