import React from 'react';

export interface MetricCardProps {
  value: string | number;
  label: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
  accent?: 'yellow' | 'coral' | 'mint' | 'cyan';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  value,
  label,
  delta,
  deltaType = 'neutral',
  icon,
  accent,
  className = '',
}) => {
  const accentBorder = accent ? `nb-card-accent-${accent}` : '';

  return (
    <div className={`nb-metric-card ${accentBorder} ${className}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span className="nb-metric-val">{value}</span>
        {icon && <div style={{ fontSize: '1.4rem' }}>{icon}</div>}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.4rem' }}>
        <span className="nb-metric-label">{label}</span>
        {delta && (
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              fontWeight: 700,
              color:
                deltaType === 'positive'
                  ? 'var(--accent-mint)'
                  : deltaType === 'negative'
                  ? 'var(--accent-red)'
                  : 'var(--text-muted)',
            }}
          >
            {delta}
          </span>
        )}
      </div>
    </div>
  );
};
