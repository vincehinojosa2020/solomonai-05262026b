import { Link } from 'react-router-dom';
import { ArrowLeft, FileText } from 'lucide-react';

export default function TermsPage() {
  return (
    <div style={{ background: '#f8fafc', minHeight: '100vh' }} data-testid="terms-page">
      <nav style={{ background: '#0f172a', padding: '16px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'baseline', gap: 6, textDecoration: 'none' }}>
          <span style={{ fontSize: 16, fontWeight: 200, letterSpacing: 6, color: '#fff' }}>SOLOMON</span>
          <span style={{ fontSize: 16, fontWeight: 700, color: '#3b82f6' }}>AI</span>
        </Link>
        <Link to="/" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
          <ArrowLeft style={{ width: 16, height: 16 }} /> Back
        </Link>
      </nav>
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '48px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
          <FileText style={{ width: 28, height: 28, color: '#3b82f6' }} />
          <h1 style={{ fontSize: 32, fontWeight: 800, color: '#0f172a', margin: 0 }}>Terms of Service</h1>
        </div>
        <p style={{ color: '#64748b', marginBottom: 8, fontSize: 14 }}>Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>

        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 32, lineHeight: 1.8, color: '#334155', fontSize: 15 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a', marginTop: 0 }}>1. Acceptance of Terms</h2>
          <p>By accessing or using Solomon AI ("the Platform"), you agree to be bound by these Terms of Service. If you are using the Platform on behalf of a church or organization, you represent that you have authority to bind that organization.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>2. Description of Service</h2>
          <p>Solomon AI is a cloud-based church management platform providing member management, online giving, attendance tracking, kids check-in, group management, event coordination, communications, and AI-powered analytics. Solomon Pay is our integrated payment processing service.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>3. Account Responsibilities</h2>
          <p>You are responsible for maintaining the confidentiality of your account credentials. Church administrators are responsible for managing user access within their organization and ensuring appropriate data handling practices.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>4. Payment Processing</h2>
          <p>Solomon Pay processing fees are 1.9% + $0.30 per card transaction and 0.8% + $0.30 per ACH transaction (capped at $5.00). Fees are deducted before settlement to the church's connected bank account. Payouts are initiated within 2 business days of transaction completion.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>5. Data Ownership</h2>
          <p>Your church retains full ownership of all member data, donation records, and content uploaded to the Platform. Solomon AI has a limited license to process this data solely to provide the service. Upon termination, you may export all data in standard formats (CSV, PDF).</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>6. Subscription & Billing</h2>
          <p>Platform subscriptions are billed monthly. Plans may be upgraded or downgraded at any time. No long-term contracts are required. Cancellation takes effect at the end of the current billing period.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>7. Limitation of Liability</h2>
          <p>Solomon AI's liability is limited to the fees paid by the church in the 12 months preceding any claim. We are not liable for indirect, incidental, or consequential damages arising from use of the Platform.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>8. Contact</h2>
          <p>For questions about these terms, contact <a href="mailto:legal@solomonai.us" style={{ color: '#3b82f6' }}>legal@solomonai.us</a>.</p>
        </div>
      </div>
    </div>
  );
}
