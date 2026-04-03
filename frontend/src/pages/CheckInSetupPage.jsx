import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Settings, MapPin, Monitor, Tag, AlertTriangle, Shield, BarChart3,
  Plus, Edit2, Trash2, Save, X, ChevronDown, ChevronUp, Users,
  Loader2, Printer, UserCheck, Baby, Clock, Calendar, TrendingUp, Tablet, Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import { API_URL, formatDate } from '@/lib/utils';
import { toast } from 'sonner';
import KioskCheckin from '@/components/KioskCheckin';
import { LabelPrinter } from '@/components/LabelPrinter';
import { HelpTooltip } from '@/components/HelpTooltip';

const STATION_MODES = [
  { id: 'self', label: 'Self Check-in', desc: 'Kiosk mode — families check in themselves', icon: '🖥️' },
  { id: 'manned', label: 'Manned Station', desc: 'Attended — volunteer checks in families', icon: '🧑' },
  { id: 'roster', label: 'Roster Mode', desc: 'Pre-loaded class roster for quick check-in', icon: '📋' },
  { id: 'quick', label: 'Quick Check-in', desc: 'Fast tap-to-check-in for known families', icon: '⚡' },
];

const LABEL_FIELDS = [
  'child_name', 'classroom', 'security_code', 'allergies_icon', 'allergies_detail',
  'medical_notes', 'parent_name', 'parent_phone', 'age', 'barcode',
];

export default function CheckInSetupPage() {
  const { tenant } = useOutletContext();
  const [activeTab, setActiveTab] = useState('locations');
  const [locations, setLocations] = useState([]);
  const [stations, setStations] = useState([]);
  const [labels, setLabels] = useState([]);
  const [medicalAlerts, setMedicalAlerts] = useState([]);
  const [trends, setTrends] = useState(null);
  const [firstTimers, setFirstTimers] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showLocationForm, setShowLocationForm] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  const [locationForm, setLocationForm] = useState({ name: '', room: '', age_range: '', capacity: 30, folder: 'General' });

  const [showStationForm, setShowStationForm] = useState(false);
  const [stationForm, setStationForm] = useState({ name: '', mode: 'self', description: '', location_ids: [] });

  const [showLabelForm, setShowLabelForm] = useState(false);
  const [labelForm, setLabelForm] = useState({ name: '', type: 'name_tag', width: 4, height: 2, fields: ['child_name', 'classroom', 'security_code'], layout: { font_size: 18, show_allergies: true, show_barcode: true, show_logo: true } });

  const [showMedicalDialog, setShowMedicalDialog] = useState(false);
  const [editingChild, setEditingChild] = useState(null);
  const [medicalForm, setMedicalForm] = useState({ allergies: '', medical_notes: '', medical_severity: 'low' });

  const [showKiosk, setShowKiosk] = useState(false);
  const [showTestLabel, setShowTestLabel] = useState(false);
  const [labelSize, setLabelSize] = useState('dymo_4x2');

  const [showGuardianForm, setShowGuardianForm] = useState(false);
  const [guardianChild, setGuardianChild] = useState(null);
  const [guardians, setGuardians] = useState([]);
  const [guardianForm, setGuardianForm] = useState({ name: '', relationship: '', phone: '', pin_code: '' });

  const token = sessionStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    await Promise.all([fetchLocations(), fetchStations(), fetchLabels(), fetchMedical(), fetchTrends(), fetchFirstTimers()]);
    setLoading(false);
  };

  const fetchLocations = async () => {
    try { const r = await fetch(`${API_URL}/admin/checkin/locations`, { headers: authHeaders }); if (r.ok) { const d = await r.json(); setLocations(d.locations || []); } } catch (e) { console.error(e); }
  };
  const fetchStations = async () => {
    try { const r = await fetch(`${API_URL}/admin/checkin/stations`, { headers: authHeaders }); if (r.ok) { const d = await r.json(); setStations(d.stations || []); } } catch (e) { console.error(e); }
  };
  const fetchLabels = async () => {
    try { const r = await fetch(`${API_URL}/admin/checkin/labels`, { headers: authHeaders }); if (r.ok) { const d = await r.json(); setLabels(d.templates || []); } } catch (e) { console.error(e); }
  };
  const fetchMedical = async () => {
    try { const r = await fetch(`${API_URL}/admin/checkin/medical-alerts`, { headers: authHeaders }); if (r.ok) { const d = await r.json(); setMedicalAlerts(d.alerts || []); } } catch (e) { console.error(e); }
  };
  const fetchTrends = async () => {
    try { const r = await fetch(`${API_URL}/admin/checkin/reports/trends`, { headers: authHeaders }); if (r.ok) { const d = await r.json(); setTrends(d); } } catch (e) { console.error(e); }
  };
  const fetchFirstTimers = async () => {
    try { const r = await fetch(`${API_URL}/admin/checkin/reports/first-timers`, { headers: authHeaders }); if (r.ok) { const d = await r.json(); setFirstTimers(d.first_timers || []); } } catch (e) { console.error(e); }
  };

  // Location CRUD
  const saveLocation = async () => {
    if (!locationForm.name) { toast.error('Name required'); return; }
    const url = editingLocation ? `${API_URL}/admin/checkin/locations/${editingLocation.id}` : `${API_URL}/admin/checkin/locations`;
    const method = editingLocation ? 'PUT' : 'POST';
    try {
      const r = await fetch(url, { method, headers: authHeaders, body: JSON.stringify(locationForm) });
      if (r.ok) { toast.success(editingLocation ? 'Updated' : 'Created'); setShowLocationForm(false); setEditingLocation(null); setLocationForm({ name: '', room: '', age_range: '', capacity: 30, folder: 'General' }); fetchLocations(); }
    } catch (e) { toast.error('Failed'); }
  };
  const deleteLocation = async (id) => {
    try { await fetch(`${API_URL}/admin/checkin/locations/${id}`, { method: 'DELETE', headers: authHeaders }); toast.success('Deleted'); fetchLocations(); } catch (e) { toast.error('Failed'); }
  };

  // Station CRUD
  const saveStation = async () => {
    if (!stationForm.name) { toast.error('Name required'); return; }
    try {
      const r = await fetch(`${API_URL}/admin/checkin/stations`, { method: 'POST', headers: authHeaders, body: JSON.stringify(stationForm) });
      if (r.ok) { toast.success('Station created'); setShowStationForm(false); setStationForm({ name: '', mode: 'self', description: '', location_ids: [] }); fetchStations(); }
    } catch (e) { toast.error('Failed'); }
  };
  const deleteStation = async (id) => {
    try { await fetch(`${API_URL}/admin/checkin/stations/${id}`, { method: 'DELETE', headers: authHeaders }); toast.success('Deleted'); fetchStations(); } catch (e) { toast.error('Failed'); }
  };

  // Label CRUD
  const saveLabel = async () => {
    if (!labelForm.name) { toast.error('Name required'); return; }
    try {
      const r = await fetch(`${API_URL}/admin/checkin/labels`, { method: 'POST', headers: authHeaders, body: JSON.stringify(labelForm) });
      if (r.ok) { toast.success('Template created'); setShowLabelForm(false); setLabelForm({ name: '', type: 'name_tag', width: 4, height: 2, fields: ['child_name', 'classroom', 'security_code'], layout: { font_size: 18, show_allergies: true, show_barcode: true, show_logo: true } }); fetchLabels(); }
    } catch (e) { toast.error('Failed'); }
  };
  const deleteLabel = async (id) => {
    try { await fetch(`${API_URL}/admin/checkin/labels/${id}`, { method: 'DELETE', headers: authHeaders }); toast.success('Deleted'); fetchLabels(); } catch (e) { toast.error('Failed'); }
  };

  // Medical update
  const saveMedical = async () => {
    if (!editingChild) return;
    try {
      const r = await fetch(`${API_URL}/admin/checkin/children/${editingChild.id}/medical`, { method: 'PUT', headers: authHeaders, body: JSON.stringify(medicalForm) });
      if (r.ok) { toast.success('Medical info updated'); setShowMedicalDialog(false); setEditingChild(null); fetchMedical(); }
    } catch (e) { toast.error('Failed'); }
  };

  // Guardian CRUD
  const openGuardians = async (child) => {
    setGuardianChild(child);
    try {
      const r = await fetch(`${API_URL}/admin/checkin/children/${child.id}/guardians`, { headers: authHeaders });
      if (r.ok) { const d = await r.json(); setGuardians(d.guardians || []); }
    } catch (e) { console.error(e); }
    setShowGuardianForm(true);
  };
  const addGuardian = async () => {
    if (!guardianForm.name) { toast.error('Name required'); return; }
    try {
      await fetch(`${API_URL}/admin/checkin/children/${guardianChild.id}/guardians`, { method: 'POST', headers: authHeaders, body: JSON.stringify(guardianForm) });
      toast.success('Guardian added');
      setGuardianForm({ name: '', relationship: '', phone: '', pin_code: '' });
      const r = await fetch(`${API_URL}/admin/checkin/children/${guardianChild.id}/guardians`, { headers: authHeaders });
      if (r.ok) { const d = await r.json(); setGuardians(d.guardians || []); }
    } catch (e) { toast.error('Failed'); }
  };
  const removeGuardian = async (guardianId) => {
    try {
      await fetch(`${API_URL}/admin/checkin/children/${guardianChild.id}/guardians/${guardianId}`, { method: 'DELETE', headers: authHeaders });
      toast.success('Guardian removed');
      setGuardians(guardians.filter(g => g.id !== guardianId));
    } catch (e) { toast.error('Failed'); }
  };

  // Group locations by folder
  const locationsByFolder = locations.reduce((acc, loc) => {
    const folder = loc.folder || 'General';
    if (!acc[folder]) acc[folder] = [];
    acc[folder].push(loc);
    return acc;
  }, {});

  if (loading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="checkin-setup-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <Settings className="w-7 h-7 text-violet-600" />
            Check-In Setup
          </h1>
          <p className="text-sm text-slate-500 mt-1">Configure locations, stations, labels, and security settings</p>
        </div>
        <Button
          onClick={() => setShowKiosk(true)}
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white"
          data-testid="launch-kiosk-btn"
        >
          <Tablet className="w-4 h-4" /> Launch Kiosk Mode
        </Button>
        <HelpTooltip featureKey="checkin" />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1 flex-wrap">
          <TabsTrigger value="locations" data-testid="tab-locations"><MapPin className="w-4 h-4 mr-1.5" />Locations</TabsTrigger>
          <TabsTrigger value="stations" data-testid="tab-stations"><Monitor className="w-4 h-4 mr-1.5" />Stations</TabsTrigger>
          <TabsTrigger value="labels" data-testid="tab-labels"><Tag className="w-4 h-4 mr-1.5" />Labels</TabsTrigger>
          <TabsTrigger value="printers" data-testid="tab-printers"><Printer className="w-4 h-4 mr-1.5" />Printers</TabsTrigger>
          <TabsTrigger value="medical" data-testid="tab-medical"><AlertTriangle className="w-4 h-4 mr-1.5" />Medical Alerts</TabsTrigger>
          <TabsTrigger value="guardians" data-testid="tab-guardians"><Shield className="w-4 h-4 mr-1.5" />Guardians</TabsTrigger>
          <TabsTrigger value="reports" data-testid="tab-reports"><BarChart3 className="w-4 h-4 mr-1.5" />Reports</TabsTrigger>
        </TabsList>

        {/* LOCATIONS TAB */}
        <TabsContent value="locations" className="space-y-4 mt-4">
          <div className="flex items-center justify-end">
            <Button onClick={() => { setEditingLocation(null); setLocationForm({ name: '', room: '', age_range: '', capacity: 30, folder: 'General' }); setShowLocationForm(true); }} data-testid="add-location-btn">
              <Plus className="w-4 h-4 mr-1.5" /> Add Location
            </Button>
          </div>
          {Object.entries(locationsByFolder).map(([folder, locs]) => (
            <div key={folder} className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-1">{folder}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {locs.map(loc => (
                  <div key={loc.id} className="bg-white border border-slate-200 rounded-xl p-4 group" data-testid={`location-${loc.id}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="text-sm font-semibold text-slate-800">{loc.name}</h4>
                        <p className="text-xs text-slate-500 mt-0.5">{loc.room}</p>
                        <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                          <span><Baby className="w-3 h-3 inline mr-0.5" />{loc.age_range}</span>
                          <span><Users className="w-3 h-3 inline mr-0.5" />{loc.capacity} cap</span>
                        </div>
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => { setEditingLocation(loc); setLocationForm({ name: loc.name, room: loc.room, age_range: loc.age_range, capacity: loc.capacity, folder: loc.folder }); setShowLocationForm(true); }} className="p-1 text-slate-400 hover:text-blue-600"><Edit2 className="w-3.5 h-3.5" /></button>
                        <button onClick={() => deleteLocation(loc.id)} className="p-1 text-slate-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </TabsContent>

        {/* STATIONS TAB */}
        <TabsContent value="stations" className="space-y-4 mt-4">
          <div className="flex items-center justify-end">
            <Button onClick={() => setShowStationForm(true)} data-testid="add-station-btn">
              <Plus className="w-4 h-4 mr-1.5" /> Add Station
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {stations.map(st => {
              const mode = STATION_MODES.find(m => m.id === st.mode) || STATION_MODES[0];
              return (
                <div key={st.id} className="bg-white border border-slate-200 rounded-xl p-5 group" data-testid={`station-${st.id}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-lg bg-violet-50 flex items-center justify-center text-xl">{mode.icon}</div>
                      <div>
                        <h4 className="text-sm font-semibold text-slate-800">{st.name}</h4>
                        <Badge variant="outline" className="mt-1 text-xs text-violet-600 border-violet-200">{mode.label}</Badge>
                        {st.description && <p className="text-xs text-slate-400 mt-1">{st.description}</p>}
                      </div>
                    </div>
                    <button onClick={() => deleteStation(st.id)} className="p-1 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 mt-2">
            <h4 className="text-sm font-semibold text-slate-700 mb-3">Station Modes Reference</h4>
            <div className="grid grid-cols-2 gap-3">
              {STATION_MODES.map(m => (
                <div key={m.id} className="flex items-start gap-2.5 text-xs">
                  <span className="text-lg">{m.icon}</span>
                  <div><p className="font-semibold text-slate-700">{m.label}</p><p className="text-slate-500">{m.desc}</p></div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* LABELS TAB */}
        <TabsContent value="labels" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              <Printer className="w-3.5 h-3.5 inline mr-1" />
              Printer driver integration (Brother/Dymo/Zebra/Citizen) requires a specialist — flag for $300 consultant (6 hours)
            </p>
            <Button onClick={() => setShowLabelForm(true)} data-testid="add-label-btn">
              <Plus className="w-4 h-4 mr-1.5" /> New Template
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {labels.map(lbl => (
              <div key={lbl.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden group" data-testid={`label-${lbl.id}`}>
                {/* Label Preview */}
                <div className="bg-slate-800 p-4 relative" style={{ aspectRatio: `${lbl.width}/${lbl.height}` }}>
                  <div className="bg-white rounded-lg p-3 h-full flex flex-col justify-between text-slate-800" style={{ fontSize: `${Math.min(lbl.layout?.font_size || 16, 14)}px` }}>
                    <div className="flex justify-between items-start">
                      {lbl.layout?.show_logo && <div className="w-6 h-6 bg-blue-100 rounded flex items-center justify-center text-[8px] text-blue-600 font-bold">S</div>}
                      {lbl.layout?.show_allergies && <AlertTriangle className="w-4 h-4 text-red-500" />}
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-sm">Child Name</p>
                      <p className="text-[10px] text-slate-500">Classroom</p>
                    </div>
                    <div className="flex justify-between items-end text-[8px] text-slate-400">
                      <span>SEC-0000</span>
                      {lbl.layout?.show_barcode && <div className="flex gap-[1px]">{[...Array(12)].map((_, i) => <div key={i} className="w-[2px] bg-slate-800" style={{ height: `${6 + (i % 3) * 3}px` }} />)}</div>}
                    </div>
                  </div>
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{lbl.name}</p>
                      <p className="text-xs text-slate-400">{lbl.width}" x {lbl.height}" &middot; {lbl.fields?.length || 0} fields</p>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                      {lbl.is_default && <Badge className="text-[10px] bg-blue-50 text-blue-600 border-blue-200">Default</Badge>}
                      <button onClick={() => deleteLabel(lbl.id)} className="p-1 text-slate-300 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* MEDICAL ALERTS TAB */}
        <TabsContent value="medical" className="space-y-4 mt-4">
          {medicalAlerts.length === 0 ? (
            <div className="bg-white border rounded-xl p-12 text-center" data-testid="medical-empty">
              <AlertTriangle className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm text-slate-500">No children with medical alerts on file.</p>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm" data-testid="medical-table">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Child</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Allergies</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Medical Notes</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Severity</th>
                    <th className="text-right p-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {medicalAlerts.map(child => (
                    <tr key={child.id} className="border-t border-slate-100" data-testid={`medical-${child.id}`}>
                      <td className="p-3 font-medium text-slate-700">{child.name}</td>
                      <td className="p-3">
                        {child.allergies ? (
                          <Badge className="bg-red-50 text-red-700 border-red-200 text-xs">{child.allergies}</Badge>
                        ) : '-'}
                      </td>
                      <td className="p-3 text-slate-500 text-xs max-w-[200px] truncate">{child.medical_notes || child.notes || '-'}</td>
                      <td className="p-3">
                        <Badge variant="outline" className={
                          child.medical_severity === 'high' ? 'text-red-600 border-red-200' :
                          child.medical_severity === 'medium' ? 'text-amber-600 border-amber-200' :
                          'text-slate-500 border-slate-200'
                        }>{child.medical_severity || 'low'}</Badge>
                      </td>
                      <td className="p-3 text-right">
                        <Button size="sm" variant="outline" className="text-xs" onClick={() => {
                          setEditingChild(child);
                          setMedicalForm({ allergies: child.allergies || '', medical_notes: child.medical_notes || child.notes || '', medical_severity: child.medical_severity || 'low' });
                          setShowMedicalDialog(true);
                        }} data-testid={`edit-medical-${child.id}`}>
                          <Edit2 className="w-3 h-3 mr-1" />Edit
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        {/* PRINTERS TAB */}
        <TabsContent value="printers" className="space-y-4 mt-4" data-testid="printers-tab">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-slate-900">Label Printing</h3>
                <p className="text-xs text-slate-500 mt-0.5">Uses browser Web Print — works with DYMO, Brother, and standard printers</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => setShowTestLabel(true)} data-testid="print-test-label-btn">
                <Eye className="w-3.5 h-3.5 mr-1.5" /> Print Test Label
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {[
                { id: 'dymo_4x2', label: 'DYMO LabelWriter', size: '2.25" × 4"', notes: 'LabelWriter 450/550 series' },
                { id: 'brother_4x3', label: 'Brother QL Series', size: '2.4" × 3.9"', notes: 'QL-700, QL-800, QL-810' },
                { id: 'standard', label: 'Standard Printer', size: '4" × 2.25"', notes: 'Any printer — full sheet per label' },
              ].map(s => (
                <button
                  key={s.id}
                  onClick={() => setLabelSize(s.id)}
                  className={`p-4 border rounded-xl text-left transition-all ${labelSize === s.id ? 'border-violet-500 bg-violet-50' : 'border-slate-200 hover:border-slate-300'}`}
                  data-testid={`label-size-${s.id}`}
                >
                  <p className="font-semibold text-sm text-slate-800">{s.label}</p>
                  <p className="text-xs text-violet-600 font-mono mt-0.5">{s.size}</p>
                  <p className="text-xs text-slate-400 mt-1">{s.notes}</p>
                </button>
              ))}
            </div>
            <div className="bg-slate-50 rounded-lg p-4 text-sm text-slate-600">
              <p className="font-semibold mb-2">How label printing works:</p>
              <ol className="list-decimal list-inside space-y-1 text-xs text-slate-500">
                <li>When a child is checked in, a "Print Labels" button appears automatically</li>
                <li>Labels open in a print preview — click Print or Cmd+P</li>
                <li>Select your label printer in the print dialog</li>
                <li>Each child gets a child label + parent receipt + allergy alert (if applicable)</li>
                <li>For kiosk mode, labels print automatically after check-in confirmation</li>
              </ol>
            </div>
          </div>
        </TabsContent>

        {/* GUARDIANS TAB */}
        <TabsContent value="guardians" className="space-y-4 mt-4">
          <p className="text-sm text-slate-500">Select a child from the medical alerts or check-in system to manage authorized guardians.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {medicalAlerts.map(child => (
              <div key={child.id} className="bg-white border border-slate-200 rounded-xl p-4 cursor-pointer hover:border-violet-300 transition-colors"
                onClick={() => openGuardians(child)} data-testid={`guardian-card-${child.id}`}>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-violet-50 flex items-center justify-center">
                    <Baby className="w-5 h-5 text-violet-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{child.name}</p>
                    <p className="text-xs text-slate-400">{(child.authorized_guardians || []).length} authorized guardian(s)</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* REPORTS TAB */}
        <TabsContent value="reports" className="space-y-4 mt-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="report-total">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                  <UserCheck className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{trends?.total_checkins || 0}</p>
                  <p className="text-xs text-slate-500">Total Check-ins (30 days)</p>
                </div>
              </div>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="report-rooms">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-violet-50 flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-violet-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{trends?.by_room?.length || 0}</p>
                  <p className="text-xs text-slate-500">Active Rooms</p>
                </div>
              </div>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="report-first-timers">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{firstTimers.length}</p>
                  <p className="text-xs text-slate-500">First-Time Visitors (30 days)</p>
                </div>
              </div>
            </div>
          </div>

          {/* Daily Trend */}
          {trends?.daily_trend?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="report-trend-chart">
              <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Daily Check-in Trend</h4>
              <div className="flex items-end gap-1 h-32">
                {trends.daily_trend.map((d, i) => {
                  const maxCount = Math.max(...trends.daily_trend.map(t => t.count));
                  const height = maxCount > 0 ? (d.count / maxCount) * 100 : 0;
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1" title={`${d.date}: ${d.count}`}>
                      <div className="w-full bg-blue-500 rounded-t" style={{ height: `${Math.max(height, 4)}%` }} />
                      <span className="text-[8px] text-slate-400 rotate-[-45deg] whitespace-nowrap">{d.date.slice(5)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Room Breakdown */}
          {trends?.by_room?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="report-by-room">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">Check-ins by Room</h4>
              <div className="space-y-2">
                {trends.by_room.map((r, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-sm text-slate-700 w-32 truncate">{r.room}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-5 overflow-hidden">
                      <div className="bg-violet-500 h-full rounded-full" style={{ width: `${(r.count / (trends.total_checkins || 1)) * 100}%` }} />
                    </div>
                    <span className="text-sm font-semibold text-slate-700 w-10 text-right">{r.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* First Timers */}
          {firstTimers.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="report-first-timers-list">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">First-Time Visitors</h4>
              <div className="space-y-2">
                {firstTimers.map((ft, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 bg-emerald-50/50 rounded-lg text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center"><Baby className="w-3.5 h-3.5 text-emerald-600" /></div>
                      <span className="font-medium text-slate-700">{ft.child_name}</span>
                    </div>
                    <div className="text-xs text-slate-400">
                      First visit: {formatDate(ft.first_checkin)} &middot; {ft.total_checkins} total
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Location Form Dialog */}
      <Dialog open={showLocationForm} onOpenChange={setShowLocationForm}>
        <DialogContent data-testid="location-dialog">
          <DialogHeader><DialogTitle>{editingLocation ? 'Edit Location' : 'Add Location'}</DialogTitle></DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Name</Label><Input value={locationForm.name} onChange={e => setLocationForm({ ...locationForm, name: e.target.value })} data-testid="loc-name" placeholder="e.g. Nursery" /></div>
              <div><Label>Room</Label><Input value={locationForm.room} onChange={e => setLocationForm({ ...locationForm, room: e.target.value })} data-testid="loc-room" placeholder="Room 100" /></div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><Label>Age Range</Label><Input value={locationForm.age_range} onChange={e => setLocationForm({ ...locationForm, age_range: e.target.value })} data-testid="loc-age" placeholder="0-2" /></div>
              <div><Label>Capacity</Label><Input type="number" value={locationForm.capacity} onChange={e => setLocationForm({ ...locationForm, capacity: parseInt(e.target.value) || 0 })} data-testid="loc-capacity" /></div>
              <div><Label>Folder</Label>
                <select className="w-full rounded-md border border-slate-200 p-2 text-sm" value={locationForm.folder} onChange={e => setLocationForm({ ...locationForm, folder: e.target.value })} data-testid="loc-folder">
                  <option value="Early Childhood">Early Childhood</option>
                  <option value="Preschool">Preschool</option>
                  <option value="Elementary">Elementary</option>
                  <option value="Youth">Youth</option>
                  <option value="Specialized">Specialized</option>
                  <option value="General">General</option>
                </select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLocationForm(false)}>Cancel</Button>
            <Button onClick={saveLocation} data-testid="save-location-btn">Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Station Form Dialog */}
      <Dialog open={showStationForm} onOpenChange={setShowStationForm}>
        <DialogContent data-testid="station-dialog">
          <DialogHeader><DialogTitle>Add Station</DialogTitle></DialogHeader>
          <div className="space-y-3 py-2">
            <div><Label>Station Name</Label><Input value={stationForm.name} onChange={e => setStationForm({ ...stationForm, name: e.target.value })} data-testid="station-name" placeholder="e.g. Main Lobby Kiosk" /></div>
            <div>
              <Label>Mode</Label>
              <div className="grid grid-cols-2 gap-2 mt-1">
                {STATION_MODES.map(m => (
                  <button key={m.id} onClick={() => setStationForm({ ...stationForm, mode: m.id })}
                    className={`p-3 rounded-lg border text-left transition-colors ${stationForm.mode === m.id ? 'border-violet-400 bg-violet-50' : 'border-slate-200 hover:border-slate-300'}`}
                    data-testid={`mode-${m.id}`}>
                    <span className="text-lg">{m.icon}</span>
                    <p className="text-xs font-semibold text-slate-700 mt-1">{m.label}</p>
                    <p className="text-[10px] text-slate-500">{m.desc}</p>
                  </button>
                ))}
              </div>
            </div>
            <div><Label>Description</Label><Input value={stationForm.description} onChange={e => setStationForm({ ...stationForm, description: e.target.value })} data-testid="station-desc" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStationForm(false)}>Cancel</Button>
            <Button onClick={saveStation} data-testid="save-station-btn">Create Station</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Label Form Dialog */}
      <Dialog open={showLabelForm} onOpenChange={setShowLabelForm}>
        <DialogContent className="sm:max-w-[520px]" data-testid="label-dialog">
          <DialogHeader><DialogTitle>New Label Template</DialogTitle></DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Template Name</Label><Input value={labelForm.name} onChange={e => setLabelForm({ ...labelForm, name: e.target.value })} data-testid="label-name" /></div>
              <div><Label>Type</Label>
                <select className="w-full rounded-md border border-slate-200 p-2 text-sm" value={labelForm.type} onChange={e => setLabelForm({ ...labelForm, type: e.target.value })} data-testid="label-type">
                  <option value="name_tag">Name Tag</option>
                  <option value="security">Security Label</option>
                  <option value="allergy">Allergy Alert</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Width (inches)</Label><Input type="number" value={labelForm.width} onChange={e => setLabelForm({ ...labelForm, width: parseFloat(e.target.value) || 4 })} data-testid="label-width" /></div>
              <div><Label>Height (inches)</Label><Input type="number" value={labelForm.height} onChange={e => setLabelForm({ ...labelForm, height: parseFloat(e.target.value) || 2 })} data-testid="label-height" /></div>
            </div>
            <div>
              <Label>Fields to Include</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {LABEL_FIELDS.map(f => (
                  <button key={f} onClick={() => {
                    const fields = labelForm.fields.includes(f) ? labelForm.fields.filter(x => x !== f) : [...labelForm.fields, f];
                    setLabelForm({ ...labelForm, fields });
                  }} className={`px-2 py-1 rounded text-xs border transition-colors ${labelForm.fields.includes(f) ? 'bg-violet-50 text-violet-700 border-violet-300' : 'bg-slate-50 text-slate-500 border-slate-200'}`}
                    data-testid={`field-${f}`}>{f.replace(/_/g, ' ')}</button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={labelForm.layout.show_allergies} onChange={e => setLabelForm({ ...labelForm, layout: { ...labelForm.layout, show_allergies: e.target.checked } })} />Show allergy icon</label>
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={labelForm.layout.show_barcode} onChange={e => setLabelForm({ ...labelForm, layout: { ...labelForm.layout, show_barcode: e.target.checked } })} />Show barcode</label>
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={labelForm.layout.show_logo} onChange={e => setLabelForm({ ...labelForm, layout: { ...labelForm.layout, show_logo: e.target.checked } })} />Show logo</label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLabelForm(false)}>Cancel</Button>
            <Button onClick={saveLabel} data-testid="save-label-btn">Create Template</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Medical Edit Dialog */}
      <Dialog open={showMedicalDialog} onOpenChange={setShowMedicalDialog}>
        <DialogContent data-testid="medical-dialog">
          <DialogHeader><DialogTitle>Edit Medical Info — {editingChild?.name}</DialogTitle></DialogHeader>
          <div className="space-y-3 py-2">
            <div><Label>Allergies</Label><Input value={medicalForm.allergies} onChange={e => setMedicalForm({ ...medicalForm, allergies: e.target.value })} data-testid="med-allergies" placeholder="e.g. Peanuts, Dairy" /></div>
            <div><Label>Medical Notes</Label><Input value={medicalForm.medical_notes} onChange={e => setMedicalForm({ ...medicalForm, medical_notes: e.target.value })} data-testid="med-notes" placeholder="Any special instructions" /></div>
            <div><Label>Severity</Label>
              <select className="w-full rounded-md border border-slate-200 p-2 text-sm" value={medicalForm.medical_severity} onChange={e => setMedicalForm({ ...medicalForm, medical_severity: e.target.value })} data-testid="med-severity">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High — Requires immediate attention</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMedicalDialog(false)}>Cancel</Button>
            <Button onClick={saveMedical} data-testid="save-medical-btn">Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Guardians Dialog */}
      <Dialog open={showGuardianForm} onOpenChange={setShowGuardianForm}>
        <DialogContent className="sm:max-w-[520px]" data-testid="guardians-dialog">
          <DialogHeader><DialogTitle>Authorized Guardians — {guardianChild?.name}</DialogTitle></DialogHeader>
          <div className="space-y-3 py-2 max-h-[400px] overflow-y-auto">
            {guardians.length > 0 && (
              <div className="space-y-2">
                {guardians.map(g => (
                  <div key={g.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg" data-testid={`guardian-${g.id}`}>
                    <div>
                      <p className="text-sm font-medium text-slate-700">{g.name}</p>
                      <p className="text-xs text-slate-400">{g.relationship} {g.phone && `&middot; ${g.phone}`}</p>
                    </div>
                    <button onClick={() => removeGuardian(g.id)} className="text-red-400 hover:text-red-600"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                ))}
              </div>
            )}
            <div className="border-t border-slate-100 pt-3 space-y-2">
              <p className="text-xs font-semibold text-slate-500">Add Guardian</p>
              <div className="grid grid-cols-2 gap-2">
                <Input placeholder="Name" value={guardianForm.name} onChange={e => setGuardianForm({ ...guardianForm, name: e.target.value })} data-testid="guardian-name" />
                <Input placeholder="Relationship" value={guardianForm.relationship} onChange={e => setGuardianForm({ ...guardianForm, relationship: e.target.value })} data-testid="guardian-rel" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Input placeholder="Phone" value={guardianForm.phone} onChange={e => setGuardianForm({ ...guardianForm, phone: e.target.value })} data-testid="guardian-phone" />
                <Input placeholder="PIN Code" value={guardianForm.pin_code} onChange={e => setGuardianForm({ ...guardianForm, pin_code: e.target.value })} data-testid="guardian-pin" />
              </div>
              <Button size="sm" onClick={addGuardian} data-testid="add-guardian-btn"><Plus className="w-3.5 h-3.5 mr-1" />Add Guardian</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Kiosk Mode */}
      {showKiosk && (
        <KioskCheckin
          tenantId={tenant?.id}
          onExit={() => setShowKiosk(false)}
        />
      )}

      {/* Test Label Print */}
      {showTestLabel && (
        <LabelPrinter
          checkins={[{
            name: 'Emma Johnson', firstInitialLast: 'Emma J.',
            classroom: 'Kindergarten — Room 104', serviceTime: 'Sunday 9:00 AM',
            pickupCode: 'X7K2', allergies: 'Peanuts',
            allergiesDetail: 'Severe peanut allergy — carry EpiPen',
            parentName: 'Sarah Johnson', emergencyContact: '(555) 234-5678',
          }]}
          onClose={() => setShowTestLabel(false)}
        />
      )}
    </div>
  );
}
