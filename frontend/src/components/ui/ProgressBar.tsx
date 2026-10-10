import React from 'react';

export interface ProgressBarProps {
  progress: number; // 0 to 100
  label?: string;
  statusText?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label = 'Processing…',
  statusText,
}) => {
  const clamped = Math.min(100, Math.max(0, progress));

  return (
    <div className="nb-progress-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', fontWeight: 700 }}>
        <span>{label}</span>
        <span>{clamped.toFixed(0)}%</span>
      </div>
      <div className="nb-progress-track">
        <div
          className="nb-progress-fill"
          style={{ width: `${clamped}%` }}
        />
      </div>
      {statusText && (
        <div style={{ marginTop: '0.35rem', fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {statusText}
        </div>
      )}
    </div>
  );
};
