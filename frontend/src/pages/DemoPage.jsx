/**
 * Solomon AI — Demo Scenarios + ROI Calculator
 * Route: /demo
 */
import { useState } from 'react';
import { DollarSign, Users, Zap, TrendingUp, CheckCircle, Play, Building2, Crown } from 'lucide-react';

function fmtCur(n) {
  const v = Number(n||0);
  if(v>=1e6) return `$${(v/1e6).toFixed(1)}M`;
  if(v>=1e3) return `$${(v/1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

const SCENARIOS = [
  { id:'switch', emoji:'⚡', title:'The Pushpay Switch', subtitle:'"We\'re 34% cheaper. Here\'s the math."', color:'#3b82f6', duration:'4 min',
    script:[
      {step:1,action:'Open Pricing page',line:'"Right now, Potter\'s House pays Pushpay $106,000/year in processing fees. Watch what happens when they switch to Solomon Pay."'},
      {step:2,action:'ROI Calculator → $5.2M annual giving',line:'"Same giving volume, Solomon Pay charges $73,000. That\'s $33,000 back in their ministry budget every single year."'},
      {step:3,action:'God Mode → Churches → Potter\'s House → Ask Solomon',line:'"But here\'s what Pushpay can\'t do. Because we\'re also the CRM, I can see 23% of their donors are at risk of lapsing. I trigger an AI workflow before they lose them."'},
      {step:4,action:'Ask Solomon: "Which donors are at risk?"',line:'"Solomon just surfaced 847 at-risk donors. Pushpay would never know this. We do."'},
    ],
    wow:'Church saves $33K/year AND prevents donor churn. Double win.',
  },
  { id:'giving', emoji:'🎁', title:'Sunday Morning in 60 Seconds', subtitle:'"From phone to confirmed gift in under a minute."', color:'#10b981', duration:'3 min',
    script:[
      {step:1,action:'Open Member Portal',line:'"This is what 100,000 members see when they open the app Sunday morning."'},
      {step:2,action:'Click Give → Building Fund → $100',line:'"One tap. It remembers her card. It knows she gave $240 last month. It suggests the right fund."'},
      {step:3,action:'Ask Solomon: "Give $100 to missions"',line:'"Or she just tells Solomon. No forms. The AI handles it with a confirmation card before charging anything."'},
      {step:4,action:'Switch to Admin → Giving Dashboard',line:'"The moment she confirms, her pastor sees it here. Real-time. Down to the fund. Down to the dollar."'},
    ],
    wow:'Complete giving experience — intent to receipt — in under 60 seconds.',
  },
  { id:'intelligence', emoji:'🧠', title:'The AI Intelligence Demo', subtitle:'"We know things Pushpay will never know."', color:'#8b5cf6', duration:'5 min',
    script:[
      {step:1,action:'Open God Mode → Dashboard',line:'"$116 million processed. 8 churches. 100,000 members. All in one place. This is Solomon AI at scale."'},
      {step:2,action:'Ask Solomon: "Which church needs attention?"',line:'"Solomon analyzes giving, attendance, groups, and volunteers across all 8 churches simultaneously. It identifies decline before the pastor knows."'},
      {step:3,action:'Reports → Cross-Analysis tab',line:'"Members in small groups give 2.4x more. We\'re the only platform that proves this — because we\'re the CRM AND the payment processor. Pushpay can\'t see groups."'},
      {step:4,action:'Donors → Retention Cohort chart',line:'"The chart CFOs ask for first. Of donors who gave in Q1 2024, 67% are still giving. Industry average: 43%. We keep donors. That\'s the business."'},
    ],
    wow:'CRM + Payments + AI = insights no pure payment processor can ever provide.',
  },
];

export default function DemoPage() {
  const [activeScenario, setActiveScenario] = useState(null);
  const [churchSize, setChurchSize] = useState(5000);
  const [annualGiving, setAnnualGiving] = useState(2500000);
  const [cardPct, setCardPct] = useState(55);
  const [achPct, setAchPct] = useState(15);

  const cardAmt = annualGiving * (cardPct/100);
  const achAmt = annualGiving * (achPct/100);
  const txnCard = Math.round(cardAmt / 85); // avg card gift ~$85
  const txnACH  = Math.round(achAmt / 200);

  const solomonCard = cardAmt * 0.019 + txnCard * 0.30;
  const solomonACH  = Math.min(achAmt * 0.008 + txnACH * 0.30, txnACH * 5.0);
  const pushCard    = cardAmt * 0.029 + txnCard * 0.30;
  const pushACH     = achAmt  * 0.010 + txnACH * 0.30;

  const savings = Math.round(pushCard + pushACH - solomonCard - solomonACH);
  const savingsPct = Math.round(savings / Math.max(pushCard + pushACH, 1) * 100);
  const subTier = churchSize >= 10000 ? {name:'Enterprise',price:2000} : churchSize >= 5000 ? {name:'Professional',price:1499} : churchSize >= 1000 ? {name:'Growth',price:999} : {name:'Starter',price:499};

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4" data-testid="demo-page">
      <div className="max-w-5xl mx-auto space-y-12">

        <div className="text-center">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-xs font-bold mb-4">
            <Zap className="w-3.5 h-3.5"/> INVESTOR DEMO READY
          </span>
          <h1 className="text-4xl font-black text-slate-900 mb-3">Solomon AI Demo Playbook</h1>
          <p className="text-slate-500 text-lg max-w-xl mx-auto">3 scripted scenarios for investor conversations. Each under 5 minutes. Each a mic drop.</p>
        </div>

        {/* ROI Calculator */}
        <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm" data-testid="roi-calculator">
          <div className="bg-blue-600 px-8 py-5">
            <h2 className="text-xl font-bold text-white">Solomon Pay ROI Calculator</h2>
            <p className="text-blue-200 text-sm mt-0.5">Show any church exactly what they save vs. Pushpay or SecureGive</p>
          </div>
          <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-5">
              {[
                {label:'Church Size',min:100,max:30000,step:100,value:churchSize,onChange:setChurchSize,fmt:v=>v.toLocaleString()+' members'},
                {label:'Annual Giving Volume',min:50000,max:20000000,step:50000,value:annualGiving,onChange:setAnnualGiving,fmt:v=>fmtCur(v)},
                {label:'Card Transaction %',min:20,max:85,step:5,value:cardPct,onChange:setCardPct,fmt:v=>`${v}%`},
              ].map(f=>(
                <div key={f.label}>
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{f.label}</label>
                  <div className="flex items-center gap-3 mt-1.5">
                    <input type="range" min={f.min} max={f.max} step={f.step} value={f.value}
                      onChange={e=>f.onChange(Number(e.target.value))} className="flex-1 accent-blue-600"/>
                    <span className="w-24 text-sm font-bold text-right text-slate-900">{f.fmt(f.value)}</span>
                  </div>
                </div>
              ))}
              <div className="bg-blue-50 rounded-xl p-3 text-xs text-blue-800">
                <strong>Subscription tier:</strong> {subTier.name} — ${subTier.price.toLocaleString()}/mo
              </div>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-50 border-2 border-slate-200 rounded-xl p-4 text-center">
                  <p className="text-xs text-slate-500 mb-1">Pushpay Fees / Year</p>
                  <p className="text-2xl font-black text-red-500">{fmtCur(pushCard+pushACH)}</p>
                </div>
                <div className="bg-blue-50 border-2 border-blue-400 rounded-xl p-4 text-center">
                  <p className="text-xs text-blue-600 mb-1">Solomon Pay Fees / Year</p>
                  <p className="text-2xl font-black text-blue-700">{fmtCur(solomonCard+solomonACH)}</p>
                </div>
              </div>
              <div className="bg-emerald-50 border-2 border-emerald-400 rounded-xl p-5 text-center">
                <p className="text-sm font-semibold text-emerald-700 mb-1">Annual Savings</p>
                <p className="text-5xl font-black text-emerald-600">{fmtCur(savings)}</p>
                <p className="text-sm text-emerald-600 mt-1">{savingsPct}% lower — {fmtCur(savings*5)} over 5 years</p>
              </div>
            </div>
          </div>
        </div>

        {/* Scenarios */}
        <div>
          <h2 className="text-2xl font-bold text-slate-900 mb-4">3 Demo Scenarios</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {SCENARIOS.map(s=>(
              <button key={s.id} onClick={()=>setActiveScenario(activeScenario?.id===s.id?null:s)}
                className={`text-left p-5 rounded-xl border-2 transition-all ${activeScenario?.id===s.id?'shadow-lg':'border-slate-200 bg-white hover:border-slate-300'}`}
                style={activeScenario?.id===s.id?{borderColor:s.color,background:`${s.color}08`}:{}}
                data-testid={`scenario-${s.id}`}>
                <div className="text-3xl mb-3">{s.emoji}</div>
                <p className="font-bold text-slate-900">{s.title}</p>
                <p className="text-xs text-slate-500 mt-0.5">{s.subtitle}</p>
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full text-white" style={{background:s.color}}>{s.duration}</span>
                  <Play className="w-3 h-3 text-slate-300"/>
                </div>
              </button>
            ))}
          </div>

          {activeScenario && (
            <div className="bg-white border-2 rounded-2xl overflow-hidden" style={{borderColor:activeScenario.color}}>
              <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3" style={{background:`${activeScenario.color}10`}}>
                <span className="text-2xl">{activeScenario.emoji}</span>
                <div><p className="font-bold text-slate-900">{activeScenario.title}</p><p className="text-xs text-slate-500">{activeScenario.subtitle}</p></div>
              </div>
              <div className="p-6 space-y-4">
                {activeScenario.script.map(step=>(
                  <div key={step.step} className="flex gap-4">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0" style={{background:activeScenario.color}}>{step.step}</div>
                    <div>
                      <p className="text-xs font-semibold text-slate-400 uppercase mb-1">→ {step.action}</p>
                      <p className="text-sm text-slate-700 italic leading-relaxed">"{step.line}"</p>
                    </div>
                  </div>
                ))}
                <div className="p-4 rounded-xl" style={{background:`${activeScenario.color}10`,border:`2px solid ${activeScenario.color}40`}}>
                  <p className="text-xs font-bold uppercase tracking-wider mb-1" style={{color:activeScenario.color}}>The Wow Moment</p>
                  <p className="text-sm font-semibold text-slate-800">{activeScenario.wow}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Feature Parity */}
        <div className="bg-white border border-slate-200 rounded-2xl p-8">
          <h2 className="text-xl font-bold text-slate-900 mb-1">Feature Parity vs. Pushpay & SecureGive</h2>
          <p className="text-sm text-slate-400 mb-5">Solomon AI matches every core capability — plus 6 features competitors can never have.</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b-2 border-slate-200">
                <th className="text-left py-2.5 text-slate-700 font-bold">Feature</th>
                <th className="text-center py-2.5 text-blue-700 font-bold">Solomon AI</th>
                <th className="text-center py-2.5 text-slate-400 font-semibold">Pushpay</th>
                <th className="text-center py-2.5 text-slate-400 font-semibold">SecureGive</th>
                <th className="text-left py-2.5 text-slate-500 font-semibold">Our Edge</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-50">
                {[
                  ['Online Giving','✅','✅','✅','34% lower fees'],
                  ['Recurring Giving','✅','✅','✅','AI churn prediction'],
                  ['ACH / Bank Transfer','✅','✅','✅','0.8% vs 1%+'],
                  ['Text-to-Give','✅','✅','❌','Integrated with CRM data'],
                  ['Real-time Reporting','✅','✅','⚠️','Cross-domain intelligence'],
                  ['Donor Retention Cohort','✅','✅','❌','Linked to attendance + groups'],
                  ['Kids Check-In','✅','❌','❌','🔥 Exclusive'],
                  ['CRM / People Database','✅','❌','❌','🔥 Exclusive'],
                  ['Small Groups','✅','❌','❌','🔥 Exclusive — groups ↔ giving'],
                  ['Service Planning + Live Mode','✅','❌','❌','🔥 Exclusive'],
                  ['AI Analytics Assistant','✅','❌','❌','🔥 Exclusive differentiator'],
                  ['Church Health Score','✅','❌','❌','🔥 Exclusive'],
                ].map(([f,s,p,sg,e])=>(
                  <tr key={f} className="hover:bg-slate-50/50">
                    <td className="py-2 font-medium text-slate-800">{f}</td>
                    <td className="py-2 text-center">{s}</td>
                    <td className="py-2 text-center">{p}</td>
                    <td className="py-2 text-center">{sg}</td>
                    <td className="py-2 text-xs text-slate-500">{e}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
