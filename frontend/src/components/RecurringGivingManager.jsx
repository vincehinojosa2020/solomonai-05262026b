import { useState, useEffect } from 'react';
import { RefreshCw, Plus, Pencil, Pause, Play, X, CreditCard, Calendar, DollarSign, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

const FREQUENCY_LABELS = {
  weekly: 'Weekly',
  biweekly: 'Every 2 Weeks',
  monthly: 'Monthly',
  annually: 'Annually',
};

const STATUS_STYLES = {
  active: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  paused: 'bg-amber-50 text-amber-700 border-amber-200',
  cancelled: 'bg-slate-100 text-slate-500 border-slate-200',
};

function ScheduleCard({ schedule, funds, onEdit, onPause, onResume, onCancel }) {
  return (
    <div
      className="relative rounded-lg border p-4 transition-all hover:shadow-sm"
      style={{
        borderColor: schedule.status === 'active' ? '#d1fae5' : schedule.status === 'paused' ? '#fef3c7' : '#e2e8f0',
        background: schedule.status === 'active' ? '#f0fdf4' : '#fafafa',
      }}
      data-testid={`recurring-schedule-${schedule.id}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-slate-500" />
          <span className="font-semibold text-slate-800">{formatCurrency(schedule.amount)}</span>
          <span className="text-xs text-slate-500">/ {FREQUENCY_LABELS[schedule.frequency] || schedule.frequency}</span>
        </div>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${STATUS_STYLES[schedule.status] || STATUS_STYLES.cancelled}`}>
          {schedule.status?.toUpperCase()}
        </span>
      </div>

      <div className="space-y-1 text-xs text-slate-600 mb-3">
        <div className="flex items-center gap-1.5">
          <DollarSign className="w-3 h-3" />
          <span>Fund: {schedule.fund_name || 'General Fund'}</span>
        </div>
        {schedule.card_last_four && (
          <div className="flex items-center gap-1.5">
            <CreditCard className="w-3 h-3" />
            <span>{schedule.card_brand || 'Card'} •••• {schedule.card_last_four}</span>
          </div>
        )}
        {schedule.next_charge_date && schedule.status === 'active' && (
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3 h-3" />
            <span>Next charge: {schedule.next_charge_date}</span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <Calendar className="w-3 h-3" />
          <span>Started: {schedule.start_date}</span>
        </div>
      </div>

      {schedule.status !== 'cancelled' && (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs h-7 px-2"
            onClick={() => onEdit(schedule)}
            data-testid={`edit-recurring-${schedule.id}`}
          >
            <Pencil className="w-3 h-3 mr-1" /> Edit
          </Button>
          {schedule.status === 'active' ? (
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7 px-2"
              onClick={() => onPause(schedule.id)}
              data-testid={`pause-recurring-${schedule.id}`}
            >
              <Pause className="w-3 h-3 mr-1" /> Pause
            </Button>
          ) : schedule.status === 'paused' ? (
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7 px-2"
              onClick={() => onResume(schedule.id)}
              data-testid={`resume-recurring-${schedule.id}`}
            >
              <Play className="w-3 h-3 mr-1" /> Resume
            </Button>
          ) : null}
          <Button
            variant="outline"
            size="sm"
            className="text-xs h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
            onClick={() => onCancel(schedule.id)}
            data-testid={`cancel-recurring-${schedule.id}`}
          >
            <X className="w-3 h-3 mr-1" /> Cancel
          </Button>
        </div>
      )}
    </div>
  );
}

function CreateEditModal({ schedule, funds, onClose, onSave }) {
  const isEdit = !!schedule;
  const [amount, setAmount] = useState(schedule?.amount?.toString() || '');
  const [fundId, setFundId] = useState(schedule?.fund_id || 'general');
  const [frequency, setFrequency] = useState(schedule?.frequency || 'monthly');
  const [saving, setSaving] = useState(false);

  const selectedFund = funds.find(f => f.id === fundId);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    setSaving(true);
    try {
      await onSave({
        amount: parseFloat(amount),
        fund_id: fundId,
        fund_name: selectedFund?.name || 'General Fund',
        frequency,
      });
      onClose();
    } catch (err) {
      toast.error(err.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="recurring-modal">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">
            {isEdit ? 'Edit Recurring Gift' : 'Set Up Recurring Gift'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded" data-testid="close-recurring-modal">
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5 uppercase tracking-wide">Amount</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-medium">$</span>
              <input
                type="number"
                step="0.01"
                min="1"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full pl-7 pr-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0.00"
                data-testid="recurring-amount-input"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5 uppercase tracking-wide">Fund</label>
            <select
              value={fundId}
              onChange={(e) => setFundId(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="recurring-fund-select"
            >
              {funds.map((f) => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5 uppercase tracking-wide">Frequency</label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(FREQUENCY_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setFrequency(key)}
                  className={`px-3 py-2 border rounded-lg text-sm transition-all ${
                    frequency === key
                      ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium'
                      : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                  data-testid={`freq-btn-${key}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="flex-1 bg-slate-900 text-white hover:bg-slate-800"
              disabled={saving}
              data-testid="save-recurring-btn"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
              {isEdit ? 'Save Changes' : 'Start Recurring Gift'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function RecurringGivingManager({ funds = [] }) {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);

  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/recurring-giving`);
      if (res.ok) {
        const data = await res.json();
        setSchedules(data.schedules || []);
      }
    } catch (err) {
      console.error('Failed to fetch recurring schedules:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data) => {
    const res = await fetch(`${API_URL}/portal/recurring-giving`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create');
    }
    toast.success('Recurring gift created!');
    fetchSchedules();
  };

  const handleEdit = async (data) => {
    const res = await fetch(`${API_URL}/portal/recurring-giving/${editingSchedule.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to update');
    }
    toast.success('Recurring gift updated!');
    setEditingSchedule(null);
    fetchSchedules();
  };

  const handlePause = async (id) => {
    const res = await fetch(`${API_URL}/portal/recurring-giving/${id}/pause`, { method: 'PUT' });
    if (res.ok) {
      toast.success('Schedule paused');
      fetchSchedules();
    } else {
      toast.error('Failed to pause schedule');
    }
  };

  const handleResume = async (id) => {
    const res = await fetch(`${API_URL}/portal/recurring-giving/${id}/resume`, { method: 'PUT' });
    if (res.ok) {
      toast.success('Schedule resumed');
      fetchSchedules();
    } else {
      toast.error('Failed to resume schedule');
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this recurring gift?')) return;
    const res = await fetch(`${API_URL}/portal/recurring-giving/${id}`, { method: 'DELETE' });
    if (res.ok) {
      toast.success('Schedule cancelled');
      fetchSchedules();
    } else {
      toast.error('Failed to cancel schedule');
    }
  };

  const activeSchedules = schedules.filter(s => s.status !== 'cancelled');
  const cancelledSchedules = schedules.filter(s => s.status === 'cancelled');

  return (
    <div className="portal-section" data-testid="recurring-giving-manager">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-slate-600" />
          <h3 className="portal-section-title" style={{ margin: 0 }}>Recurring Giving</h3>
        </div>
        <Button
          size="sm"
          className="bg-slate-900 text-white hover:bg-slate-800 text-xs h-8"
          onClick={() => { setEditingSchedule(null); setShowModal(true); }}
          data-testid="new-recurring-btn"
        >
          <Plus className="w-3 h-3 mr-1" /> New Schedule
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        </div>
      ) : activeSchedules.length === 0 && cancelledSchedules.length === 0 ? (
        <div className="text-center py-8" data-testid="no-recurring-schedules">
          <RefreshCw className="w-10 h-10 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No recurring gifts set up yet</p>
          <p className="text-slate-400 text-xs mt-1">Set up automated giving to never miss a gift</p>
        </div>
      ) : (
        <div className="space-y-3">
          {activeSchedules.map((s) => (
            <ScheduleCard
              key={s.id}
              schedule={s}
              funds={funds}
              onEdit={(schedule) => { setEditingSchedule(schedule); setShowModal(true); }}
              onPause={handlePause}
              onResume={handleResume}
              onCancel={handleCancel}
            />
          ))}
          {cancelledSchedules.length > 0 && (
            <>
              <p className="text-xs text-slate-400 pt-2 uppercase tracking-wide font-medium">Cancelled</p>
              {cancelledSchedules.map((s) => (
                <ScheduleCard
                  key={s.id}
                  schedule={s}
                  funds={funds}
                  onEdit={() => {}}
                  onPause={() => {}}
                  onResume={() => {}}
                  onCancel={() => {}}
                />
              ))}
            </>
          )}
        </div>
      )}

      {showModal && (
        <CreateEditModal
          schedule={editingSchedule}
          funds={funds}
          onClose={() => { setShowModal(false); setEditingSchedule(null); }}
          onSave={editingSchedule ? handleEdit : handleCreate}
        />
      )}
    </div>
  );
}
