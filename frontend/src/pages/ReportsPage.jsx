import { useState, useEffect } from 'react';
import { BarChart3, Users, DollarSign, Calendar, Download, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { API_URL, formatCurrency, formatDate } from '@/lib/utils';

const COLORS = ['#4f6ef7', '#00c896', '#f5a623', '#8b5cf6', '#ec4899'];

const ReportCard = ({ icon: Icon, title, description, onClick }) => (
  <button
    className="bg-white border border-slate-200 rounded-lg p-5 text-left hover:border-blue-200 hover:shadow-sm transition-all w-full"
    onClick={onClick}
  >
    <Icon className="w-8 h-8 text-blue-500 mb-3" />
    <h3 className="font-semibold text-slate-900">{title}</h3>
    <p className="text-sm text-slate-500 mt-1">{description}</p>
  </button>
);

export default function ReportsPage() {
  const [activeReport, setActiveReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  const reportTypes = [
    { id: 'membership', title: 'Membership Report', description: 'Member counts by status', icon: Users },
    { id: 'giving-fund', title: 'Giving by Fund', description: 'Donations grouped by fund', icon: DollarSign },
    { id: 'giving-method', title: 'Giving by Method', description: 'Payment method breakdown', icon: DollarSign },
    { id: 'top-donors', title: 'Top Donors', description: 'Highest contributing members', icon: DollarSign },
  ];

  const loadReport = async (reportId) => {
    setActiveReport(reportId);
    setLoading(true);
    try {
      let url;
      switch (reportId) {
        case 'membership':
          url = `${API_URL}/reports/membership`;
          break;
        case 'giving-fund':
          url = `${API_URL}/reports/giving-by-fund?start_date=${dateRange.start}&end_date=${dateRange.end}`;
          break;
        case 'giving-method':
          url = `${API_URL}/reports/giving-by-method?start_date=${dateRange.start}&end_date=${dateRange.end}`;
          break;
        case 'top-donors':
          url = `${API_URL}/reports/top-donors?start_date=${dateRange.start}&end_date=${dateRange.end}&limit=20`;
          break;
        default:
          return;
      }
      const response = await fetch(url);
      const data = await response.json();
      setReportData(data);
    } catch (error) {
      console.error('Failed to load report:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeReport) {
      loadReport(activeReport);
    }
  }, [dateRange]);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="reports-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Generate insights and analytics</p>
        </div>
        <Button variant="outline" className="h-9" data-testid="export-all-btn">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {!activeReport ? (
        /* Report Selection */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {reportTypes.map((report) => (
            <ReportCard
              key={report.id}
              icon={report.icon}
              title={report.title}
              description={report.description}
              onClick={() => loadReport(report.id)}
            />
          ))}
        </div>
      ) : (
        /* Report View */
        <div className="space-y-6">
          {/* Back Button & Filters */}
          <div className="flex items-center justify-between">
            <button
              className="text-sm text-blue-600 hover:underline"
              onClick={() => { setActiveReport(null); setReportData(null); }}
            >
              ← Back to Reports
            </button>
            
            {['giving-fund', 'giving-method', 'top-donors'].includes(activeReport) && (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Label className="text-sm">From</Label>
                  <Input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                    className="w-40"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Label className="text-sm">To</Label>
                  <Input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                    className="w-40"
                  />
                </div>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            )}
          </div>

          {/* Report Content */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-6">
              {reportTypes.find(r => r.id === activeReport)?.title}
            </h2>

            {loading ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-pulse text-slate-400">Loading report...</div>
              </div>
            ) : (
              <>
                {/* Membership Report */}
                {activeReport === 'membership' && reportData && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div>
                      <h3 className="font-medium text-slate-700 mb-4">Members by Status</h3>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={reportData.by_status}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={100}
                              paddingAngle={2}
                              dataKey="count"
                              nameKey="status"
                              label={({ status, count }) => `${status}: ${count}`}
                            >
                              {reportData.by_status?.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-700 mb-4">Summary</h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Total Members</span>
                          <span className="text-2xl font-bold font-data">{reportData.total?.toLocaleString()}</span>
                        </div>
                        {reportData.by_status?.map((status, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                              ></div>
                              <span className="text-slate-600 capitalize">{status.status}</span>
                            </div>
                            <span className="font-semibold font-data">{status.count?.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
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
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Fund</th>
                          <th className="text-right">Total</th>
                          <th className="text-right">Donations</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportData?.map((item, idx) => (
                          <tr key={idx}>
                            <td className="font-medium">{item.fund_name}</td>
                            <td className="text-right font-data">{formatCurrency(item.total)}</td>
                            <td className="text-right font-data">{item.count}</td>
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
                          <Pie
                            data={reportData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={2}
                            dataKey="total"
                            nameKey="method"
                            label={({ method, percent }) => `${method} ${(percent * 100).toFixed(0)}%`}
                          >
                            {reportData?.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-3">
                      {reportData?.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                            ></div>
                            <span className="text-slate-600 capitalize">{item.method}</span>
                          </div>
                          <div className="text-right">
                            <span className="font-semibold font-data">{formatCurrency(item.total)}</span>
                            <span className="text-slate-400 text-sm ml-2">({item.count} gifts)</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Top Donors */}
                {activeReport === 'top-donors' && reportData && (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Donor</th>
                        <th className="text-right">Total Given</th>
                        <th className="text-right"># Gifts</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData?.map((donor, idx) => (
                        <tr key={idx}>
                          <td className="font-data text-slate-400">{idx + 1}</td>
                          <td className="font-medium">{donor.name}</td>
                          <td className="text-right font-data font-semibold">{formatCurrency(donor.total)}</td>
                          <td className="text-right font-data">{donor.count}</td>
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
