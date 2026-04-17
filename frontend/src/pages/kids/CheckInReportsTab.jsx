import { UserCheck, MapPin, TrendingUp, Baby } from 'lucide-react';

export function CheckInReportsTab({ trends, firstTimers, formatDate }) {
  return (
    <div className="space-y-4">
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
        <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="report-trend-chart" role="img" aria-label="Daily check-in trend chart">
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
          <div className="space-y-2" role="list" aria-label="Check-ins by room">
            {trends.by_room.map((r, i) => (
              <div key={i} className="flex items-center gap-3" role="listitem">
                <span className="text-sm text-slate-700 w-32 truncate">{r.room}</span>
                <div className="flex-1 bg-slate-100 rounded-full h-5 overflow-hidden" role="progressbar" aria-valuenow={r.count} aria-valuemax={trends.total_checkins}>
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
          <div className="space-y-2" role="list" aria-label="First-time visitors">
            {firstTimers.map((ft, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 bg-emerald-50/50 rounded-lg text-sm" role="listitem">
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
    </div>
  );
}
