import React from 'react';

export interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  badge?: React.ReactNode;
  accent?: 'yellow' | 'coral' | 'mint' | 'cyan';
  interactive?: boolean;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  badge,
  accent,
  interactive = false,
  headerAction,
  children,
  className = '',
}) => {
  const accentClass = accent ? `nb-card-accent-${accent}` : '';
  const interactiveClass = interactive ? 'nb-card-interactive' : '';

  return (
    <div className={`nb-card ${accentClass} ${interactiveClass} ${className}`}>
      {(title || badge || headerAction) && (
        <div className="nb-card-header">
          <div>
            {title && <h3 style={{ fontSize: '1.05rem', margin: 0 }}>{title}</h3>}
            {subtitle && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>{subtitle}</p>}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {badge}
            {headerAction}
          </div>
        </div>
      )}
      {children}
    </div>
  );
};
