import { useState, useEffect } from 'react';
import { Target, Pencil, Trash2, Loader2, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

export default function GivingGoalTracker() {
  const [goal, setGoal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [amount, setAmount] = useState('');

  useEffect(() => { fetchGoal(); }, []);

  const fetchGoal = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/giving-goal`);
      if (res.ok) {
        const data = await res.json();
        setGoal(data);
        if (data.has_goal) setAmount(data.target_amount.toString());
      }
    } catch (err) {
      console.error('Failed to fetch goal:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid goal amount');
      return;
    }
    try {
      const res = await fetch(`${API_URL}/portal/giving-goal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_amount: parseFloat(amount) }),
      });
      if (res.ok) {
        toast.success('Giving goal saved!');
        setEditing(false);
        fetchGoal();
      }
    } catch {
      toast.error('Failed to save goal');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Remove your giving goal?')) return;
    try {
      const res = await fetch(`${API_URL}/portal/giving-goal`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Goal removed');
        setAmount('');
        fetchGoal();
      }
    } catch {
      toast.error('Failed to remove goal');
    }
  };

  if (loading) return null;

  const hasGoal = goal?.has_goal;
  const pct = goal?.progress_pct || 0;
  const target = goal?.target_amount || 0;
  const given = goal?.ytd_given || 0;
  const remaining = goal?.remaining || 0;
  const year = goal?.year || new Date().getFullYear();

  // Color gradient based on progress
  const barColor = pct >= 100 ? '#10b981' : pct >= 75 ? '#22c55e' : pct >= 50 ? '#3b82f6' : pct >= 25 ? '#6366f1' : '#8b5cf6';

  return (
    <div className="portal-section" data-testid="giving-goal-tracker">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-slate-600" />
          <h3 className="portal-section-title" style={{ margin: 0 }}>{year} Giving Goal</h3>
        </div>
        {!editing && (
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => setEditing(true)}
              data-testid="edit-goal-btn"
            >
              <Pencil className="w-3 h-3 mr-1" /> {hasGoal ? 'Edit' : 'Set Goal'}
            </Button>
            {hasGoal && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs text-red-500 hover:text-red-700"
                onClick={handleDelete}
                data-testid="delete-goal-btn"
              >
                <Trash2 className="w-3 h-3" />
              </Button>
            )}
          </div>
        )}
      </div>

      {editing ? (
        <div className="flex items-center gap-2" data-testid="goal-edit-form">
          <span className="text-slate-400 font-medium">$</span>
          <input
            type="number"
            min="1"
            step="100"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. 5000"
            data-testid="goal-amount-input"
          />
          <Button size="sm" className="bg-slate-900 text-white hover:bg-slate-800 h-9" onClick={handleSave} data-testid="save-goal-btn">
            Save
          </Button>
          <Button size="sm" variant="outline" className="h-9" onClick={() => setEditing(false)}>
            Cancel
          </Button>
        </div>
      ) : hasGoal ? (
        <div data-testid="goal-progress">
          <div className="flex items-end justify-between mb-2">
            <div>
              <span className="text-2xl font-bold text-slate-900">{formatCurrency(given)}</span>
              <span className="text-sm text-slate-400 ml-1">of {formatCurrency(target)}</span>
            </div>
            <span className="text-sm font-semibold" style={{ color: barColor }}>{pct}%</span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mb-3" data-testid="goal-progress-bar">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{ width: `${Math.min(pct, 100)}%`, background: `linear-gradient(90deg, ${barColor}cc, ${barColor})` }}
            />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>{goal?.donation_count || 0} gifts this year</span>
            {remaining > 0 ? (
              <span>{formatCurrency(remaining)} remaining</span>
            ) : (
              <span className="flex items-center gap-1 text-emerald-600 font-medium">
                <TrendingUp className="w-3 h-3" /> Goal reached!
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-4" data-testid="no-goal-set">
          <p className="text-slate-500 text-sm">No giving goal set for {year}</p>
          <p className="text-slate-400 text-xs mt-1">Set a goal to track your generosity journey</p>
        </div>
      )}
    </div>
  );
}
