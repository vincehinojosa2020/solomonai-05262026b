import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Search, Filter, Download, Plus, ChevronLeft, ChevronRight,
  MoreHorizontal, Mail, UserPlus, Trash2, Check, Upload
} from 'lucide-react';
import { SectionTutorial, TUTORIALS } from '@/components/SectionTutorial';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { API_URL, formatCurrency, formatDate, getInitials, getStatusColor, debounce } from '@/lib/utils';
import AddPersonModal from '@/components/modals/AddPersonModal';
import { FeatureEducationHeader } from '@/components/FeatureEducationHeader';
import { HelpTooltip } from '@/components/HelpTooltip';

const StatusBadge = ({ status }) => (
  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
    {status.charAt(0).toUpperCase() + status.slice(1)}
  </span>
);

export default function PeopleList({ type = 'people' }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('last_name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [selectedIds, setSelectedIds] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkUpdate, setShowBulkUpdate] = useState(false);
  const [bulkStatus, setBulkStatus] = useState('');
  const [bulkCampus, setBulkCampus] = useState('');
  const [bulkLoading, setBulkLoading] = useState(false);

  const statusCounts = {
    all: total,
    member: people.filter(p => p.membership_status === 'member').length,
    visitor: people.filter(p => p.membership_status === 'visitor').length,
    regular: people.filter(p => p.membership_status === 'regular').length,
    inactive: people.filter(p => p.membership_status === 'inactive').length,
  };

  useEffect(() => {
    const action = searchParams.get('action');
    if (action === 'add') {
      setShowAddModal(true);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchPeople();
  }, [page, perPage, statusFilter, sortBy, sortOrder]);

  useEffect(() => {
    const debouncedSearch = debounce(() => {
      setPage(1);
      fetchPeople();
    }, 300);
    
    debouncedSearch();
  }, [search]);

  const fetchPeople = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      
      if (search) params.append('search', search);
      if (statusFilter !== 'all') params.append('status', statusFilter);
      
      const response = await fetch(`${API_URL}/people?${params}`);
      const data = await response.json();
      
      setPeople(data.data);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to fetch people:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedIds(people.map(p => p.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id, checked) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter(i => i !== id));
    }
  };

  const handlePersonAdded = () => {
    setShowAddModal(false);
    searchParams.delete('action');
    setSearchParams(searchParams);
    fetchPeople();
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="people-list-page">
      <FeatureEducationHeader featureKey="people" />
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Members</h1>
          <p className="page-subtitle">Manage your church members and visitors</p>
        </div>
        <div className="flex items-center gap-3">
          <SectionTutorial {...TUTORIALS.people} />
          <HelpTooltip featureKey="people" />
          <Button variant="outline" className="h-9" onClick={() => navigate('/admin/members/import')} data-testid="import-btn">
            <Upload className="w-4 h-4 mr-2" />
            Import CSV
          </Button>
          <Button className="h-9 btn-primary" onClick={() => setShowAddModal(true)} data-testid="add-person-btn">
            <Plus className="w-4 h-4 mr-2" />
            Add Person
          </Button>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {selectedIds.length > 0 && (
        <div className="bulk-actions-bar" data-testid="bulk-actions-bar">
          <span className="selected-count">{selectedIds.length} selected</span>
          <div className="actions">
            <button className="bulk-action-btn" data-testid="bulk-update-status" onClick={() => setShowBulkUpdate(true)}>
              <Check className="w-4 h-4" />
              Update Status
            </button>
            <button className="bulk-action-btn" data-testid="bulk-add-group" onClick={() => toast.info('Group assignment coming soon')}>
              <UserPlus className="w-4 h-4" />
              Add to Group
            </button>
            <button className="bulk-action-btn" data-testid="bulk-send-email" onClick={() => { navigate('/communications'); }}>
              <Mail className="w-4 h-4" />
              Send Email
            </button>
            <button className="bulk-action-btn" data-testid="bulk-export" onClick={async () => {
              const token = sessionStorage.getItem('session_token');
              const res = await fetch(`${API_URL}/admin/people/bulk-export`, {
                method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: selectedIds }),
              });
              if (res.ok) { const blob = await res.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'people_export.csv'; a.click(); }
              else { toast.info('Export CSV from the header button for all members'); }
            }}>
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
          <button className="ml-auto text-white/70 hover:text-white text-sm" onClick={() => setSelectedIds([])}>
            Clear selection
          </button>
        </div>
      )}

      {/* Bulk Update Modal */}
      {showBulkUpdate && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Update {selectedIds.length} People</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-500">NEW STATUS</label>
                <select className="w-full mt-1 border border-slate-200 rounded-lg px-3 py-2 text-sm" value={bulkStatus} onChange={e => setBulkStatus(e.target.value)}>
                  <option value="">No change</option>
                  <option value="member">Member</option>
                  <option value="regular">Regular Attender</option>
                  <option value="visitor">Visitor</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <Button variant="outline" className="flex-1" onClick={() => setShowBulkUpdate(false)}>Cancel</Button>
              <Button className="flex-1 btn-primary" disabled={!bulkStatus || bulkLoading} onClick={async () => {
                setBulkLoading(true);
                const token = sessionStorage.getItem('session_token');
                const res = await fetch(`${API_URL}/admin/people/bulk-update`, {
                  method: 'POST',
                  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                  body: JSON.stringify({ ids: selectedIds, updates: { membership_status: bulkStatus } }),
                });
                if (res.ok) { toast.success(`Updated ${selectedIds.length} people`); setShowBulkUpdate(false); setSelectedIds([]); setBulkStatus(''); }
                else toast.error('Update failed');
                setBulkLoading(false);
              }} data-testid="bulk-update-confirm">{bulkLoading ? 'Updating...' : 'Apply Update'}</Button>
            </div>
          </div>
        </div>
      )}

      {/* Table Container */}
      <div className="data-table-container">
        {/* Filters Header */}
        <div className="data-table-header">
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search by name, email, phone..."
                className="pl-9 w-80 h-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                data-testid="search-input"
              />
            </div>

            {/* Status Filter Pills */}
            <div className="flex items-center gap-2">
              {['all', 'member', 'visitor', 'regular', 'inactive'].map((status) => (
                <button
                  key={status}
                  className={`filter-pill ${statusFilter === status ? 'active' : ''}`}
                  onClick={() => { setStatusFilter(status); setPage(1); }}
                  data-testid={`filter-${status}`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                  <span className="count">
                    {status === 'all' ? total : statusCounts[status] || 0}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Sort */}
            <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setPage(1); }}>
              <SelectTrigger className="w-40 h-9" data-testid="sort-select">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="last_name">Name</SelectItem>
                <SelectItem value="created_at">Date Added</SelectItem>
                <SelectItem value="last_attended_at">Last Attended</SelectItem>
                <SelectItem value="ytd_giving">YTD Giving</SelectItem>
              </SelectContent>
            </Select>

            {/* Export */}
            <Button variant="outline" size="sm" data-testid="export-btn">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th className="w-12">
                  <Checkbox
                    checked={selectedIds.length === people.length && people.length > 0}
                    onCheckedChange={handleSelectAll}
                    data-testid="select-all-checkbox"
                  />
                </th>
                <th>Name</th>
                <th>Status</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Campus</th>
                <th className="text-right">YTD Giving</th>
                <th className="w-20">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(10)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8}>
                      <div className="h-12 bg-slate-100 rounded animate-pulse"></div>
                    </td>
                  </tr>
                ))
              ) : people.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-slate-400">
                    No members found
                  </td>
                </tr>
              ) : (
                people.map((person) => (
                  <tr 
                    key={person.id} 
                    className="hover:bg-slate-50 cursor-pointer"
                    data-testid={`person-row-${person.id}`}
                  >
                    <td onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedIds.includes(person.id)}
                        onCheckedChange={(checked) => handleSelectOne(person.id, checked)}
                      />
                    </td>
                    <td>
                      <Link 
                        to={`/people/${person.id}`}
                        className="flex items-center gap-3 hover:text-blue-600"
                      >
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={person.photo_url} />
                          <AvatarFallback className="text-xs">
                            {getInitials(person.first_name, person.last_name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium text-slate-900">
                            {person.first_name} {person.last_name}
                          </p>
                          {person.preferred_name && person.preferred_name !== person.first_name && (
                            <p className="text-xs text-slate-400">({person.preferred_name})</p>
                          )}
                        </div>
                      </Link>
                    </td>
                    <td>
                      <StatusBadge status={person.membership_status} />
                    </td>
                    <td className="text-slate-600">{person.email || '—'}</td>
                    <td className="text-slate-600 font-data text-sm">{person.mobile_phone || '—'}</td>
                    <td className="text-slate-600">{person.campus || '—'}</td>
                    <td className="text-right font-data text-slate-900">
                      {formatCurrency(person.ytd_giving || 0)}
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" data-testid={`actions-${person.id}`}>
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/people/${person.id}`)}>
                            View Profile
                          </DropdownMenuItem>
                          <DropdownMenuItem>Edit</DropdownMenuItem>
                          <DropdownMenuItem>Add to Group</DropdownMenuItem>
                          <DropdownMenuItem>Send Email</DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">Archive</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="pagination">
          <div className="pagination-info">
            Showing {((page - 1) * perPage) + 1}–{Math.min(page * perPage, total)} of {total.toLocaleString()} members
          </div>
          <div className="flex items-center gap-4">
            <Select value={perPage.toString()} onValueChange={(v) => { setPerPage(parseInt(v)); setPage(1); }}>
              <SelectTrigger className="w-20 h-8" data-testid="per-page-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
            <div className="pagination-controls">
              <button
                className="pagination-btn"
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                data-testid="prev-page-btn"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const pageNum = page <= 3 ? i + 1 : page - 2 + i;
                if (pageNum > totalPages) return null;
                return (
                  <button
                    key={pageNum}
                    className={`pagination-btn ${page === pageNum ? 'active' : ''}`}
                    onClick={() => setPage(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                className="pagination-btn"
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
                data-testid="next-page-btn"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Add Person Modal */}
      {showAddModal && (
        <AddPersonModal 
          onClose={() => { setShowAddModal(false); searchParams.delete('action'); setSearchParams(searchParams); }}
          onSuccess={handlePersonAdded}
        />
      )}
    </div>
  );
}
