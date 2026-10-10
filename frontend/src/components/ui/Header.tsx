import React, { useState, useEffect } from 'react';
import { Zap, HelpCircle, Activity } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { Modal } from './Modal';
import { api } from '../../utilities/api';

export type TabId = 'compress' | 'decompress' | 'image' | 'benchmark' | 'inspect';

export interface HeaderProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange }) => {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [isInfoOpen, setIsInfoOpen] = useState(false);

  useEffect(() => {
    api.checkHealth()
      .then(() => setIsOnline(true))
      .catch(() => setIsOnline(false));

    const interval = setInterval(() => {
      api.checkHealth()
        .then(() => setIsOnline(true))
        .catch(() => setIsOnline(false));
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const tabs: { id: TabId; label: string; icon: string }[] = [
    { id: 'compress', label: 'COMPRESS', icon: '🗜️' },
    { id: 'decompress', label: 'DECOMPRESS', icon: '📂' },
    { id: 'image', label: 'IMAGE OPTIMIZER', icon: '🖼️' },
    { id: 'benchmark', label: 'BENCHMARK', icon: '📊' },
    { id: 'inspect', label: 'INSPECT ARCHIVE', icon: '🔍' },
  ];

  return (
    <header
      style={{
        borderBottom: 'var(--border-width) solid var(--border-color)',
        backgroundColor: 'var(--bg-surface)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Top utility bar */}
      <div
        className="nb-container"
        style={{
          paddingTop: '0.85rem',
          paddingBottom: '0.85rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              backgroundColor: 'var(--accent-yellow)',
              border: 'var(--border-width) solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              boxShadow: 'var(--shadow-sm)',
              display: 'grid',
              placeContent: 'center',
            }}
          >
            <Zap size={24} strokeWidth={2.8} color="#121316" fill="#121316" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '1.45rem',
                  fontWeight: 900,
                  letterSpacing: '-0.03em',
                  color: 'var(--text-main)',
                }}
              >
                ZIPFORGE
              </span>
              <span className="nb-badge nb-badge-yellow" style={{ fontSize: '0.7rem' }}>
                v2.0
              </span>
            </div>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.7rem',
                color: 'var(--text-muted)',
                fontWeight: 600,
              }}
            >
              MULTI-ENGINE COMPRESSION SUITE
            </span>
          </div>
        </div>

        {/* Actions & Theme */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {isOnline !== null && (
            <div
              className={`nb-badge ${isOnline ? 'nb-badge-mint' : 'nb-badge-red'}`}
              style={{ fontSize: '0.72rem' }}
              title={isOnline ? 'Backend API connected' : 'Backend API unreachable'}
            >
              <Activity size={12} strokeWidth={3} />
              {isOnline ? 'API READY' : 'API OFFLINE'}
            </div>
          )}

          <button
            onClick={() => setIsInfoOpen(true)}
            className="nb-btn nb-btn-secondary nb-btn-sm"
            title="Algorithm Architecture & Details"
            style={{ padding: '0.45rem 0.75rem' }}
          >
            <HelpCircle size={16} strokeWidth={2.5} />
            <span style={{ fontSize: '0.8rem', fontWeight: 700 }}>ENGINES</span>
          </button>

          <ThemeToggle />
        </div>
      </div>

      {/* Navigation tabs */}
      <nav
        style={{
          borderTop: '1.5px solid var(--border-color)',
          backgroundColor: 'var(--bg-surface-subtle)',
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <div
          className="nb-container"
          style={{
            paddingTop: '0.35rem',
            paddingBottom: '0.35rem',
            display: 'flex',
            gap: '0.5rem',
          }}
        >
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`nb-btn nb-btn-sm ${isActive ? 'nb-btn-primary' : 'nb-btn-secondary'}`}
                style={{
                  boxShadow: isActive ? 'var(--shadow-md)' : 'none',
                  transform: isActive ? 'translate(-1px, -1px)' : 'none',
                  borderWidth: isActive ? 'var(--border-width)' : '1.5px',
                  fontWeight: isActive ? 800 : 600,
                  fontSize: '0.82rem',
                }}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Info Modal */}
      <Modal
        isOpen={isInfoOpen}
        onClose={() => setIsInfoOpen(false)}
        title="⚡ ZipForge Compression Engine Architecture"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="nb-card nb-card-accent-yellow">
            <h4 style={{ margin: '0 0 0.35rem 0' }}>🟩 Huffman Coding</h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
              Builds an optimal prefix tree by frequency analysis, mapping high-probability bytes to ultra-short bit codes. Guaranteed to reach the theoretical entropy limit.
            </p>
          </div>

          <div className="nb-card nb-card-accent-coral">
            <h4 style={{ margin: '0 0 0.35rem 0' }}>🟨 Lempel-Ziv-Welch (LZW)</h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
              Dynamic sliding phrase-dictionary engine. Emits variable-width bit codes (9 to 16 bits), automatically rebuilding dictionaries upon overflow (64K max phrases).
            </p>
          </div>

          <div className="nb-card nb-card-accent-mint">
            <h4 style={{ margin: '0 0 0.35rem 0' }}>🟦 Run-Length Encoding (RLE)</h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
              Identifies continuous repeated byte patterns and encodes them as compact <em>(escape, run-length, byte)</em> triplets.
            </p>
          </div>

          <div className="nb-card nb-card-accent-cyan">
            <h4 style={{ margin: '0 0 0.35rem 0' }}>🟥 STORE (Verbatim Pass-Through)</h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
              Activated when input data is already high-entropy (e.g. JPEG, MP4, pre-compressed files) to avoid data inflation, backed by full SHA-256 integrity verification.
            </p>
          </div>
        </div>
      </Modal>
    </header>
  );
};
