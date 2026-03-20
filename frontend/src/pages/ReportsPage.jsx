import { useState, useEffect } from 'react';
import { BarChart3, Users, DollarSign, Calendar, Download, FileText, Baby, Coffee, ShoppingBag, UsersRound, GraduationCap, TrendingUp, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line 
} from 'recharts';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

const COLORS = ['#4f6ef7', '#00c896', '#f5a623', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

const ReportCard = ({ icon: Icon, title, description, onClick, color }) => (
  <button
    className="bg-white border border-slate-200 rounded-xl p-5 text-left hover:border-blue-200 hover:shadow-md transition-all w-full group"
    onClick={onClick}
    data-testid={`report-card-${title.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${color || 'bg-blue-50'}`}>
      <Icon className="w-5 h-5 text-blue-600" />
    </div>
    <h3 className="font-semibold text-slate-900 group-hover:text-blue-700 transition-colors">{title}</h3>
    <p className="text-sm text-slate-500 mt-1">{description}</p>
  </button>
);

export default function ReportsPage() {
  const [activeReport, setActiveReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  const reportTypes = [
    { id: 'executive-summary', title: 'Executive Summary', description: 'Full church health overview', icon: TrendingUp, color: 'bg-indigo-50' },
    { id: 'membership', title: 'Membership', description: 'Member counts by status', icon: Users, color: 'bg-blue-50' },
    { id: 'giving-fund', title: 'Giving by Fund', description: 'Donations grouped by fund', icon: DollarSign, color: 'bg-green-50' },
    { id: 'giving-method', title: 'Giving by Method', description: 'Payment method breakdown', icon: DollarSign, color: 'bg-emerald-50' },
    { id: 'top-donors', title: 'Top Donors', description: 'Highest contributing members', icon: DollarSign, color: 'bg-teal-50' },
    { id: 'attendance', title: 'Attendance', description: 'Weekly service attendance', icon: Calendar, color: 'bg-purple-50' },
    { id: 'kids-history', title: 'Kids Check-In', description: 'Kids check-in/out history', icon: Baby, color: 'bg-pink-50' },
    { id: 'cafe', title: 'Cafe Orders', description: 'Cafe revenue and top items', icon: Coffee, color: 'bg-amber-50' },
    { id: 'merch', title: 'Merch Orders', description: 'Merchandise sales report', icon: ShoppingBag, color: 'bg-orange-50' },
    { id: 'groups', title: 'Groups', description: 'Small group participation', icon: UsersRound, color: 'bg-cyan-50' },
    { id: 'next-steps', title: 'Next Steps', description: 'Membership pathway completion', icon: GraduationCap, color: 'bg-violet-50' },
  ];

  const loadReport = async (reportId) => {
    setActiveReport(reportId);
    setLoading(true);
    try {
      const dateParams = `start_date=${dateRange.start}&end_date=${dateRange.end}`;
      let url;
      switch (reportId) {
        case 'membership': url = `${API_URL}/reports/membership`; break;
        case 'giving-fund': url = `${API_URL}/reports/giving-by-fund?${dateParams}`; break;
        case 'giving-method': url = `${API_URL}/reports/giving-by-method?${dateParams}`; break;
        case 'top-donors': url = `${API_URL}/reports/top-donors?${dateParams}&limit=20`; break;
        case 'attendance': url = `${API_URL}/reports/attendance?${dateParams}`; break;
        case 'kids-history': url = `${API_URL}/reports/kids-history?${dateParams}`; break;
        case 'cafe': url = `${API_URL}/reports/cafe?${dateParams}`; break;
        case 'merch': url = `${API_URL}/reports/merch?${dateParams}`; break;
        case 'groups': url = `${API_URL}/reports/groups`; break;
        case 'next-steps': url = `${API_URL}/reports/next-steps`; break;
        case 'executive-summary': url = `${API_URL}/reports/executive-summary`; break;
        default: return;
      }
      const response = await fetch(url);
      const data = await response.json();
      setReportData(data);
    } catch (error) {
      console.error('Failed to load report:', error);
      toast.error('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (reportId) => {
    setExporting(true);
    try {
      const url = `${API_URL}/reports/${reportId}/export?format=csv&start_date=${dateRange.start}&end_date=${dateRange.end}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${reportId}_report.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
      toast.success('Report exported successfully');
    } catch (error) {
      toast.error('Export failed');
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    if (activeReport) loadReport(activeReport);
  }, [dateRange]);

  const SummaryMetric = ({ label, value, sub }) => (
    <div className="p-4 bg-slate-50 rounded-xl">
      <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-slate-900 mt-1 font-data">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );

  return (
    <div className="space-y-6 animate-fade-in" data-testid="reports-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Generate insights and analytics across all church operations</p>
        </div>
      </div>

      {!activeReport ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" data-testid="reports-grid">
          {reportTypes.map((report) => (
            <ReportCard
              key={report.id}
              icon={report.icon}
              title={report.title}
              description={report.description}
              color={report.color}
              onClick={() => loadReport(report.id)}
            />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <button
              className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 font-medium"
              onClick={() => { setActiveReport(null); setReportData(null); }}
              data-testid="reports-back-btn"
            >
              <ArrowLeft className="w-4 h-4" />
              All Reports
            </button>
            
            <div className="flex items-center gap-3 flex-wrap">
              {!['membership', 'groups', 'next-steps', 'executive-summary'].includes(activeReport) && (
                <>
                  <div className="flex items-center gap-2">
                    <Label className="text-sm text-slate-500">From</Label>
                    <Input type="date" value={dateRange.start} onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })} className="w-40 h-9" data-testid="report-date-start" />
                  </div>
                  <div className="flex items-center gap-2">
                    <Label className="text-sm text-slate-500">To</Label>
                    <Input type="date" value={dateRange.end} onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })} className="w-40 h-9" data-testid="report-date-end" />
                  </div>
                </>
              )}
              <Button variant="outline" size="sm" onClick={() => handleExport(activeReport)} disabled={exporting} data-testid="report-export-csv">
                <Download className="w-4 h-4 mr-2" />
                {exporting ? 'Exporting...' : 'Export CSV'}
              </Button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6" data-testid="report-content">
            <h2 className="text-xl font-semibold text-slate-900 mb-6">
              {reportTypes.find(r => r.id === activeReport)?.title}
            </h2>

            {loading ? (
              <div className="h-64 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <>
                {/* Executive Summary */}
                {activeReport === 'executive-summary' && reportData && (
                  <div className="space-y-6" data-testid="exec-summary">
                    <p className="text-sm text-slate-500">{reportData.period?.month}</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <SummaryMetric label="Total Members" value={reportData.membership?.total?.toLocaleString()} sub={`${reportData.membership?.new_this_month} new this month`} />
                      <SummaryMetric label="Giving This Month" value={formatCurrency(reportData.giving?.total_this_month)} sub={`${reportData.giving?.donation_count} donations`} />
                      <SummaryMetric label="Attendance" value={reportData.attendance?.total_checkins} sub={`${reportData.attendance?.unique_attendees} unique`} />
                      <SummaryMetric label="Kids Check-Ins" value={reportData.kids?.checkins_this_month} />
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <SummaryMetric label="Active Groups" value={reportData.groups?.active_groups} />
                      <SummaryMetric label="Cafe Orders" value={reportData.cafe?.orders_this_month} />
                      <SummaryMetric label="Merch Orders" value={reportData.merch?.orders_this_month} />
                      <SummaryMetric label="Avg Gift" value={formatCurrency(reportData.giving?.avg_gift)} />
                    </div>
                  </div>
                )}

                {/* Membership Report */}
                {activeReport === 'membership' && reportData && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={reportData.by_status} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={2} dataKey="count" nameKey="status" label={({ status, count }) => `${status}: ${count}`}>
                            {reportData.by_status?.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-3">
                      <SummaryMetric label="Total Members" value={reportData.total?.toLocaleString()} />
                      {reportData.by_status?.map((s, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                            <span className="text-slate-600 capitalize">{s.status}</span>
                          </div>
                          <span className="font-semibold font-data">{s.count?.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Attendance Report */}
                {activeReport === 'attendance' && reportData && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                      <SummaryMetric label="Total Services" value={reportData.summary?.total_services} />
                      <SummaryMetric label="Total Check-Ins" value={reportData.summary?.total_checkins} />
                      <SummaryMetric label="Avg per Service" value={reportData.summary?.avg_per_service} />
                    </div>
                    {reportData.weekly?.length > 0 && (
                      <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={reportData.weekly.slice(0, 12).reverse()}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="in_person" fill="#4f6ef7" name="In Person" radius={[4,4,0,0]} />
                            <Bar dataKey="online" fill="#00c896" name="Online" radius={[4,4,0,0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                )}

                {/* Kids History */}
                {activeReport === 'kids-history' && reportData && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <SummaryMetric label="Total Check-Ins" value={reportData.summary?.total_checkins} />
                      <SummaryMetric label="Unique Kids" value={reportData.summary?.unique_kids} />
                      <SummaryMetric label="Checked Out" value={reportData.summary?.checked_out} />
                      <SummaryMetric label="Still Checked In" value={reportData.summary?.still_checked_in} />
                    </div>
                    {reportData.records?.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead><tr className="border-b border-slate-200">
                            <th className="text-left p-3 text-slate-500 font-medium">Child</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Service</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Check-In</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Pickup Code</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Status</th>
                          </tr></thead>
                          <tbody>
                            {reportData.records.slice(0, 50).map((r, i) => (
                              <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                                <td className="p-3 font-medium">{r.child_name || 'Unknown'}</td>
                                <td className="p-3 text-slate-600">{r.service_type || '-'}</td>
                                <td className="p-3 text-slate-600">{r.checked_in_at ? new Date(r.checked_in_at).toLocaleString() : '-'}</td>
                                <td className="p-3 font-mono font-bold text-blue-700">{r.pickup_code || '-'}</td>
                                <td className="p-3">{r.checked_out_at ? <span className="text-green-600 font-medium">Checked Out</span> : <span className="text-amber-600 font-medium">Checked In</span>}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {/* Cafe Report */}
                {activeReport === 'cafe' && reportData && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                      <SummaryMetric label="Total Orders" value={reportData.summary?.total_orders} />
                      <SummaryMetric label="Revenue" value={formatCurrency(reportData.summary?.total_revenue)} />
                      <SummaryMetric label="Avg Order" value={formatCurrency(reportData.summary?.avg_order)} />
                    </div>
                    {reportData.top_items?.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-slate-700 mb-3">Top Items</h3>
                        <div className="space-y-2">
                          {reportData.top_items.map((item, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                              <span className="font-medium">{item.name}</span>
                              <span className="font-data text-slate-600">{item.quantity} sold</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Merch Report */}
                {activeReport === 'merch' && reportData && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <SummaryMetric label="Total Orders" value={reportData.summary?.total_orders} />
                      <SummaryMetric label="Revenue" value={formatCurrency(reportData.summary?.total_revenue)} />
                    </div>
                  </div>
                )}

                {/* Groups Report */}
                {activeReport === 'groups' && reportData && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                      <SummaryMetric label="Total Groups" value={reportData.summary?.total_groups} />
                      <SummaryMetric label="Members in Groups" value={reportData.summary?.total_members_in_groups} />
                      <SummaryMetric label="Avg Group Size" value={reportData.summary?.avg_group_size} />
                    </div>
                    {reportData.groups?.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead><tr className="border-b border-slate-200">
                            <th className="text-left p-3 text-slate-500 font-medium">Group</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Type</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Members</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Leader</th>
                            <th className="text-left p-3 text-slate-500 font-medium">Status</th>
                          </tr></thead>
                          <tbody>
                            {reportData.groups.map((g, i) => (
                              <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                                <td className="p-3 font-medium">{g.name}</td>
                                <td className="p-3 text-slate-600 capitalize">{g.type?.replace('_', ' ')}</td>
                                <td className="p-3 font-data">{g.members}</td>
                                <td className="p-3 text-slate-600">{g.leader || '-'}</td>
                                <td className="p-3 capitalize">{g.status}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {/* Next Steps Report */}
                {activeReport === 'next-steps' && reportData && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                      <SummaryMetric label="Enrolled" value={reportData.summary?.total_enrolled} />
                      <SummaryMetric label="Completed" value={reportData.summary?.completed_membership} />
                      <SummaryMetric label="Completion Rate" value={`${reportData.summary?.completion_rate}%`} />
                    </div>
                  </div>
                )}

                {/* Giving by Fund */}
                {activeReport === 'giving-fund' && reportData && (
                  <div>
                    <div className="h-80 mb-8">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={reportData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="fund_name" tick={{ fontSize: 12 }} />
                          <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                          <Bar dataKey="total" fill="#4f6ef7" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <table className="w-full text-sm">
                      <thead><tr className="border-b border-slate-200">
                        <th className="text-left p-3">Fund</th>
                        <th className="text-right p-3">Total</th>
                        <th className="text-right p-3">Donations</th>
                      </tr></thead>
                      <tbody>
                        {reportData?.map((item, i) => (
                          <tr key={i} className="border-b border-slate-100">
                            <td className="p-3 font-medium">{item.fund_name}</td>
                            <td className="text-right p-3 font-data">{formatCurrency(item.total)}</td>
                            <td className="text-right p-3 font-data">{item.count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Giving by Method */}
                {activeReport === 'giving-method' && reportData && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={reportData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={2} dataKey="total" nameKey="method" label={({ method, percent }) => `${method} ${(percent * 100).toFixed(0)}%`}>
                            {reportData?.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                          </Pie>
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-3">
                      {reportData?.map((item, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                            <span className="text-slate-600 capitalize">{item.method}</span>
                          </div>
                          <div className="text-right">
                            <span className="font-semibold font-data">{formatCurrency(item.total)}</span>
                            <span className="text-slate-400 text-sm ml-2">({item.count})</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Top Donors */}
                {activeReport === 'top-donors' && reportData && (
                  <table className="w-full text-sm">
                    <thead><tr className="border-b border-slate-200">
                      <th className="text-left p-3">Rank</th>
                      <th className="text-left p-3">Donor</th>
                      <th className="text-right p-3">Total Given</th>
                      <th className="text-right p-3"># Gifts</th>
                    </tr></thead>
                    <tbody>
                      {reportData?.map((donor, i) => (
                        <tr key={i} className="border-b border-slate-100">
                          <td className="p-3 font-data text-slate-400">{i + 1}</td>
                          <td className="p-3 font-medium">{donor.name}</td>
                          <td className="text-right p-3 font-data font-semibold">{formatCurrency(donor.total)}</td>
                          <td className="text-right p-3 font-data">{donor.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
