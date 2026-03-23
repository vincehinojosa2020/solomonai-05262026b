import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Search, Users, Mail, Phone, User } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { API_URL } from '@/lib/utils';

const STATUS_STYLES = {
  member: { bg: 'bg-blue-50', text: 'text-blue-700' },
  visitor: { bg: 'bg-amber-50', text: 'text-amber-700' },
  regular: { bg: 'bg-emerald-50', text: 'text-emerald-700' },
  inactive: { bg: 'bg-slate-100', text: 'text-slate-500' },
};

export default function PortalDirectory() {
  const { user, tenant } = useOutletContext();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [total, setTotal] = useState(0);

  const token = localStorage.getItem('session_token');

  useEffect(() => { fetchDirectory(); }, []);

  const fetchDirectory = async (searchTerm) => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.set('search', searchTerm);
      const res = await fetch(`${API_URL}/portal/directory?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to fetch directory:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value) => {
    setSearch(value);
    // Debounce search
    clearTimeout(window._dirSearchTimeout);
    window._dirSearchTimeout = setTimeout(() => fetchDirectory(value), 300);
  };

  const getAvatarColor = (name) => {
    const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-purple-500', 'bg-amber-500', 'bg-rose-500', 'bg-teal-500', 'bg-indigo-500'];
    const idx = (name || '').charCodeAt(0) % colors.length;
    return colors[idx];
  };

  if (loading) {
    return (
      <div className="space-y-4 py-6" data-testid="directory-loading">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="animate-pulse flex items-center gap-3 p-4 bg-white rounded-xl">
            <div className="w-10 h-10 bg-slate-200 rounded-full" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-200 rounded w-32" />
              <div className="h-3 bg-slate-100 rounded w-48" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-5" data-testid="portal-directory-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900" data-testid="directory-title">Church Directory</h1>
        <p className="text-sm text-slate-500 mt-1">Find and connect with members of {tenant?.name || 'your church'}</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder="Search by name..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          className="pl-10 bg-white"
          data-testid="directory-search"
        />
      </div>

      {/* Stats */}
      <div className="flex items-center gap-2">
        <Badge variant="secondary" data-testid="directory-count">
          <Users className="w-3.5 h-3.5 mr-1" />
          {total} member{total !== 1 ? 's' : ''}
        </Badge>
      </div>

      {/* Directory List */}
      {members.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center" data-testid="directory-empty">
          <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            {search ? 'No members found' : 'Directory is empty'}
          </h3>
          <p className="text-sm text-slate-500">
            {search ? 'Try a different search term.' : 'No members are visible in the directory yet.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {members.map((member, idx) => {
            const status = STATUS_STYLES[member.membership_status] || STATUS_STYLES.visitor;
            return (
              <div
                key={idx}
                className="flex items-center gap-3 p-4 bg-white rounded-xl border border-slate-100 hover:border-slate-200 transition-colors"
                data-testid={`directory-member-${idx}`}
              >
                <Avatar className="w-10 h-10">
                  <AvatarFallback className={`${getAvatarColor(member.name)} text-white text-sm font-semibold`}>
                    {member.avatar_initials || '?'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-slate-900 truncate" data-testid={`directory-member-name-${idx}`}>
                      {member.name}
                    </h3>
                    <Badge className={`${status.bg} ${status.text} text-xs`}>
                      {member.membership_status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                    {member.email && (
                      <a href={`mailto:${member.email}`} className="flex items-center gap-1 hover:text-blue-600 transition-colors" data-testid={`directory-member-email-${idx}`}>
                        <Mail className="w-3 h-3" />{member.email}
                      </a>
                    )}
                    {member.phone && (
                      <a href={`tel:${member.phone}`} className="flex items-center gap-1 hover:text-blue-600 transition-colors" data-testid={`directory-member-phone-${idx}`}>
                        <Phone className="w-3 h-3" />{member.phone}
                      </a>
                    )}
                  </div>
                  {member.groups && member.groups.length > 0 && (
                    <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                      {member.groups.slice(0, 3).map((g, gi) => (
                        <span key={gi} className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
                          {typeof g === 'object' ? g.name : g}
                        </span>
                      ))}
                      {member.groups.length > 3 && (
                        <span className="text-xs text-slate-400">+{member.groups.length - 3} more</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
