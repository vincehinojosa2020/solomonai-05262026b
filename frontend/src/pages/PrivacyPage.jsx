import { Link } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';

export default function PrivacyPage() {
  return (
    <div style={{ background: '#f8fafc', minHeight: '100vh' }} data-testid="privacy-page">
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
          <Shield style={{ width: 28, height: 28, color: '#3b82f6' }} />
          <h1 style={{ fontSize: 32, fontWeight: 800, color: '#0f172a', margin: 0 }}>Privacy Policy</h1>
        </div>
        <p style={{ color: '#64748b', marginBottom: 8, fontSize: 14 }}>Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>

        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 32, lineHeight: 1.8, color: '#334155', fontSize: 15 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a', marginTop: 0 }}>1. Information We Collect</h2>
          <p>Solomon AI collects information you provide when creating an account, making donations, registering for events, or communicating through our platform. This includes names, email addresses, phone numbers, mailing addresses, and payment information.</p>
          <p>For churches using Solomon Pay, we process payment information through PCI-compliant third-party processors. We do not store full credit card numbers on our servers.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>2. How We Use Your Information</h2>
          <p>We use your information to: provide and maintain our services, process donations and transactions, send receipts and giving statements, communicate about events and church activities, and improve our platform through analytics.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>3. Data Sharing</h2>
          <p>We share your information only with the church organization(s) you are connected to through our platform. Your church admin can view member profiles, giving history, and attendance records within their tenant. We do not sell personal data to third parties.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>4. AI Assistant (Ask Solomon)</h2>
          <p>Our AI assistant processes queries using Anthropic's Claude language model. Conversations may include church data context to provide relevant answers. AI conversations are stored for session continuity and may be reviewed to improve service quality.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>5. Data Retention & Deletion</h2>
          <p>Donation records are retained for 7 years to comply with IRS requirements for charitable giving documentation. You may request deletion of your personal account data by contacting your church admin or emailing privacy@solomonai.us.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>6. Security</h2>
          <p>We implement industry-standard security measures including encrypted data transmission (TLS), secure session management, and access controls. For details, see our <Link to="/security" style={{ color: '#3b82f6' }}>Security page</Link>.</p>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>7. Contact</h2>
          <p>For privacy questions or data requests, contact us at <a href="mailto:privacy@solomonai.us" style={{ color: '#3b82f6' }}>privacy@solomonai.us</a>.</p>
        </div>
      </div>
    </div>
  );
}
