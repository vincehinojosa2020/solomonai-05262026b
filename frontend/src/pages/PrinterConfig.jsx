import { useState, useEffect } from 'react';
import { Printer, Plus, Trash2, TestTube2, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function PrinterConfig() {
  const [printers, setPrinters] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', type: 'zebra', connection: 'network', ip_address: '', port: 9100 });

  const headers = () => { const t = sessionStorage.getItem('session_token'); return t ? { 'Authorization': `Bearer ${t}` } : {}; };

  const fetchPrinters = async () => {
    try { const res = await fetch(`${API_URL}/admin/printers`, { headers: headers() }); if (res.ok) { const d = await res.json(); setPrinters(d.printers || []); } } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchPrinters(); }, []);

  const addPrinter = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/printers`, { method: 'POST', headers: { ...headers(), 'Content-Type': 'application/json' }, body: JSON.stringify(form) });
      if (res.ok) { toast.success('Printer added'); setShowAdd(false); setForm({ name: '', type: 'zebra', connection: 'network', ip_address: '', port: 9100 }); fetchPrinters(); }
    } catch { toast.error('Failed to add'); }
  };

  const removePrinter = async (id) => {
    if (!confirm('Remove this printer?')) return;
    try { await fetch(`${API_URL}/admin/printers/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Removed'); fetchPrinters(); } catch { toast.error('Failed'); }
  };

  const testPrint = async (id) => {
    try {
      const res = await fetch(`${API_URL}/admin/printers/${id}/test`, { method: 'POST', headers: headers() });
      if (res.ok) { const d = await res.json(); toast.success(d.message || 'Test print sent'); }
    } catch { toast.error('Test failed'); }
  };

  return (
    <div className="space-y-4" data-testid="printer-config">
      <div className="flex items-center justify-between">
        <div><h2 className="text-lg font-bold text-slate-900">Printer Configuration</h2><p className="text-sm text-slate-500">Manage label printers for check-in stations</p></div>
        <Button onClick={() => setShowAdd(!showAdd)} size="sm" data-testid="add-printer-btn"><Plus className="w-3.5 h-3.5 mr-1" /> Add Printer</Button>
      </div>

      {showAdd && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs font-medium text-slate-500">NAME</label><input type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Main Lobby Printer" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="printer-name-input" /></div>
            <div><label className="text-xs font-medium text-slate-500">TYPE</label>
              <select value={form.type} onChange={e => setForm({...form, type: e.target.value})} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm">
                <option value="zebra">Zebra (ZD/GK series)</option><option value="brother">Brother QL series</option><option value="dymo">Dymo LabelWriter</option>
              </select></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs font-medium text-slate-500">CONNECTION</label>
              <select value={form.connection} onChange={e => setForm({...form, connection: e.target.value})} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm">
                <option value="network">Network (IP)</option><option value="usb">USB</option>
              </select></div>
            {form.connection === 'network' && (
              <div><label className="text-xs font-medium text-slate-500">IP ADDRESS</label><input type="text" value={form.ip_address} onChange={e => setForm({...form, ip_address: e.target.value})} placeholder="192.168.1.100" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            )}
          </div>
          <div className="flex gap-2"><Button onClick={addPrinter} disabled={!form.name} size="sm">Save Printer</Button><Button variant="outline" size="sm" onClick={() => setShowAdd(false)}>Cancel</Button></div>
        </div>
      )}

      {printers.length === 0 && !showAdd ? (
        <div className="text-center py-12 bg-white border border-slate-200 rounded-xl">
          <Printer className="w-12 h-12 text-slate-300 mx-auto" />
          <p className="text-slate-500 mt-3">No printers configured</p>
          <p className="text-slate-400 text-sm mt-1">Add a label printer for check-in label printing</p>
          <p className="text-xs text-slate-400 mt-4">Supported: Zebra ZD/GK, Brother QL, Dymo LabelWriter</p>
        </div>
      ) : (
        <div className="space-y-2">
          {printers.map(p => (
            <div key={p.id} className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-xl" data-testid={`printer-${p.id}`}>
              <div className="flex items-center gap-3">
                <Printer className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="text-sm font-medium text-slate-800">{p.name}</p>
                  <p className="text-xs text-slate-400">{p.type} | {p.connection}{p.ip_address ? ` | ${p.ip_address}` : ''}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => testPrint(p.id)} data-testid={`test-print-${p.id}`}><TestTube2 className="w-3.5 h-3.5 mr-1" /> Test</Button>
                <Button variant="outline" size="sm" onClick={() => removePrinter(p.id)} className="text-red-500 hover:text-red-600"><Trash2 className="w-3.5 h-3.5" /></Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
