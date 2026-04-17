import { Link } from 'react-router-dom';
import { ArrowLeft, Lock, ShieldCheck, Server, Key, Eye, Database } from 'lucide-react';

export default function SecurityPage() {
  const items = [
    { icon: Lock, title: 'Encryption in Transit', desc: 'All data transmitted between your browser and Solomon AI is encrypted using TLS 1.3. API communications use HTTPS exclusively.' },
    { icon: Database, title: 'Data at Rest', desc: 'Database backups are encrypted using AES-256 encryption. Production infrastructure runs in SOC 2-compliant data centers.' },
    { icon: Key, title: 'Authentication', desc: 'Session-based authentication with httpOnly secure cookies. Password hashing uses bcrypt with automatic migration from legacy algorithms. Google OAuth available for social login.' },
    { icon: ShieldCheck, title: 'Access Controls', desc: 'Role-based access control (RBAC) with four tiers: Platform Admin, Church Admin, Staff, and Member. Each role has granular permissions. Cross-tenant data isolation enforced at the database query level.' },
    { icon: Server, title: 'Infrastructure', desc: 'Hosted on Google Cloud Platform with Kubernetes orchestration. Automated health checks, container isolation, and supervisor-managed processes ensure high availability.' },
    { icon: Eye, title: 'Audit Logging', desc: 'Administrative actions are logged to an immutable audit trail including user identity, action type, timestamp, and affected records. Accessible to church admins via the Audit Log page.' },
  ];

  return (
    <div style={{ background: '#f8fafc', minHeight: '100vh' }} data-testid="security-page">
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <ShieldCheck style={{ width: 28, height: 28, color: '#3b82f6' }} />
          <h1 style={{ fontSize: 32, fontWeight: 800, color: '#0f172a', margin: 0 }}>Security</h1>
        </div>
        <p style={{ color: '#64748b', marginBottom: 32, fontSize: 15 }}>How Solomon AI protects your church's data</p>

        <div style={{ display: 'grid', gap: 16 }}>
          {items.map(item => (
            <div key={item.title} style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 24, display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <div style={{ width: 44, height: 44, borderRadius: 10, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <item.icon style={{ width: 22, height: 22, color: '#3b82f6' }} />
              </div>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', margin: '0 0 6px 0' }}>{item.title}</h3>
                <p style={{ fontSize: 14, color: '#475569', margin: 0, lineHeight: 1.7 }}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div style={{ background: '#0f172a', borderRadius: 12, padding: 32, marginTop: 24, textAlign: 'center' }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', margin: '0 0 8px 0' }}>Report a Vulnerability</h3>
          <p style={{ fontSize: 14, color: '#94a3b8', margin: '0 0 16px 0' }}>If you discover a security issue, please report it responsibly.</p>
          <a href="mailto:security@solomonai.us" style={{ color: '#3b82f6', fontSize: 15, fontWeight: 600 }}>security@solomonai.us</a>
        </div>
      </div>
    </div>
  );
}
