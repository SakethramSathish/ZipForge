import React from 'react';
import { ShieldCheck, Cpu, HardDrive } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer
      style={{
        borderTop: 'var(--border-width) solid var(--border-color)',
        backgroundColor: 'var(--bg-surface)',
        padding: '2rem 1.25rem',
        marginTop: 'auto',
      }}
    >
      <div
        className="nb-container"
        style={{
          padding: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.1rem' }}>
                ⚡ ZIPFORGE
              </span>
              <span className="nb-badge nb-badge-mint" style={{ fontSize: '0.68rem' }}>
                PRODUCTION READY
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
              Defensive, high-performance compression platform combining classical algorithms with target-size budgeting.
            </p>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span className="nb-badge nb-badge-gray">
              <Cpu size={12} strokeWidth={2.5} />
              HUFFMAN · LZW · RLE
            </span>
            <span className="nb-badge nb-badge-gray">
              <ShieldCheck size={12} strokeWidth={2.5} />
              SHA-256 DEFENSE
            </span>
            <span className="nb-badge nb-badge-gray">
              <HardDrive size={12} strokeWidth={2.5} />
              UNIVERSAL .ZIP
            </span>
          </div>
        </div>

        <div
          style={{
            borderTop: '1px solid var(--border-color)',
            paddingTop: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            fontSize: '0.78rem',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <span>© 2026 ZipForge Architecture. Clean Two-Tier Production System.</span>
          <span>Zero external runtime telemetry · 100% Local execution</span>
        </div>
      </div>
    </footer>
  );
};
