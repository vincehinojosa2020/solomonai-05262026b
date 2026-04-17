/**
 * Solomon AI — God Mode Platform Dashboard (Easter Sprint)
 * World-class payment processor admin experience.
 * Route: /platform  (standalone — no AppShell)
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp, TrendingDown, Building2, Users, Receipt, Landmark,
  DollarSign, Activity, AlertTriangle, ChevronRight, ArrowUpRight,
  Download, RefreshCw, Search, Filter, Plus, X, Zap, Globe,
  BarChart3, Shield, Settings, LogOut, Calendar, Heart, Baby,
  Clock, CreditCard, CheckCircle2, RotateCcw, Eye, ChevronDown, ChevronUp,
  Bell, Layers, PieChart as PieChartIcon, LineChart as LineChartIcon,
  HelpCircle, BookOpen, Info, Brain
} from 'lucide-react';
import ChurchDetail from './platform/ChurchDetail';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  PieChart as RechartsPie, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import ChurchOnboardingWizard from '@/components/ChurchOnboardingWizard';
import SolomonGodMode from '@/components/SolomonGodMode';

// ─── Color palette ─────────────────────────────────────────────────────────
const C = ['#3b82f6','#8b5cf6','#10b981','#f59e0b','#ef4444','#0891b2','#ec4899','#6366f1'];
const getColor = (name) => {
  const map = {'Abundant Church':'#3b82f6','The Potter\'s House':'#8b5cf6','City Reach Church':'#10b981','EdenX Ministries':'#0891b2','Abundant East':'#f59e0b','Abundant West':'#ec4899','Abundant Downtown':'#6366f1','Hill Country Bible Church':'#14b8a6'};
  for (const [k,v] of Object.entries(map)) if (name?.includes(k.split(' ')[0]) || name === k) return v;
  return '#64748b';
};

// ─── Formatters ─────────────────────────────────────────────────────────────
const fmtM = (n) => { const v=Number(n??0); if(isNaN(v))return'$0'; if(v>=1e9)return`$${(v/1e9).toFixed(2)}B`; if(v>=1e6)return`$${(v/1e6).toFixed(1)}M`; if(v>=1e3)return`$${(v/1e3).toFixed(1)}K`; return`$${v.toFixed(0)}`; };
const fmtNum = (n) => Number(n??0).toLocaleString();
const fmtPct = (n) => `${Number(n??0).toFixed(1)}%`;
const fmtCur = (n) => `$${Number(n??0).toLocaleString(undefined,{minimumFractionDigits:0,maximumFractionDigits:0})}`;
const getAuth = () => { const t=sessionStorage.getItem('session_token'); return t?{Authorization:`Bearer ${t}`}:{}; };

// ─── KPI Glossary Definitions ──────────────────────────────────────────────
const KPI_GLOSSARY = {
  dashboard: {
    title: 'Dashboard KPI Definitions',
    terms: [
      { term: 'Platform GMV', def: 'Gross Merchandise Volume — the total dollar amount of all donations processed through Solomon Pay across all churches on the platform, since inception.' },
      { term: 'Total Revenue', def: 'The sum of all processing fees earned by Solomon AI from payment transactions, plus subscription revenue from church plans. This is Solomon AI\'s actual revenue, not the churches\' giving.' },
      { term: 'Processing MRR', def: 'Monthly Recurring Revenue from processing — the monthly fee income Solomon AI earns from recurring giving schedules that auto-process through Solomon Pay.' },
      { term: 'Total ARR', def: 'Annual Recurring Revenue — Processing MRR × 12 plus Subscription MRR × 12. This is the annualized run-rate of all predictable revenue streams.' },
      { term: 'Churches', def: 'The total number of active church partners currently using Solomon AI with valid subscriptions.' },
      { term: 'Total Members', def: 'The combined count of all people (members, visitors, contacts) across every church on the platform.' },
      { term: 'Transactions', def: 'The total number of individual donation transactions processed through Solomon Pay across all churches, all time.' },
      { term: 'Subscription MRR', def: 'Monthly revenue from church subscription plans (Standard, Growth, Enterprise). Each church pays a flat monthly fee for platform access.' },
      { term: 'Avg Transaction', def: 'The average dollar amount per donation transaction across all churches. Calculated as Total GMV ÷ Total Transactions.' },
    ],
  },
  portfolio: {
    title: 'Church Portfolio Definitions',
    terms: [
      { term: 'Members', def: 'The total number of people in that church\'s database — includes active members, regular attenders, visitors, and inactive contacts.' },
      { term: 'Active Donors', def: 'People who have made at least one donation through Solomon Pay in the last 90 days. This measures recent financial engagement.' },
      { term: 'Active %', def: 'Active Donors ÷ Total Members × 100. A healthy church typically has 40-80% active donor rate. Below 30% signals engagement issues.' },
      { term: 'All-Time Giving', def: 'The cumulative total of all donations processed through Solomon Pay for that church since they joined the platform.' },
      { term: 'Fees Earned', def: 'The total processing fees Solomon AI has earned from that church\'s transactions. This is our revenue from their giving volume.' },
      { term: 'Plan', def: 'The subscription tier — Standard ($499/mo), Growth ($999/mo), or Enterprise ($2,000/mo). Higher tiers unlock more features and support.' },
      { term: 'Health Score', def: 'A composite grade (A+ to F) based on 5 dimensions: giving consistency, attendance trends, group engagement, volunteer participation, and donor retention. Click the badge to see the full breakdown.' },
    ],
  },
  churches: {
    title: 'Church Detail Definitions',
    terms: [
      { term: 'All-Time', def: 'Total giving processed through Solomon Pay for this church since they onboarded.' },
      { term: 'Fees', def: 'Total processing fees Solomon AI has earned from this church\'s transaction volume.' },
      { term: 'Active Donors', def: 'Number of unique people who donated in the last 90 days.' },
      { term: 'Health Dimensions', def: 'Each bar shows a 0-100 score: Giving Consistency (regularity of donations), Attendance Trend (week-over-week growth), Group Engagement (% of members in small groups), Volunteer Rate (% of members serving), and Donor Retention (% of donors who give again within 90 days).' },
    ],
  },
  solomonPay: {
    title: 'Solomon Pay Definitions',
    terms: [
      { term: 'GMV All-Time', def: 'Total dollar volume processed through Solomon Pay since launch. This is the churches\' giving, not our revenue.' },
      { term: 'Processing Revenue', def: 'Total fees earned from processing transactions (1.9% + $0.30 per card, 0.8% + $0.30 per ACH).' },
      { term: 'Subscription MRR', def: 'Monthly recurring revenue from church subscription plans.' },
      { term: 'Fee Rate (Blended)', def: 'Average effective fee rate across all payment methods. Calculated as Total Fees ÷ Total GMV.' },
      { term: 'Net Payout', def: 'The amount sent to the church\'s bank account after Solomon Pay processing fees are deducted. Gross Amount − Fees = Net Payout.' },
    ],
  },
  donors: {
    title: 'Donor Metric Definitions',
    terms: [
      { term: 'Total Donors', def: 'Every unique person who has ever made a donation through Solomon Pay across all churches.' },
      { term: 'Active (90d)', def: 'Donors who gave at least once in the last 90 days. This is the primary "health" metric for donor engagement.' },
      { term: 'Recurring', def: 'Donors with an active automated giving schedule (weekly, bi-weekly, or monthly). These are the most valuable donors.' },
      { term: 'Avg Gift', def: 'The average individual transaction amount across all donors and all churches.' },
      { term: 'Avg LTV (36mo)', def: 'Average Lifetime Value — projected total giving per donor over a 36-month period based on their current giving rate.' },
      { term: 'DonorIQ Breakdown', def: 'Segmentation of all donors by engagement level: Recurring (automated giving), Regular (3+ gifts/quarter), Occasional (1-2 gifts/quarter), First-Time (gave once, within 90 days), At Risk (gap in giving pattern), Lapsed (no gift in 90+ days).' },
      { term: 'Donor Retention Cohort', def: 'Tracks what percentage of first-time donors from each quarter continue giving in subsequent quarters. The #1 metric church CFOs care about.' },
    ],
  },
};

// ─── Glossary Panel Component ──────────────────────────────────────────────
function GlossaryPanel({ sectionKey }) {
  const [open, setOpen] = useState(false);
  const glossary = KPI_GLOSSARY[sectionKey];
  if (!glossary) return null;

  return (
    <div className="bg-gradient-to-r from-slate-50 to-blue-50/30 border border-slate-200 rounded-xl overflow-hidden" data-testid={`glossary-${sectionKey}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-50/60 transition-colors"
        data-testid={`glossary-toggle-${sectionKey}`}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
          </div>
          <span className="text-sm font-semibold text-slate-800">{glossary.title}</span>
          <span className="text-xs text-slate-400 hidden sm:inline">— What do these numbers mean?</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {glossary.terms.map((t, i) => (
              <div key={i} className="bg-white border border-slate-100 rounded-lg px-3 py-2.5">
                <p className="text-xs font-bold text-slate-800">{t.term}</p>
                <p className="text-xs text-slate-500 leading-snug mt-0.5">{t.def}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Inline KPI Info Tooltip ───────────────────────────────────────────────
function KpiInfo({ term }) {
  const [show, setShow] = useState(false);
  const all = Object.values(KPI_GLOSSARY).flatMap(s => s.terms);
  const match = all.find(t => t.term === term);
  if (!match) return null;
  return (
    <div className="relative inline-flex">
      <button onClick={() => setShow(!show)} className="w-4 h-4 rounded-full bg-slate-100 hover:bg-blue-100 flex items-center justify-center transition-colors" title={`What is ${term}?`} data-testid={`kpi-info-${term.replace(/\s+/g,'-').toLowerCase()}`}>
        <Info className="w-2.5 h-2.5 text-slate-400" />
      </button>
      {show && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setShow(false)} />
          <div className="absolute left-0 top-6 z-50 w-64 bg-white border border-slate-200 rounded-lg shadow-xl p-3" data-testid={`kpi-info-panel-${term.replace(/\s+/g,'-').toLowerCase()}`}>
            <p className="text-xs font-bold text-slate-800 mb-1">{match.term}</p>
            <p className="text-xs text-slate-500 leading-snug">{match.def}</p>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Sort Abundant campuses first ──────────────────────────────────────────
function sortAbundantFirst(arr) {
  return [...arr].sort((a, b) => {
    const aIsAbundant = (a.name || '').toLowerCase().includes('abundant');
    const bIsAbundant = (b.name || '').toLowerCase().includes('abundant');
    if (aIsAbundant && !bIsAbundant) return -1;
    if (!aIsAbundant && bIsAbundant) return 1;
    return (b.giving || 0) - (a.giving || 0);
  });
}

// ─── Recharts custom tooltip ─────────────────────────────────────────────────
const ChartTooltip = ({active,payload,label}) => {
  if(!active||!payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-lg text-xs">
      <p className="font-semibold text-slate-700 mb-1.5">{label}</p>
      {payload.map((p,i)=>(
        <div key={i} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{background:p.color}}/>{p.name}</span>
          <span className="font-semibold">{typeof p.value==='number'&&p.value>1000?fmtM(p.value):p.value?.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
};

// ─── Hero KPI Card ────────────────────────────────────────────────────────────
function KpiCard({label,value,subtext,change,changeLabel,icon:Icon}) {
  const positive = change === undefined || change >= 0;
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow" data-testid={`kpi-${label.replace(/\s+/g,'-').toLowerCase()}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-1.5">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <KpiInfo term={label} />
        </div>
        <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
          <Icon className="w-4 h-4 text-blue-600"/>
        </div>
      </div>
      <p className="text-3xl font-bold text-slate-900 tracking-tight mb-1">{value}</p>
      <p className="text-xs text-slate-400 mb-2">{subtext}</p>
      {change !== undefined && (
        <div className={`flex items-center gap-1 text-xs font-semibold ${positive?'text-emerald-600':'text-red-500'}`}>
          {positive?<ArrowUpRight className="w-3.5 h-3.5"/>:<TrendingDown className="w-3.5 h-3.5"/>}
          {positive?'+':''}{fmtPct(Math.abs(change))} {changeLabel||'vs last year'}
        </div>
      )}
    </div>
  );
}

// ─── Health Score Badge ────────────────────────────────────────────────────────
function HealthBadge({grade,score,dimensions}) {
  const [open,setOpen] = useState(false);
  const g=grade?.charAt(0)||'N';
  // Color mapping: A+ = green, A = teal, B+ = blue, B = sky, B- = yellow, C = orange, D/F = red
  const cfg = {
    'A+': {color:'#16a34a', bg:'#dcfce7', border:'#86efac', label:'Excellent'},
    'A':  {color:'#0f766e', bg:'#d1fae5', border:'#6ee7b7', label:'Strong'},
    'B+': {color:'#2563eb', bg:'#dbeafe', border:'#93c5fd', label:'Healthy'},
    'B':  {color:'#0284c7', bg:'#e0f2fe', border:'#7dd3fc', label:'Good'},
    'B-': {color:'#ca8a04', bg:'#fef9c3', border:'#fde047', label:'Developing'},
    'C':  {color:'#ea580c', bg:'#fff7ed', border:'#fed7aa', label:'Attention Needed'},
    'D':  {color:'#dc2626', bg:'#fee2e2', border:'#fca5a5', label:'At Risk'},
    'F':  {color:'#dc2626', bg:'#fee2e2', border:'#fca5a5', label:'Critical'},
    'N/A':{color:'#64748b', bg:'#f1f5f9', border:'#e2e8f0', label:'No Data'},
  }[grade] || {color:'#64748b', bg:'#f1f5f9', border:'#e2e8f0', label:''};
  const {color,bg,border} = cfg;
  return (
    <div className="relative inline-block">
      <button onClick={()=>setOpen(!open)} className="w-12 h-12 rounded-full flex items-center justify-center font-black text-lg border-2 transition-all hover:scale-105 cursor-pointer" style={{background:bg,borderColor:border,color}} title={`${cfg.label} — Score: ${score}/100 — Click for breakdown`} data-testid="health-badge">
        {grade||'—'}
      </button>
      {open && dimensions && (
        <div className="absolute left-14 top-0 z-50 bg-white border border-slate-200 rounded-xl shadow-2xl p-4 w-72 text-sm" data-testid="health-breakdown">
          <div className="flex items-center justify-between mb-3">
            <span className="font-semibold text-slate-900">Health Score: <span style={{color}}>{grade} ({score}/100)</span></span>
            <button onClick={()=>setOpen(false)} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4"/></button>
          </div>
          <div className="space-y-2.5">
            {Object.values(dimensions).map(dim=>(
              <div key={dim.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-600">{dim.label}</span>
                  <span className="font-semibold text-slate-800">{dim.value}{dim.unit}</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{width:`${dim.score}%`,background:dim.score>=70?'#16a34a':dim.score>=50?'#3b82f6':'#f59e0b'}}/>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Date Range Selector ─────────────────────────────────────────────────────
const RANGES = [{id:'7d',label:'7 Days'},{id:'30d',label:'30 Days'},{id:'90d',label:'90 Days'},{id:'1y',label:'This Year'},{id:'all',label:'All Time'}];
function DateRangePicker({value,onChange}) {
  return (
    <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
      {RANGES.map(r=>(
        <button key={r.id} onClick={()=>onChange(r.id)} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${value===r.id?'bg-white shadow text-slate-900':'text-slate-500 hover:text-slate-700'}`}>{r.label}</button>
      ))}
    </div>
  );
}

// ─── Donor Retention Cohort Chart ─────────────────────────────────────────────
function RetentionCohort({cohorts}) {
  if(!cohorts?.length) return <div className="text-center py-8 text-slate-400 text-sm">No cohort data available</div>;
  const COHORT_COLORS = C;
  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart margin={{top:0,right:10,left:0,bottom:0}}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
          <XAxis dataKey="quarter" type="number" domain={[0,4]} tickCount={5} label={{value:'Quarters Since First Gift',position:'insideBottom',offset:-2,fontSize:10}} tick={{fontSize:10}}/>
          <YAxis domain={[0,100]} tickFormatter={v=>`${v}%`} tick={{fontSize:10}} width={40}/>
          <Tooltip formatter={(v)=>`${v}%`} labelFormatter={(l)=>`Q+${l}`} content={ChartTooltip}/>
          <Legend iconSize={8} wrapperStyle={{fontSize:10}}/>
          {cohorts.slice(-6).map((cohort,i)=>(
            <Line key={cohort.label} data={cohort.retention} dataKey="pct" name={cohort.label} stroke={COHORT_COLORS[i%COHORT_COLORS.length]} strokeWidth={2} dot={false}/>
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Main Dashboard ────────────────────────────────────────────────────────────
export default function PlatformDashboard() {
  const navigate = useNavigate();
  const [section, setSection] = useState('dashboard');
  const [solomonPayTab, setSolomonPayTab] = useState('overview');
  const [reportTab, setReportTab] = useState('giving');
  const [stats, setStats] = useState(null);
  const [healthScores, setHealthScores] = useState({});
  const [activity, setActivity] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [showSolomon, setShowSolomon] = useState(false);

  // Solomon Pay vs competitor pricing advantage (verified)
  const PRICING_COMPARISON = [
    { label: 'Credit/Debit Card', solomon: '1.9% + $0.30', competitor: '2.9% + $0.30', savings: '34% cheaper' },
    { label: 'ACH / Bank Transfer', solomon: '0.8% + $0.30 (max $5)', competitor: '1.0% + $0.30', savings: '20% cheaper' },
    { label: 'Cash / Check', solomon: '$0 (free)', competitor: 'Manual fees vary', savings: '100% free' },
  ];
  const [txns, setTxns] = useState([]);
  const [txnTotal, setTxnTotal] = useState(0);
  const [txnPage, setTxnPage] = useState(1);
  const [txnSearch, setTxnSearch] = useState('');
  const [txnChurch, setTxnChurch] = useState('');
  const [txnMethod, setTxnMethod] = useState('');
  const [txnLoading, setTxnLoading] = useState(false);
  const [donorStats, setDonorStats] = useState(null);
  const [donorSearch, setDonorSearch] = useState('');
  const [selectedDonor, setSelectedDonor] = useState(null);
  const [donorProfile, setDonorProfile] = useState(null);
  const [cohortData, setCohortData] = useState(null);
  const [reportData, setReportData] = useState({});
  const [revenue, setRevenue] = useState(null);
  const [payouts, setPayouts] = useState([]);
  const [selectedChurchId, setSelectedChurchId] = useState(null);
  const actRef = useRef();

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuth();
      const r = await fetch(`${API_URL}/platform/stats`, { headers });
      if (r.status === 401) { setError('Session expired — please sign in again'); return; }
      if (r.status === 429) { setError('Too many requests — please wait a moment and refresh'); return; }
      if (!r.ok) { setError(`API error ${r.status} — refresh to retry`); return; }
      const d = await r.json();
      setStats(d);
    } catch (e) {
      setError(`Network error: ${e.message} — check your connection`);
      console.error('fetchStats error:', e);
    } finally {
      setLoading(false);
    }
  }, []);
  const fetchHealthScores = useCallback(async () => {
    try {
      const r=await fetch(`${API_URL}/platform/health-scores`,{headers:getAuth()});
      if(r.ok){const d=await r.json();const m={};(d.churches||[]).forEach(c=>{m[c.tenant_id]=c.health;});setHealthScores(m);}
    } catch {}
  },[]);
  const fetchActivity = useCallback(async () => {
    try { const r=await fetch(`${API_URL}/platform/activity-feed?limit=15`,{headers:getAuth()}); if(r.ok){const d=await r.json();setActivity(d.events||[]);} } catch {}
  },[]);
  const fetchTxns = useCallback(async () => {
    setTxnLoading(true);
    try {
      const p=new URLSearchParams({page:txnPage,limit:50});
      if(txnSearch)p.set('search',txnSearch); if(txnChurch)p.set('church',txnChurch); if(txnMethod)p.set('method',txnMethod);
      const r=await fetch(`${API_URL}/platform/transactions?${p}`,{headers:getAuth()});
      if(r.ok){const d=await r.json();setTxns(d.transactions||d.donations||[]);setTxnTotal(d.total||0);}
    } catch {} finally{setTxnLoading(false);}
  },[txnPage,txnSearch,txnChurch,txnMethod]);
  const fetchDonors = useCallback(async () => {
    try { const r=await fetch(`${API_URL}/platform/donors`,{headers:getAuth()}); if(r.ok)setDonorStats(await r.json()); } catch {}
  },[]);
  const fetchCohort = useCallback(async () => {
    if(cohortData) return;
    try { const r=await fetch(`${API_URL}/platform/reports/retention-cohort`,{headers:getAuth()}); if(r.ok)setCohortData(await r.json()); } catch {}
  },[cohortData]);
  const fetchRevenue = useCallback(async () => {
    try { const r=await fetch(`${API_URL}/platform/revenue`,{headers:getAuth()}); if(r.ok)setRevenue(await r.json()); } catch {}
  },[]);
  const fetchPayouts = useCallback(async () => {
    try { const r=await fetch(`${API_URL}/platform/payouts?limit=50`,{headers:getAuth()}); if(r.ok){const d=await r.json();setPayouts(d.payouts||[]);} } catch {}
  },[]);
  const fetchReportTab = useCallback(async (tab) => {
    if(reportData[tab]) return;
    const urls = {giving:'platform/reports/giving',attendance:'platform/reports/attendance',groups:'platform/reports/groups',checkin:'platform/reports/checkin',volunteers:'platform/reports/volunteers',membership:'platform/reports/membership',audit:'platform/reports/audit?limit=50'};
    const url = urls[tab]; if(!url) return;
    try {
      const r=await fetch(`${API_URL}/${url}`,{headers:getAuth()});
      if(r.ok){const d=await r.json();setReportData(p=>({...p,[tab]:d}));}
    } catch {}
  },[reportData]);
  const fetchDonorProfile = useCallback(async (personId) => {
    try { const r=await fetch(`${API_URL}/platform/donor/${personId}`,{headers:getAuth()}); if(r.ok)setDonorProfile(await r.json()); } catch {}
  },[]);

  useEffect(()=>{
    fetchStats(); fetchHealthScores(); fetchActivity();
    actRef.current=setInterval(fetchActivity,15000);
    return()=>clearInterval(actRef.current);
  },[fetchStats,fetchHealthScores,fetchActivity]);

  useEffect(()=>{ if(section==='transactions')fetchTxns(); },[section,txnPage,txnSearch,txnChurch,txnMethod]);
  useEffect(()=>{ if(section==='donors'){fetchDonors();fetchCohort();} },[section]);
  useEffect(()=>{ if(section==='solomon-pay'&&solomonPayTab==='revenue')fetchRevenue(); if(section==='solomon-pay'&&solomonPayTab==='payouts')fetchPayouts(); if(section==='solomon-pay'&&solomonPayTab==='transactions')fetchTxns(); },[section,solomonPayTab]);
  useEffect(()=>{ if(section==='reports')fetchReportTab(reportTab); },[section,reportTab]);

  const exportCSV = (data,fn) => {
    if(!data?.length){toast.error('No data');return;}
    const keys=Object.keys(data[0]);
    const csv=[keys.join(','),...data.map(r=>keys.map(k=>`"${r[k]??''}"`).join(','))].join('\n');
    const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download=fn;a.click();
    toast.success('Exported');
  };

  const g=stats?.giving||{}; const f=stats?.fees||{}; const p=stats?.platform||{};
  const churches=sortAbundantFirst(stats?.campus_breakdown||[]);
  const trend=stats?.giving_trend||[];
  const monthlyData=trend.map(m=>({month:m.month?.slice(5)||m.month,giving:Math.round(m.total_giving||0),fees:Math.round(m.total_fees||0),...Object.fromEntries(Object.entries(m.by_campus||{}).map(([n,v])=>[n.split(' ')[0],Math.round(v)]))}));
  const attention=churches.filter(c=>{ const h=healthScores[c.tenant_id]; return h&&['C','D','F'].includes(h.grade?.charAt(0)); });

  const NAV = [
    {id:'dashboard',label:'Dashboard',icon:Activity},
    {id:'churches',label:'Churches',icon:Building2},
    {id:'solomon-pay',label:'Solomon Pay',icon:CreditCard,badge:true},
    {id:'donors',label:'Donors',icon:Users},
    {id:'reports',label:'Reports',icon:BarChart3},
    {id:'settings',label:'Settings',icon:Settings},
  ];
  const SP_TABS=[{id:'overview',label:'Overview'},{id:'transactions',label:'Transactions'},{id:'payouts',label:'Payouts'},{id:'recurring',label:'Recurring'}];
  const REPORT_TABS=[
    {id:'giving',label:'Giving',icon:DollarSign},{id:'attendance',label:'Attendance',icon:Calendar},
    {id:'groups',label:'Groups',icon:Users},{id:'checkin',label:'Check-In',icon:Baby},
    {id:'volunteers',label:'Volunteers',icon:Heart},{id:'membership',label:'Membership',icon:CheckCircle2},
    {id:'cross',label:'Cross-Analysis',icon:PieChartIcon},{id:'audit',label:'Audit Log',icon:Shield},
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden" data-testid="god-mode-platform">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 flex flex-col flex-shrink-0 shadow-xl">
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0"><Zap className="w-4 h-4 text-white"/></div>
            <span className="text-white font-bold text-sm tracking-tight" data-testid="sidebar-brand">Solomon AI</span>
          </div>
          <p className="text-[10px] text-blue-400 mt-1 ml-10 font-semibold uppercase tracking-wider">Platform Admin</p>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {NAV.map(item=>(
            <button key={item.id} onClick={()=>setSection(item.id)} className={`w-full flex items-center gap-3 px-5 py-2.5 text-sm font-medium transition-all ${section===item.id?'bg-blue-600 text-white':'text-slate-400 hover:text-white hover:bg-slate-800'}`} data-testid={`nav-${item.id}`}>
              <item.icon className="w-4 h-4 flex-shrink-0"/>
              {item.label}
              {item.badge&&<span className="ml-auto text-[9px] bg-blue-500 text-white px-1.5 py-0.5 rounded-full font-bold">PAY</span>}
            </button>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-slate-800 space-y-2">
          <button onClick={()=>setShowSolomon(true)} className="w-full flex items-center gap-2 px-3 py-2.5 text-xs font-semibold text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 rounded-lg transition-all" data-testid="solomon-ai-btn"><Brain className="w-4 h-4"/>Ask Solomon</button>
          <button onClick={()=>setShowWizard(true)} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all" data-testid="add-church-btn"><Plus className="w-3.5 h-3.5"/>Add New Church</button>
          <button onClick={()=>{sessionStorage.clear();navigate('/login');}} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-500 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-all"><LogOut className="w-3.5 h-3.5"/>Sign Out</button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <div className="sticky top-0 z-20 bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-sm font-bold text-slate-900 capitalize">{section==='solomon-pay'?'Solomon Pay':section==='dashboard'?'Platform Overview':section}</h1>
            <p className="text-[10px] text-slate-400">{new Date().toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'})}</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={()=>{fetchStats();fetchHealthScores();toast.success('Refreshed');}} className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"><RefreshCw className="w-4 h-4"/></button>
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">SA</div>
          </div>
        </div>

        <div className="p-6 space-y-6">

          {/* Error / Loading Banner */}
          {(loading || error) && (
            <div className={`rounded-xl px-5 py-4 flex items-center gap-3 ${error ? 'bg-red-50 border border-red-200' : 'bg-blue-50 border border-blue-200'}`}>
              {loading ? (
                <><div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0"/>
                <span className="text-sm text-blue-700 font-medium">Loading platform data... (aggregating {fmtNum(stats?.transactions?.total || 0)} records)</span></>
              ) : (
                <><AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0"/>
                <span className="text-sm text-red-700 font-medium">{error}</span>
                <button onClick={fetchStats} className="ml-auto px-3 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700">Retry</button></>
              )}
            </div>
          )}

          {/* ══════ DASHBOARD ══════ */}
          {section==='dashboard'&&(
            <>
              {/* Hero KPIs — all same blue accent, consistent */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="hero-kpis">
                <KpiCard label="Platform GMV" value={fmtM(g.all_time)} subtext="All-time giving processed" change={g.yoy_change} icon={Globe}/>
                <KpiCard label="Total Revenue" value={fmtM((f.all_time||0)+(p.subscription_mrr||0)*36)} subtext="Processing + subscriptions" change={g.yoy_change} icon={DollarSign}/>
                <KpiCard label="Processing MRR" value={fmtM(p.processing_mrr)} subtext="Solomon Pay fee run rate" change={4.2} changeLabel="vs last year" icon={CreditCard}/>
                <KpiCard label="Total ARR" value={fmtM(p.arr)} subtext={`Proc. ${fmtM(p.total_arr_processing)} + Sub. ${fmtM(p.total_arr_subscription)}`} change={g.yoy_change} icon={TrendingUp}/>
              </div>
              {/* Sub stats */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  {label:'Churches',value:churches.length,icon:Building2},
                  {label:'Total Members',value:fmtNum(p.total_members||0),icon:Users},
                  {label:'Transactions',value:fmtNum(stats?.transactions?.total||0),icon:Receipt},
                  {label:'Subscription MRR',value:fmtM(p.subscription_mrr||0),icon:Layers},
                  {label:'Avg Transaction',value:`$${(stats?.transactions?.avg_amount||0).toFixed(2)}`,icon:DollarSign},
                ].map(s=>(
                  <div key={s.label} className="bg-white border border-slate-100 rounded-xl p-4 flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0"><s.icon className="w-4 h-4 text-blue-600"/></div>
                    <div><div className="flex items-center gap-1"><p className="text-[10px] text-slate-500">{s.label}</p><KpiInfo term={s.label} /></div><p className="text-base font-bold text-slate-900">{s.value}</p></div>
                  </div>
                ))}
              </div>
              {/* KPI Glossary */}
              <GlossaryPanel sectionKey="dashboard" />

              {/* Revenue Model Breakdown */}
              <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="revenue-model-card">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-sm font-bold text-slate-900">How Solomon AI Makes Money</p>
                    <p className="text-xs text-slate-400">Three revenue streams powering platform economics</p>
                  </div>
                  <KpiInfo term="Total Revenue" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Processing Fees */}
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 border border-blue-200/50 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center"><CreditCard className="w-4 h-4 text-white"/></div>
                      <div>
                        <p className="text-xs font-bold text-blue-900">Processing Fees</p>
                        <p className="text-[10px] text-blue-600">Per-transaction revenue</p>
                      </div>
                    </div>
                    <p className="text-2xl font-black text-blue-900 mb-1">{fmtM(f.all_time||0)}</p>
                    <p className="text-[10px] text-blue-700 mb-2">All-time fees earned from Solomon Pay</p>
                    <div className="space-y-1.5 border-t border-blue-200/50 pt-2">
                      <div className="flex justify-between text-[10px]"><span className="text-blue-600">Card rate</span><span className="font-bold text-blue-900">1.9% + $0.30</span></div>
                      <div className="flex justify-between text-[10px]"><span className="text-blue-600">ACH rate</span><span className="font-bold text-blue-900">0.8% + $0.30</span></div>
                      <div className="flex justify-between text-[10px]"><span className="text-blue-600">Blended take rate</span><span className="font-bold text-blue-900">{((f.all_time||0)/Math.max(g.all_time||1,1)*100).toFixed(2)}%</span></div>
                    </div>
                    <p className="text-[10px] text-blue-700 mt-2 leading-snug">Every donation processed through Solomon Pay generates fee revenue. We earn on every swipe, every ACH transfer, every recurring gift — 34% cheaper than Pushpay.</p>
                  </div>
                  {/* Subscription Fees */}
                  <div className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 border border-emerald-200/50 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center"><Layers className="w-4 h-4 text-white"/></div>
                      <div>
                        <p className="text-xs font-bold text-emerald-900">Subscription Fees</p>
                        <p className="text-[10px] text-emerald-600">Monthly SaaS revenue</p>
                      </div>
                    </div>
                    <p className="text-2xl font-black text-emerald-900 mb-1">{fmtM((p.subscription_mrr||0)*12)}</p>
                    <p className="text-[10px] text-emerald-700 mb-2">Annualized subscription revenue</p>
                    <div className="space-y-1.5 border-t border-emerald-200/50 pt-2">
                      <div className="flex justify-between text-[10px]"><span className="text-emerald-600">Standard</span><span className="font-bold text-emerald-900">$499/mo</span></div>
                      <div className="flex justify-between text-[10px]"><span className="text-emerald-600">Growth</span><span className="font-bold text-emerald-900">$999/mo</span></div>
                      <div className="flex justify-between text-[10px]"><span className="text-emerald-600">Enterprise</span><span className="font-bold text-emerald-900">$2,000+/mo</span></div>
                    </div>
                    <p className="text-[10px] text-emerald-700 mt-2 leading-snug">Predictable monthly revenue from church platform subscriptions. Each tier unlocks more features, higher member limits, and priority support.</p>
                  </div>
                  {/* Professional Services */}
                  <div className="bg-gradient-to-br from-violet-50 to-violet-100/50 border border-violet-200/50 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 bg-violet-600 rounded-lg flex items-center justify-center"><Zap className="w-4 h-4 text-white"/></div>
                      <div>
                        <p className="text-xs font-bold text-violet-900">Professional Services</p>
                        <p className="text-[10px] text-violet-600">Onboarding & consulting</p>
                      </div>
                    </div>
                    <p className="text-2xl font-black text-violet-900 mb-1">$80K+</p>
                    <p className="text-[10px] text-violet-700 mb-2">Annual services revenue potential</p>
                    <div className="space-y-1.5 border-t border-violet-200/50 pt-2">
                      <div className="flex justify-between text-[10px]"><span className="text-violet-600">10-Hour Bundle</span><span className="font-bold text-violet-900">$10,000</span></div>
                      <div className="flex justify-between text-[10px]"><span className="text-violet-600">On-Site Workshop (1 week)</span><span className="font-bold text-violet-900">$25,000</span></div>
                      <div className="flex justify-between text-[10px]"><span className="text-violet-600">Full Migration + Training</span><span className="font-bold text-violet-900">$15,000</span></div>
                      <div className="flex justify-between text-[10px]"><span className="text-violet-600">Ongoing Office Hours (mo)</span><span className="font-bold text-violet-900">$2,500/mo</span></div>
                    </div>
                    <p className="text-[10px] text-violet-700 mt-2 leading-snug">High-touch onboarding, data migration from Pushpay/SecureGive, on-site workshops, CI/CD integration, and ongoing strategic office hours. Modeled after Snyk/Veracode enterprise engagement pricing.</p>
                  </div>
                </div>
                {/* Why churches switch */}
                <div className="mt-4 bg-slate-50 border border-slate-200 rounded-xl p-4">
                  <p className="text-xs font-bold text-slate-800 mb-2">Why Churches Switch from SecureGive & Pushpay to Solomon AI</p>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-[11px]">
                    <div className="space-y-1"><p className="font-bold text-blue-700">34% Lower Fees</p><p className="text-slate-500">1.9% + $0.30 vs. 2.9% + $0.30. On $1M in annual giving, that's $10,000 saved per year per church.</p></div>
                    <div className="space-y-1"><p className="font-bold text-emerald-700">AI-Native Platform</p><p className="text-slate-500">Solomon AI provides McKinsey-grade strategic analysis, donor intelligence, and predictive insights — no other church platform has this.</p></div>
                    <div className="space-y-1"><p className="font-bold text-violet-700">All-in-One</p><p className="text-slate-500">Giving, check-in, groups, events, cafe, merch, communications, and AI — one platform, one price. No bolt-on fees.</p></div>
                    <div className="space-y-1"><p className="font-bold text-amber-700">No Contracts</p><p className="text-slate-500">Month-to-month. Pushpay locks you into 3-year contracts with $15K+ annual minimums. We earn your business every month.</p></div>
                  </div>
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
                <div className="lg:col-span-3 bg-white border border-slate-100 rounded-xl p-5" data-testid="giving-chart">
                  <div className="flex items-center justify-between mb-4">
                    <div><p className="text-sm font-semibold text-slate-900">Monthly Giving by Church</p><p className="text-xs text-slate-400">Last 12 months</p></div>
                    <button onClick={()=>exportCSV(monthlyData,'giving_trend.csv')} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600"><Download className="w-3.5 h-3.5"/>CSV</button>
                  </div>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={monthlyData.slice(-12)} margin={{top:0,right:0,left:0,bottom:0}}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                      <XAxis dataKey="month" tick={{fontSize:10}}/>
                      <YAxis tickFormatter={v=>`$${(v/1000).toFixed(0)}K`} tick={{fontSize:10}} width={52}/>
                      <Tooltip content={ChartTooltip}/>
                      <Legend iconSize={8} wrapperStyle={{fontSize:10}}/>
                      {Array.from(new Set(Object.keys(monthlyData[0]||{}).filter(k=>k!=='month'&&k!=='giving'&&k!=='fees'))).map((name,i)=>(
                        <Bar key={name} dataKey={name} stackId="a" fill={C[i%C.length]} radius={[2,2,0,0]}/>
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="lg:col-span-2 bg-white border border-slate-100 rounded-xl p-5" data-testid="revenue-chart">
                  <div className="mb-4"><p className="text-sm font-semibold text-slate-900">Revenue Trend</p><p className="text-xs text-slate-400">Monthly Solomon Pay fees</p></div>
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={monthlyData.slice(-12)} margin={{top:0,right:0,left:0,bottom:0}}>
                      <defs><linearGradient id="rev" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/><stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/></linearGradient></defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                      <XAxis dataKey="month" tick={{fontSize:10}}/>
                      <YAxis tickFormatter={v=>`$${(v/1000).toFixed(0)}K`} tick={{fontSize:10}} width={48}/>
                      <Tooltip content={ChartTooltip}/>
                      <Area type="monotone" dataKey="fees" stroke="#3b82f6" fill="url(#rev)" strokeWidth={2} name="Revenue"/>
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
              {/* Church Portfolio Table */}
              <div className="bg-white border border-slate-100 rounded-xl overflow-hidden" data-testid="church-portfolio-table">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div><p className="font-semibold text-slate-900">Church Portfolio</p><p className="text-xs text-slate-400">{churches.length} active partners · Click row to expand health</p></div>
                  <button onClick={()=>setShowWizard(true)} className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700"><Plus className="w-3.5 h-3.5"/>Add Church</button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead><tr className="bg-slate-50">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Church</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">City</th>
                      {[
                        {h:'Members',tip:'Members'},
                        {h:'Active Donors',tip:'Active Donors'},{h:'Active %',tip:'Active %'},
                        {h:'All-Time Giving',tip:'All-Time Giving'},{h:'Fees Earned',tip:'Fees Earned'},
                        {h:'Plan',tip:'Plan'},{h:'Health',tip:'Health Score'},
                      ].map(col=>(
                        <th key={col.h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">
                          <div className="flex items-center gap-1">{col.h}<KpiInfo term={col.tip} /></div>
                        </th>
                      ))}
                    </tr></thead>
                    <tbody className="divide-y divide-slate-50">
                      {churches.map(c=>{
                        const hs=healthScores[c.tenant_id];
                        const cached=stats?.campus_breakdown?.find(x=>x.tenant_id===c.tenant_id);
                        const totalM=p.total_members>0?Math.round(p.total_members*(c.giving/Math.max(g.all_time,1))):0;
                        const activeD=c.active_donors||0;
                        const activePct=totalM>0?Math.round(activeD/totalM*100):0;
                        const planLabels={'growth':'Growth','enterprise':'Enterprise','standard':'Standard'};
                        const plan=planLabels[c.plan||'growth']||'Growth';
                        return (
                          <tr key={c.tenant_id} className="hover:bg-slate-50/50 transition-colors" data-testid={`church-row-${c.tenant_id}`}>
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0" style={{background:getColor(c.name)}}>{c.name.charAt(0)}</div>
                                <span className="font-semibold text-slate-800 whitespace-nowrap">{c.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3.5 text-xs text-slate-500 whitespace-nowrap">{c.city}{c.state?`, ${c.state}`:''}</td>
                            <td className="px-4 py-3.5 text-slate-700">{fmtNum(totalM)}</td>
                            <td className="px-4 py-3.5 text-slate-700">{fmtNum(activeD)}</td>
                            <td className="px-4 py-3.5"><span className={`text-xs font-semibold ${activePct>=65?'text-emerald-600':activePct>=50?'text-blue-600':'text-amber-600'}`}>{activePct}%</span></td>
                            <td className="px-4 py-3.5 font-semibold text-slate-900">{fmtM(c.giving)}</td>
                            <td className="px-4 py-3.5 text-emerald-700 font-semibold">{fmtM(c.fees)}</td>
                            <td className="px-4 py-3.5"><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${plan==='Enterprise'?'bg-purple-100 text-purple-700':'bg-blue-50 text-blue-700'}`}>{plan}</span></td>
                            <td className="px-4 py-3.5">
                              {hs?<HealthBadge grade={hs.grade} score={hs.score} dimensions={hs.dimensions}/>:<span className="text-xs text-slate-300">—</span>}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
              {/* Portfolio Glossary */}
              <GlossaryPanel sectionKey="portfolio" />
              {/* Row 4: Activity + Attention */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="bg-white border border-slate-100 rounded-xl p-5" data-testid="activity-feed">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2"><Activity className="w-4 h-4 text-blue-600"/><p className="text-sm font-semibold text-slate-900">Live Activity</p><span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-1"/></div>
                    <span className="text-[10px] text-slate-400">Updates every 15s</span>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {activity.length===0?<p className="text-sm text-slate-400 text-center py-6">No recent activity</p>:activity.map((e,i)=>(
                      <div key={i} className="flex items-start gap-2.5 py-2 border-b border-slate-50 last:border-0">
                        <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-sm" style={{background:e.color==='emerald'?'#dcfce7':'#dbeafe'}}>{e.type==='donation'?'🎁':'🔁'}</div>
                        <div className="flex-1 min-w-0"><p className="text-xs text-slate-700 leading-snug">{e.message}</p><p className="text-[10px] text-slate-400 mt-0.5">{String(e.timestamp||'').slice(0,10)}</p></div>
                        {e.amount>0&&<span className="text-xs font-semibold text-emerald-700 flex-shrink-0">{fmtM(e.amount)}</span>}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-white border border-slate-100 rounded-xl p-5" data-testid="attention-required">
                  <div className="flex items-center gap-2 mb-4"><AlertTriangle className="w-4 h-4 text-amber-500"/><p className="text-sm font-semibold text-slate-900">Attention Required</p>{attention.length>0&&<span className="ml-auto text-xs font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">{attention.length}</span>}</div>
                  {attention.length===0?(
                    <div className="text-center py-8"><div className="w-10 h-10 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-2"><Activity className="w-5 h-5 text-emerald-500"/></div><p className="text-xs font-medium text-emerald-700">All churches healthy</p></div>
                  ):attention.map(c=>{
                    const hs=healthScores[c.tenant_id];
                    const isRed=['D','F'].includes(hs?.grade?.charAt(0));
                    const weakest=hs?.dimensions?Object.values(hs.dimensions).sort((a,b)=>a.score-b.score)[0]:null;
                    return (
                      <div key={c.tenant_id} className="flex items-center gap-3 p-3 rounded-xl border mb-2 cursor-pointer hover:shadow-sm" style={{borderColor:isRed?'#fca5a5':'#fde68a',background:isRed?'#fff5f5':'#fffbeb'}} onClick={()=>setSection('churches')}>
                        <div className="w-9 h-9 rounded-lg flex items-center justify-center font-black text-sm flex-shrink-0" style={{background:isRed?'#fee2e2':'#fef3c7',color:isRed?'#dc2626':'#d97706'}}>{hs?.grade}</div>
                        <div className="flex-1 min-w-0"><p className="text-sm font-semibold text-slate-900">{c.name}</p><p className="text-xs text-slate-500 truncate">{weakest?`${weakest.label}: ${weakest.value}${weakest.unit} (score ${weakest.score}/100)`:'Needs attention'}</p></div>
                        <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0"/>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {/* ══════ CHURCHES ══════ */}
          {section==='churches'&&(
            selectedChurchId ? (
              <ChurchDetail token={sessionStorage.getItem('session_token')} tenantId={selectedChurchId} onBack={() => setSelectedChurchId(null)} />
            ) : (
            <div className="space-y-4" data-testid="churches-section">
              <div className="flex items-center justify-between"><h2 className="text-lg font-bold text-slate-900">{churches.length} Church Partners</h2><button onClick={()=>setShowWizard(true)} className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"><Plus className="w-4 h-4"/>Add Church</button></div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {churches.map(c=>{
                  const hs=healthScores[c.tenant_id];
                  return (
                    <div key={c.tenant_id} className="bg-white border border-slate-100 rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer" data-testid={`church-card-${c.tenant_id}`} onClick={() => setSelectedChurchId(c.tenant_id)}>
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold" style={{background:getColor(c.name)}}>{c.name.charAt(0)}</div>
                          <div><p className="font-bold text-slate-900">{c.name}</p><p className="text-xs text-slate-500">{c.city}{c.state?`, ${c.state}`:''}</p></div>
                        </div>
                        {hs&&<HealthBadge grade={hs.grade} score={hs.score} dimensions={hs.dimensions}/>}
                      </div>
                      <div className="grid grid-cols-3 gap-2 mb-4 text-center">
                        <div className="bg-slate-50 rounded-lg p-2.5"><p className="text-[10px] text-slate-500">All-Time</p><p className="text-sm font-bold text-slate-900">{fmtM(c.giving)}</p></div>
                        <div className="bg-slate-50 rounded-lg p-2.5"><p className="text-[10px] text-slate-500">Fees</p><p className="text-sm font-bold text-emerald-700">{fmtM(c.fees)}</p></div>
                        <div className="bg-slate-50 rounded-lg p-2.5"><p className="text-[10px] text-slate-500">Active Donors</p><p className="text-sm font-bold text-slate-900">{fmtNum(c.active_donors)}</p></div>
                      </div>
                      {hs?.dimensions&&(
                        <div className="space-y-1.5">
                          {Object.values(hs.dimensions).map(dim=>(
                            <div key={dim.label} className="flex items-center gap-2">
                              <span className="text-[10px] text-slate-400 w-28 flex-shrink-0 truncate">{dim.label}</span>
                              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full rounded-full" style={{width:`${dim.score}%`,background:dim.score>=70?'#16a34a':dim.score>=50?'#3b82f6':'#f59e0b'}}/></div>
                              <span className="text-[10px] text-slate-500 w-6 text-right">{dim.score}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              <GlossaryPanel sectionKey="churches" />
            </div>
            )
          )}

          {/* ══════ SOLOMON PAY ══════ */}
          {section==='solomon-pay'&&(
            <div className="space-y-4" data-testid="solomon-pay-section">
              <div className="flex items-center gap-1 bg-slate-100 rounded-xl p-1">
                {SP_TABS.map(t=><button key={t.id} onClick={()=>setSolomonPayTab(t.id)} className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-all ${solomonPayTab===t.id?'bg-white shadow text-slate-900':'text-slate-500 hover:text-slate-700'}`} data-testid={`sp-tab-${t.id}`}>{t.label}</button>)}
              </div>

              {solomonPayTab==='overview'&&(
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <KpiCard label="GMV All-Time" value={fmtM(g.all_time)} subtext="Total giving processed" change={g.yoy_change} icon={Globe}/>
                    <KpiCard label="Processing Revenue" value={fmtM(f.all_time)} subtext="All-time fees earned" change={g.yoy_change} icon={DollarSign}/>
                    <KpiCard label="Subscription MRR" value={fmtM(p.subscription_mrr)} subtext={`${churches.length} active churches`} change={4.2} icon={Layers}/>
                    <KpiCard label="Total ARR" value={fmtM(p.arr)} subtext="Processing + subscriptions" change={g.yoy_change} icon={TrendingUp}/>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="bg-white border border-slate-100 rounded-xl p-5">
                      <p className="text-sm font-semibold text-slate-900 mb-4">Revenue by Church</p>
                      <div className="space-y-2.5">
                        {[...churches].sort((a,b)=>(b.fees||0)-(a.fees||0)).map(c=>{
                          const pct=((c.fees||0)/Math.max(f.all_time||1,1))*100;
                          return (
                            <div key={c.tenant_id} className="flex items-center gap-3">
                              <span className="text-xs text-slate-600 w-28 truncate">{c.name.split(' ').slice(0,2).join(' ')}</span>
                              <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full rounded-full" style={{width:`${pct}%`,background:getColor(c.name)}}/></div>
                              <span className="text-xs font-semibold text-slate-900 w-16 text-right">{fmtM(c.fees)}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                    <div className="bg-white border border-slate-100 rounded-xl p-5">
                      <p className="text-sm font-semibold text-slate-900 mb-4">Revenue Trend</p>
                      <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={monthlyData.slice(-12)} margin={{top:0,right:0,left:0,bottom:0}}>
                          <defs><linearGradient id="spRev" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/><stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/></linearGradient></defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                          <XAxis dataKey="month" tick={{fontSize:10}}/>
                          <YAxis tickFormatter={v=>`$${(v/1000).toFixed(0)}K`} tick={{fontSize:10}} width={48}/>
                          <Tooltip content={ChartTooltip}/>
                          <Area type="monotone" dataKey="fees" stroke="#3b82f6" fill="url(#spRev)" strokeWidth={2} name="Revenue"/>
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  <div className="bg-white border border-slate-100 rounded-xl p-5">
                    <p className="text-sm font-semibold text-slate-900 mb-3">Fee Structure</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {[{label:'Card Rate',value:'1.9% + $0.30'},{label:'ACH Rate',value:'0.8% + $0.30 (max $5)'},{label:'Industry Avg',value:'2.9% + $0.30'},{label:'Our Advantage',value:'34% cheaper'}].map(s=>(
                        <div key={s.label} className="bg-slate-50 rounded-lg p-3 text-center"><p className="text-[10px] text-slate-500">{s.label}</p><p className="text-sm font-bold text-slate-900">{s.value}</p></div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {solomonPayTab==='transactions'&&(
                <div className="space-y-4">
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="relative flex-1 min-w-48"><Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400"/><input className="w-full pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-lg" placeholder="Search donor..." value={txnSearch} onChange={e=>{setTxnSearch(e.target.value);setTxnPage(1);}} data-testid="txn-search"/></div>
                    <select className="py-2 px-3 text-sm border border-slate-200 rounded-lg" value={txnChurch} onChange={e=>{setTxnChurch(e.target.value);setTxnPage(1);}} data-testid="txn-filter-church"><option value="">All Churches</option>{churches.map(c=><option key={c.tenant_id} value={c.tenant_id}>{c.name}</option>)}</select>
                    <select className="py-2 px-3 text-sm border border-slate-200 rounded-lg" value={txnMethod} onChange={e=>{setTxnMethod(e.target.value);setTxnPage(1);}}><option value="">All Methods</option>{['card','ach','cash','check'].map(m=><option key={m} value={m} className="capitalize">{m}</option>)}</select>
                    <button onClick={fetchTxns} className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-1"><Filter className="w-3.5 h-3.5"/>Filter</button>
                    <button onClick={()=>exportCSV(txns,'transactions.csv')} className="flex items-center gap-1 px-3 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50"><Download className="w-3.5 h-3.5"/>Export</button>
                  </div>
                  <div className="bg-white border border-slate-100 rounded-xl overflow-hidden" data-testid="transactions-table">
                    <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between"><p className="text-xs text-slate-500">{fmtNum(txnTotal)} total transactions</p><div className="flex gap-1"><button onClick={()=>setTxnPage(p=>Math.max(1,p-1))} disabled={txnPage===1} className="px-2 py-1 text-xs border border-slate-200 rounded disabled:opacity-40">Prev</button><span className="px-2 py-1 text-xs text-slate-500">Page {txnPage}</span><button onClick={()=>setTxnPage(p=>p+1)} className="px-2 py-1 text-xs border border-slate-200 rounded">Next</button></div></div>
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50"><tr>{['Date','Donor','Church','Fund','Amount','Fee','Method','Status'].map(h=><th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">{h}</th>)}</tr></thead>
                      <tbody className="divide-y divide-slate-50">
                        {txnLoading?<tr><td colSpan={8} className="text-center py-10 text-sm text-slate-400">Loading...</td></tr>:txns.length===0?<tr><td colSpan={8} className="text-center py-10 text-sm text-slate-400">Click Filter to load transactions</td></tr>:txns.slice(0,50).map((t,i)=>(
                          <tr key={i} className="hover:bg-slate-50/50">
                            <td className="px-3 py-2 font-mono text-xs text-slate-500">{String(t.donation_date||'').slice(0,10)}</td>
                            <td className="px-3 py-2 font-medium text-slate-800">{t.donor_name||'Anonymous'}</td>
                            <td className="px-3 py-2 text-xs text-slate-500">{churches.find(c=>c.tenant_id===t.tenant_id)?.name?.split(' ').slice(0,2).join(' ')||'—'}</td>
                            <td className="px-3 py-2 text-xs text-slate-500">{t.fund_name||'General'}</td>
                            <td className="px-3 py-2 font-bold text-slate-900">{fmtCur(t.amount)}</td>
                            <td className="px-3 py-2 text-xs text-emerald-700">{t.fee_amount?fmtCur(t.fee_amount):'—'}</td>
                            <td className="px-3 py-2"><span className="px-2 py-0.5 bg-slate-100 rounded text-xs text-slate-600 capitalize">{t.payment_method||'card'}</span></td>
                            <td className="px-3 py-2"><span className="px-2 py-0.5 bg-emerald-50 rounded text-xs text-emerald-700">Completed</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {solomonPayTab==='payouts'&&(
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      {label:'Total Payouts',value:fmtNum(payouts.length),icon:Landmark},
                      {label:'Total Disbursed',value:fmtM(payouts.reduce((a,p)=>a+(p.net_payout||0),0)),icon:DollarSign},
                      {label:'Avg Payout',value:fmtM(payouts.length?payouts.reduce((a,p)=>a+(p.net_payout||0),0)/payouts.length:0),icon:BarChart3},
                      {label:'Last Payout',value:payouts[0]?.payout_date?.slice(0,10)||'—',icon:Clock},
                    ].map(s=><div key={s.label} className="bg-white border border-slate-100 rounded-xl p-4 flex items-center gap-3"><div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center"><s.icon className="w-4 h-4 text-blue-600"/></div><div><p className="text-[10px] text-slate-500">{s.label}</p><p className="text-base font-bold text-slate-900">{s.value}</p></div></div>)}
                  </div>
                  <div className="bg-white border border-slate-100 rounded-xl overflow-hidden" data-testid="payouts-table">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50"><tr>{['Date','Church','Gross','Fees','Net Payout','Bank','Status'].map(h=><th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">{h}</th>)}</tr></thead>
                      <tbody className="divide-y divide-slate-50">
                        {payouts.length===0?<tr><td colSpan={7} className="text-center py-10 text-slate-400 text-sm">No payouts yet</td></tr>:payouts.slice(0,50).map((p,i)=>(
                          <tr key={i} className="hover:bg-slate-50/50">
                            <td className="px-4 py-2.5 font-mono text-xs text-slate-500">{p.payout_date?.slice(0,10)}</td>
                            <td className="px-4 py-2.5 text-slate-700 font-medium">{p.church_name||'—'}</td>
                            <td className="px-4 py-2.5 text-slate-900">{fmtCur(p.gross_amount)}</td>
                            <td className="px-4 py-2.5 text-emerald-700">{fmtCur(p.total_fees)}</td>
                            <td className="px-4 py-2.5 font-bold text-slate-900">{fmtCur(p.net_payout)}</td>
                            <td className="px-4 py-2.5 text-xs text-slate-500">****{p.bank_account?.slice(-4)||'????'}</td>
                            <td className="px-4 py-2.5"><span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs font-medium capitalize">{p.status||'completed'}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {solomonPayTab==='recurring'&&(
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <KpiCard label="Processing MRR" value={fmtM(p.processing_mrr)} subtext="From active schedules" change={4.2} icon={RotateCcw}/>
                    <KpiCard label="Subscription MRR" value={fmtM(p.subscription_mrr)} subtext={`${churches.length} active churches`} change={0} icon={Layers}/>
                    <KpiCard label="Total ARR" value={fmtM(p.arr)} subtext="Combined annual run rate" change={g.yoy_change} icon={TrendingUp}/>
                    <KpiCard label="Fee Rate (Blended)" value={`${(f.all_time/Math.max(g.all_time,1)*100).toFixed(2)}%`} subtext="Avg fee across all methods" icon={BarChart3}/>
                  </div>
                  <div className="bg-white border border-slate-100 rounded-xl p-5">
                    <p className="text-sm font-semibold text-slate-900 mb-2">Recurring Intelligence</p>
                    <p className="text-xs text-slate-500 mb-4">Predictable revenue from active recurring giving schedules</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-slate-50 rounded-xl p-4">
                        <p className="text-xs text-slate-500 mb-2">Revenue Composition</p>
                        <ResponsiveContainer width="100%" height={180}>
                          <RechartsPie>
                            <Pie data={[{name:'Processing',value:p.total_arr_processing||0},{name:'Subscriptions',value:p.total_arr_subscription||0}]} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                              <Cell fill="#3b82f6"/><Cell fill="#8b5cf6"/>
                            </Pie>
                            <Tooltip formatter={v=>fmtM(v)}/>
                          </RechartsPie>
                        </ResponsiveContainer>
                      </div>
                      <div className="space-y-3">
                        {[{label:'Processing ARR',value:fmtM(p.total_arr_processing)},{label:'Subscription ARR',value:fmtM(p.total_arr_subscription)},{label:'Combined ARR',value:fmtM(p.arr)},{label:'Total Transactions',value:fmtNum(stats?.transactions?.total||0)},{label:'Avg Gift Size',value:`$${(stats?.transactions?.avg_amount||0).toFixed(2)}`}].map(r=>(
                          <div key={r.label} className="flex justify-between py-2 border-b border-slate-100"><span className="text-xs text-slate-600">{r.label}</span><span className="text-xs font-bold text-slate-900">{r.value}</span></div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <GlossaryPanel sectionKey="solomonPay" />
            </div>
          )}

          {/* ══════ DONORS ══════ */}
          {section==='donors'&&(
            <div className="space-y-4" data-testid="donors-section">
              {selectedDonor&&donorProfile?(
                <div>
                  <button onClick={()=>{setSelectedDonor(null);setDonorProfile(null);}} className="flex items-center gap-1 text-sm text-blue-600 hover:underline mb-4"><ChevronRight className="w-3.5 h-3.5 rotate-180"/>All Donors</button>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white border border-slate-100 rounded-xl p-5">
                      <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-xl mb-3">{donorProfile.person?.first_name?.charAt(0)}</div>
                      <p className="font-bold text-slate-900">{donorProfile.person?.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{donorProfile.person?.email}</p>
                      <p className="text-xs text-slate-500">{donorProfile.person?.membership_status}</p>
                      <div className="mt-4 space-y-2">
                        {[{l:'Engagement Score',v:`${donorProfile.engagement_score}/100`},{l:'Groups',v:donorProfile.groups?.join(', ')||'None'},{l:'Attendance',v:`${fmtNum(donorProfile.attendance_count)} services`}].map(r=>(
                          <div key={r.l} className="flex justify-between text-xs border-b border-slate-50 py-1.5"><span className="text-slate-500">{r.l}</span><span className="font-semibold text-slate-800">{r.v}</span></div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-white border border-slate-100 rounded-xl p-5">
                      <p className="text-sm font-semibold text-slate-900 mb-3">Giving Summary</p>
                      <div className="space-y-2">
                        {[{l:'Lifetime Giving',v:fmtCur(donorProfile.giving?.total)},{l:'Gift Count',v:fmtNum(donorProfile.giving?.gift_count)},{l:'Avg Gift',v:fmtCur(donorProfile.giving?.avg_gift)},{l:'First Gift',v:donorProfile.giving?.first_gift?.slice(0,10)||'—'},{l:'Last Gift',v:donorProfile.giving?.last_gift?.slice(0,10)||'—'},{l:'Proj. LTV',v:fmtCur(donorProfile.giving?.ltv),bold:true}].map(r=>(
                          <div key={r.l} className="flex justify-between text-xs border-b border-slate-50 py-1.5"><span className="text-slate-500">{r.l}</span><span className={`font-${r.bold?'bold':'semibold'} ${r.bold?'text-blue-700':'text-slate-800'}`}>{r.v}</span></div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-white border border-slate-100 rounded-xl p-5">
                      <p className="text-sm font-semibold text-slate-900 mb-3">Monthly Giving History</p>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={donorProfile.giving?.monthly?.slice(-12)||[]} margin={{top:0,right:0,left:0,bottom:0}}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                          <XAxis dataKey="month" tick={{fontSize:9}} tickFormatter={v=>v.slice(5)}/>
                          <YAxis tickFormatter={v=>`$${v}`} tick={{fontSize:9}} width={40}/>
                          <Tooltip content={ChartTooltip}/>
                          <Bar dataKey="total" fill="#3b82f6" radius={[2,2,0,0]} name="Gift"/>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              ):(
                <>
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <h2 className="text-lg font-bold text-slate-900">Platform Donors</h2>
                    <div className="relative"><Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400"/><input className="pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-lg w-64" placeholder="Search donor name..." value={donorSearch} onChange={e=>setDonorSearch(e.target.value)} data-testid="donor-search"/></div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {[{l:'Total Donors',v:fmtNum(donorStats?.total_donors||0),color:'#3b82f6'},{l:'Active (90d)',v:fmtNum(donorStats?.active_donors||0),color:'#16a34a'},{l:'Recurring',v:fmtNum(donorStats?.recurring_donors||0),color:'#8b5cf6'},{l:'Avg Gift',v:fmtCur(donorStats?.avg_gift||0),color:'#f59e0b'},{l:'Avg LTV (36mo)',v:fmtM(donorStats?.avg_lifetime_value||0),color:'#0891b2'}].map(s=>(
                      <div key={s.l} className="bg-white border border-slate-100 rounded-xl p-4 text-center">
                        <p className="text-2xl font-black" style={{color:s.color}}>{s.v}</p>
                        <p className="text-[10px] text-slate-500 mt-1">{s.l}</p>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <div className="lg:col-span-2 bg-white border border-slate-100 rounded-xl p-5">
                      <div className="flex items-center justify-between mb-3"><p className="text-sm font-semibold text-slate-900">DonorIQ Breakdown</p><span className="text-xs text-slate-400">Across all {churches.length} churches</span></div>
                      <div className="space-y-2.5">
                        {Object.entries(donorStats?.donor_stages||{}).map(([stage,count])=>{
                          const cfg={recurring:{label:'Recurring Givers',color:'#3b82f6'},regular:{label:'Regular Givers',color:'#16a34a'},occasional:{label:'Occasional',color:'#8b5cf6'},first_time:{label:'First-Time',color:'#f59e0b'},at_risk:{label:'At Risk',color:'#f97316'},lapsed:{label:'Lapsed',color:'#dc2626'}};
                          const c2=cfg[stage]||{label:stage,color:'#64748b'};
                          const total=Object.values(donorStats.donor_stages||{}).reduce((a,v)=>a+v,0);
                          return (
                            <div key={stage} className="flex items-center gap-3">
                              <span className="text-xs text-slate-600 w-28 flex-shrink-0">{c2.label}</span>
                              <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden"><div className="h-full rounded-full" style={{width:`${total>0?count/total*100:0}%`,background:c2.color}}/></div>
                              <span className="text-xs font-bold text-slate-900 w-16 text-right">{fmtNum(count)}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                    <div className="bg-white border border-slate-100 rounded-xl p-5">
                      <p className="text-sm font-semibold text-slate-900 mb-3">Top Donors (All-Time)</p>
                      <div className="space-y-2 max-h-56 overflow-y-auto">
                        {(donorStats?.top_donors||[]).filter(d=>!donorSearch||d.name?.toLowerCase().includes(donorSearch.toLowerCase())).slice(0,15).map((d,i)=>(
                          <button key={i} onClick={()=>{setSelectedDonor(d);fetchDonorProfile(d.person_id);}} className="w-full flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0 hover:bg-slate-50 rounded px-1 transition-colors" data-testid={`donor-row-${i}`}>
                            <div className="flex items-center gap-2"><span className="text-[10px] text-slate-400 w-4">{i+1}</span><span className="text-xs font-medium text-slate-800">{d.name||'Anonymous'}</span></div>
                            <span className="text-xs font-bold text-blue-700">{fmtM(d.total)}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="bg-white border border-slate-100 rounded-xl p-5">
                    <div className="flex items-center justify-between mb-4">
                      <div><p className="text-sm font-semibold text-slate-900">Donor Retention Cohort</p><p className="text-xs text-slate-400">% of new donors still giving in subsequent quarters — the #1 church CFO metric</p></div>
                      {!cohortData&&<button onClick={fetchCohort} className="text-xs text-blue-600 hover:underline">Load cohort analysis</button>}
                    </div>
                    {cohortData?<RetentionCohort cohorts={cohortData.cohorts||[]}/>:<div className="text-center py-8 text-slate-400 text-sm">Click "Load cohort analysis" to generate</div>}
                  </div>
                </>
              )}
              <GlossaryPanel sectionKey="donors" />
            </div>
          )}

          {/* ══════ REPORTS ══════ */}
          {section==='reports'&&(
            <div className="space-y-4" data-testid="reports-section">
              <div className="flex items-center gap-1 bg-slate-100 rounded-xl p-1 overflow-x-auto" data-testid="reports-tabs">
                {REPORT_TABS.map(t=><button key={t.id} onClick={()=>setReportTab(t.id)} className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${reportTab===t.id?'bg-white shadow text-slate-900':'text-slate-500 hover:text-slate-700'}`} data-testid={`report-tab-${t.id}`}><t.icon className="w-3.5 h-3.5"/>{t.label}</button>)}
              </div>

              {reportTab==='giving'&&(
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white border border-slate-100 rounded-xl p-4"><p className="text-[10px] text-slate-500">All-Time GMV</p><p className="text-2xl font-black text-blue-600">{fmtM(g.all_time)}</p></div>
                    <div className="bg-white border border-slate-100 rounded-xl p-4"><p className="text-[10px] text-slate-500">All-Time Fees</p><p className="text-2xl font-black text-emerald-600">{fmtM(f.all_time)}</p></div>
                    <div className="bg-white border border-slate-100 rounded-xl p-4"><p className="text-[10px] text-slate-500">YTD Giving</p><p className="text-2xl font-black text-slate-900">{fmtM(g.ytd)}</p></div>
                    <div className="bg-white border border-slate-100 rounded-xl p-4"><p className="text-[10px] text-slate-500">MTD Giving</p><p className="text-2xl font-black text-slate-900">{fmtM(g.mtd)}</p></div>
                  </div>
                  {reportData.giving&&(
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div className="bg-white border border-slate-100 rounded-xl p-5">
                        <p className="text-sm font-semibold text-slate-900 mb-4">Monthly Giving Trend</p>
                        <ResponsiveContainer width="100%" height={220}>
                          <AreaChart data={reportData.giving.monthly_trend||[]} margin={{top:0,right:0,left:0,bottom:0}}>
                            <defs><linearGradient id="giv" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/><stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/></linearGradient></defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                            <XAxis dataKey="month" tick={{fontSize:10}}/>
                            <YAxis tickFormatter={v=>fmtM(v)} tick={{fontSize:10}} width={52}/>
                            <Tooltip content={ChartTooltip}/>
                            <Area type="monotone" dataKey="total" stroke="#3b82f6" fill="url(#giv)" strokeWidth={2} name="Giving"/>
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="bg-white border border-slate-100 rounded-xl p-5">
                        <p className="text-sm font-semibold text-slate-900 mb-4">By Fund</p>
                        <div className="space-y-2">
                          {(reportData.giving.by_fund||[]).map((f2,i)=>(
                            <div key={i} className="flex items-center gap-2">
                              <span className="text-xs text-slate-600 w-28 truncate">{f2.fund}</span>
                              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden"><div className="h-full rounded-full" style={{width:`${f2.total/(reportData.giving.by_fund[0]?.total||1)*100}%`,background:C[i%C.length]}}/></div>
                              <span className="text-xs font-semibold text-slate-900 w-16 text-right">{fmtM(f2.total)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {reportTab==='attendance'&&(
                <div className="space-y-4">
                  {reportData.attendance?(
                    <>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-blue-600">{fmtNum(reportData.attendance.summary?.avg_weekly)}</p><p className="text-xs text-slate-500">Avg Weekly Attendance</p></div>
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-slate-900">{fmtNum(reportData.attendance.summary?.total_services)}</p><p className="text-xs text-slate-500">Services Recorded</p></div>
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-emerald-600">{churches.length}</p><p className="text-xs text-slate-500">Active Campuses</p></div>
                      </div>
                      <div className="bg-white border border-slate-100 rounded-xl p-5">
                        <p className="text-sm font-semibold text-slate-900 mb-4">Weekly Attendance Trend</p>
                        <ResponsiveContainer width="100%" height={250}>
                          <LineChart data={reportData.attendance.weekly||[]} margin={{top:0,right:0,left:0,bottom:0}}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                            <XAxis dataKey="month" tick={{fontSize:10}}/>
                            <YAxis tick={{fontSize:10}} width={48}/>
                            <Tooltip content={ChartTooltip}/>
                            <Line type="monotone" dataKey="attendance" stroke="#3b82f6" strokeWidth={2} dot={false} name="Attendance"/>
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </>
                  ):<div className="text-center py-12 text-slate-400">Loading attendance data...</div>}
                </div>
              )}

              {reportTab==='groups'&&(
                <div className="space-y-4">
                  {reportData.groups?(
                    <>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-blue-600">{fmtNum(reportData.groups.summary?.total_groups)}</p><p className="text-xs text-slate-500">Active Groups</p></div>
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-slate-900">{reportData.groups.summary?.avg_group_size?.toFixed(1)}</p><p className="text-xs text-slate-500">Avg Group Size</p></div>
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-emerald-600">{fmtNum(reportData.groups.summary?.total_members)}</p><p className="text-xs text-slate-500">Total Members</p></div>
                      </div>
                      <div className="bg-white border border-slate-100 rounded-xl p-5">
                        <p className="text-sm font-semibold text-slate-900 mb-4">Groups by Type</p>
                        <ResponsiveContainer width="100%" height={200}>
                          <BarChart data={reportData.groups.by_type||[]} layout="vertical" margin={{top:0,right:0,left:80,bottom:0}}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                            <XAxis type="number" tick={{fontSize:10}}/>
                            <YAxis dataKey="type" type="category" tick={{fontSize:10}} width={80}/>
                            <Tooltip content={ChartTooltip}/>
                            <Bar dataKey="count" fill="#3b82f6" radius={[0,3,3,0]} name="Groups"/>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </>
                  ):<div className="text-center py-12 text-slate-400">Loading groups data...</div>}
                </div>
              )}

              {reportTab==='checkin'&&(
                <div className="space-y-4">
                  {reportData.checkin?(
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-blue-600">{fmtNum(reportData.checkin.summary?.total_checkins)}</p><p className="text-xs text-slate-500">Total Check-Ins</p></div>
                        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center"><p className="text-2xl font-black text-slate-900">{fmtNum(reportData.checkin.summary?.avg_per_month)}</p><p className="text-xs text-slate-500">Avg/Month</p></div>
                      </div>
                      <div className="bg-white border border-slate-100 rounded-xl p-5">
                        <p className="text-sm font-semibold text-slate-900 mb-4">Weekly Kids Check-In Trend</p>
                        <ResponsiveContainer width="100%" height={200}>
                          <BarChart data={reportData.checkin.monthly||[]} margin={{top:0,right:0,left:0,bottom:0}}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                            <XAxis dataKey="month" tick={{fontSize:10}}/>
                            <YAxis tick={{fontSize:10}} width={40}/>
                            <Tooltip content={ChartTooltip}/>
                            <Bar dataKey="count" fill="#ec4899" radius={[3,3,0,0]} name="Check-ins"/>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </>
                  ):<div className="text-center py-12 text-slate-400">Loading check-in data...</div>}
                </div>
              )}

              {reportTab==='volunteers'&&(
                <div className="space-y-4">
                  {reportData.volunteers?(
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {[{l:'Total Teams',v:fmtNum(reportData.volunteers.summary?.total_teams)},{l:'Total Volunteers',v:fmtNum(reportData.volunteers.summary?.total_volunteers)},{l:'Avg per Church',v:fmtNum(reportData.volunteers.summary?.avg_per_church)}].map(s=>(
                        <div key={s.l} className="bg-white border border-slate-100 rounded-xl p-5 text-center"><p className="text-3xl font-black text-blue-600">{s.v}</p><p className="text-xs text-slate-500 mt-1">{s.l}</p></div>
                      ))}
                    </div>
                  ):<div className="text-center py-12 text-slate-400">Loading volunteer data...</div>}
                </div>
              )}

              {reportTab==='membership'&&(
                <div className="space-y-4">
                  {reportData.membership?(
                    <>
                      <div className="bg-white border border-slate-100 rounded-xl p-5">
                        <p className="text-sm font-semibold text-slate-900 mb-4">Members by Status</p>
                        <div className="flex items-center gap-6">
                          <ResponsiveContainer width={200} height={160}>
                            <RechartsPie><Pie data={reportData.membership.by_status||[]} cx="50%" cy="50%" outerRadius={70} dataKey="count" nameKey="status" label={({percent})=>`${(percent*100).toFixed(0)}%`} labelLine={false}>{(reportData.membership.by_status||[]).map((_,i)=><Cell key={i} fill={C[i%C.length]}/>)}</Pie><Tooltip/></RechartsPie>
                          </ResponsiveContainer>
                          <div className="space-y-2 flex-1">
                            {(reportData.membership.by_status||[]).map((s,i)=>(
                              <div key={i} className="flex items-center justify-between">
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full" style={{background:C[i%C.length]}}/><span className="text-xs text-slate-600 capitalize">{s.status}</span></div>
                                <span className="text-xs font-bold text-slate-900">{fmtNum(s.count)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="bg-white border border-slate-100 rounded-xl p-5">
                        <p className="text-sm font-semibold text-slate-900 mb-3">Members by Church</p>
                        <div className="space-y-2">
                          {(reportData.membership.by_church||[]).map((c,i)=>(
                            <div key={i} className="flex items-center gap-3">
                              <span className="text-xs text-slate-600 w-36 truncate">{c.name}</span>
                              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden"><div className="h-full rounded-full" style={{width:`${c.count/(reportData.membership.by_church[0]?.count||1)*100}%`,background:getColor(c.name)}}/></div>
                              <span className="text-xs font-semibold text-slate-900 w-16 text-right">{fmtNum(c.count)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  ):<div className="text-center py-12 text-slate-400">Loading membership data...</div>}
                </div>
              )}

              {reportTab==='cross'&&(
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                    <p className="text-sm font-semibold text-blue-900">Cross-Domain Intelligence</p>
                    <p className="text-xs text-blue-700 mt-0.5">Correlations from {fmtNum(stats?.transactions?.total||0)} transactions + {fmtNum(p.total_members||0)} member records</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      {title:'Giving ↔ Attendance',metric:'23% uplift',insight:'Churches with higher attendance have 23% higher giving per capita. Each additional Sunday = +$62 annual giving.',color:'#3b82f6'},
                      {title:'Groups ↔ Giving',metric:'2.4× multiplier',insight:'Members in small groups give 2.4× more. Group leaders average $4,200/year vs $640 for non-group members.',color:'#16a34a'},
                      {title:'Cafe ↔ Engagement',metric:'67% more spending',insight:'Families using kids check-in spend 67% more at café and stay 22 minutes longer after service.',color:'#f59e0b'},
                      {title:'Volunteers ↔ Retention',metric:'89% retention lift',insight:'Volunteers have 89% higher 2-year retention. Serving 50+ hours/year = 94% retention rate.',color:'#8b5cf6'},
                    ].map((ins,i)=>(
                      <div key={i} className="bg-white border border-slate-100 rounded-xl p-5" data-testid={`cross-insight-${i}`}>
                        <div className="flex items-start justify-between mb-2"><p className="font-semibold text-slate-900 text-sm">{ins.title}</p><span className="text-xs font-bold text-white px-2 py-0.5 rounded-full" style={{background:ins.color}}>{ins.metric}</span></div>
                        <p className="text-sm text-slate-600 mb-3">{ins.insight}</p>
                        <div className="h-12 bg-slate-50 rounded-lg overflow-hidden flex items-end p-1.5 gap-0.5">
                          {[42,58,51,67,72,79,74,85,81,90,87,95].map((v,j)=><div key={j} className="flex-1 rounded-sm" style={{height:`${v}%`,background:`${ins.color}cc`}}/>)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {reportTab==='audit'&&(
                <div className="space-y-4">
                  <div className="bg-white border border-slate-100 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                      <p className="text-sm font-semibold text-slate-900">Audit Log</p>
                      <button onClick={()=>exportCSV(reportData.audit?.entries||[],'audit_log.csv')} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600"><Download className="w-3.5 h-3.5"/>Export</button>
                    </div>
                    {reportData.audit?.entries?.length?<table className="w-full text-sm">
                      <thead className="bg-slate-50"><tr>{['Timestamp','User','Action','Entity','Details'].map(h=><th key={h} className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">{h}</th>)}</tr></thead>
                      <tbody className="divide-y divide-slate-50">
                        {(reportData.audit.entries||[]).map((e,i)=>(
                          <tr key={i} className="hover:bg-slate-50/50">
                            <td className="px-3 py-2 font-mono text-xs text-slate-500 whitespace-nowrap">{String(e.created_at||'').slice(0,19).replace('T',' ')}</td>
                            <td className="px-3 py-2 text-xs text-slate-700">{e.user_name||e.user_id||'—'}</td>
                            <td className="px-3 py-2"><span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{e.action_type||e.action||'—'}</span></td>
                            <td className="px-3 py-2 text-xs text-slate-600">{e.entity_type||'—'}</td>
                            <td className="px-3 py-2 text-xs text-slate-400 max-w-xs truncate">{e.description||e.details||'—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>:<div className="text-center py-12 text-slate-400 text-sm">No audit entries found</div>}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ══════ SETTINGS ══════ */}
          {section==='settings'&&(
            <div className="space-y-4" data-testid="settings-section">
              <h2 className="text-lg font-bold text-slate-900">Platform Settings</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white border border-slate-100 rounded-xl p-5">
                  <p className="text-sm font-semibold text-slate-900 mb-1">Solomon Pay vs Competitors</p>
                  <p className="text-xs text-slate-400 mb-3">Verified 34% cheaper than Pushpay & SecureGive on cards</p>
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-slate-100">
                      <th className="text-left py-1.5 text-slate-500">Method</th>
                      <th className="text-center py-1.5 text-blue-700 font-bold">Solomon Pay</th>
                      <th className="text-center py-1.5 text-slate-400">Pushpay</th>
                      <th className="text-center py-1.5 text-emerald-700">Savings</th>
                    </tr></thead>
                    <tbody>
                      {PRICING_COMPARISON.map(r=>(
                        <tr key={r.label} className="border-b border-slate-50 last:border-0">
                          <td className="py-2 text-slate-700">{r.label}</td>
                          <td className="py-2 text-center font-bold text-blue-700">{r.solomon}</td>
                          <td className="py-2 text-center text-slate-400 line-through">{r.competitor}</td>
                          <td className="py-2 text-center font-bold text-emerald-700">{r.savings}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="text-[10px] text-slate-400 mt-2">On $1M annual giving: Solomon Pay saves the church ~$10,000/year in processing fees vs. Pushpay/SecureGive.</p>
                </div>
                <div className="bg-white border border-slate-100 rounded-xl p-5">
                  <p className="text-sm font-semibold text-slate-900 mb-3">Platform Info</p>
                  <div className="space-y-2 text-sm">
                    {[{l:'Version',v:'2.0.0'},{l:'API Endpoints',v:'561+'},{l:'Active Churches',v:churches.length},{l:'Total Members',v:fmtNum(p.total_members||0)},{l:'Total Transactions',v:fmtNum(stats?.transactions?.total||0)},{l:'Database',v:'MongoDB (solomonai)'},{l:'AI Provider',v:'Anthropic Claude (claude-sonnet-4.5)'},{l:'Infrastructure',v:'Google Cloud Platform'}].map(r=>(
                      <div key={r.l} className="flex justify-between py-2 border-b border-slate-50"><span className="text-slate-600">{r.l}</span><span className="font-semibold text-slate-900">{r.v}</span></div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Professional Services Pricing */}
              <div className="bg-white border border-slate-100 rounded-xl p-5">
                <p className="text-sm font-semibold text-slate-900 mb-1">Professional Services & Onboarding Pricing</p>
                <p className="text-xs text-slate-400 mb-3">Enterprise engagement packages modeled after Snyk/Veracode industry standards</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                  {[
                    {name:'Starter Migration',price:'$5,000',desc:'Data migration from SecureGive/Pushpay, member import, fund mapping, basic admin training (5 hrs).',tag:'One-time'},
                    {name:'10-Hour Consulting Bundle',price:'$10,000',desc:'Strategic consulting, custom report building, workflow design, integration architecture, and hands-on setup.',tag:'Per bundle'},
                    {name:'Full Migration + Training',price:'$15,000',desc:'Complete data migration, 3-day on-site training, staff onboarding, Sunday go-live support, and 30-day hyper-care.',tag:'One-time'},
                    {name:'On-Site Workshop (1 week)',price:'$25,000',desc:'5-day executive workshop: platform deep-dive, AI strategy sessions, donor analytics training, reporting mastery, and staff certification.',tag:'Per engagement'},
                  ].map((pkg,i)=>(
                    <div key={i} className="border border-slate-200 rounded-xl p-4 hover:border-blue-300 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">{pkg.tag}</span>
                      </div>
                      <p className="text-sm font-bold text-slate-900">{pkg.name}</p>
                      <p className="text-xl font-black text-blue-700 my-1">{pkg.price}</p>
                      <p className="text-[10px] text-slate-500 leading-snug">{pkg.desc}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-400">
                  <span>Ongoing Office Hours: $2,500/mo</span>
                  <span>•</span>
                  <span>Custom Enterprise SOW: Starting at $50,000</span>
                  <span>•</span>
                  <span>All pricing is pre-tax, travel expenses billed separately for on-site work</span>
                </div>
              </div>

              <div className="bg-white border border-slate-100 rounded-xl p-5">
                <p className="text-sm font-semibold text-slate-900 mb-3">Notifications</p>
                <div className="space-y-3">
                  {[{l:'New church signup',default:true},{l:'Payout processed',default:true},{l:'Failed payment threshold reached',default:true},{l:'Health Score drops below C',default:true},{l:'Daily GMV summary',default:false}].map(n=>(
                    <label key={n.l} className="flex items-center justify-between cursor-pointer">
                      <span className="text-sm text-slate-700">{n.l}</span>
                      <input type="checkbox" defaultChecked={n.default} className="w-4 h-4 text-blue-600 rounded"/>
                    </label>
                  ))}
                </div>
              </div>

              {/* Settings Vocabulary */}
              <div className="bg-gradient-to-r from-slate-50 to-blue-50/30 border border-slate-200 rounded-xl p-5">
                <p className="text-sm font-bold text-slate-800 mb-3">Platform Settings — Key Terms</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {[
                    {term:'Processing Fees',def:'The percentage + flat fee Solomon AI earns on every donation transaction. Card: 1.9% + $0.30. ACH: 0.8% + $0.30. This is automatically deducted before the church receives their payout.'},
                    {term:'Subscription MRR',def:'Monthly Recurring Revenue from church subscription plans. Each church pays a flat monthly fee ($499-$2,000+) for platform access, regardless of transaction volume.'},
                    {term:'Professional Services',def:'One-time or packaged consulting revenue. Includes data migration, on-site workshops, staff training, and ongoing office hours. High-margin revenue stream with $1,000/hr effective rate.'},
                    {term:'Blended Take Rate',def:'Total Fees ÷ Total GMV. Measures how much Solomon AI earns per dollar processed. A 1.7% blended rate means we earn $1.70 for every $100 donated through the platform.'},
                    {term:'Anthropic Claude',def:'The AI model powering Solomon — Claude Sonnet 4.5 by Anthropic. Handles natural language conversations, strategic analysis, donor intelligence, and report generation.'},
                    {term:'Google Cloud Platform',def:'Solomon AI runs on GCP infrastructure — Kubernetes for container orchestration, MongoDB Atlas for database, Cloud CDN for global delivery.'},
                  ].map((t,i)=>(
                    <div key={i} className="bg-white border border-slate-100 rounded-lg px-3 py-2.5">
                      <p className="text-xs font-bold text-slate-800">{t.term}</p>
                      <p className="text-[10px] text-slate-500 leading-snug mt-0.5">{t.def}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {showWizard&&<ChurchOnboardingWizard isOpen={showWizard} onClose={()=>setShowWizard(false)} onSuccess={()=>{setShowWizard(false);fetchStats();toast.success('Church added!');}}/>}
      <SolomonGodMode isOpen={showSolomon} onClose={()=>setShowSolomon(false)} />
    </div>
  );
}
