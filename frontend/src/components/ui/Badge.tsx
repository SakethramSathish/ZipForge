import React from 'react';

export interface BadgeProps {
  variant?: 'yellow' | 'coral' | 'mint' | 'cyan' | 'purple' | 'gray' | 'red';
  pill?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'yellow',
  pill = false,
  icon,
  children,
  className = '',
}) => {
  const variantClass = {
    yellow: 'nb-badge-yellow',
    coral: 'nb-badge-coral',
    mint: 'nb-badge-mint',
    cyan: 'nb-badge-cyan',
    purple: 'nb-badge-purple',
    gray: 'nb-badge-gray',
    red: 'nb-badge-red',
  }[variant];

  const pillClass = pill ? 'nb-badge-pill' : '';

  return (
    <span className={`nb-badge ${variantClass} ${pillClass} ${className}`}>
      {icon && <span className="mr-1">{icon}</span>}
      {children}
    </span>
  );
};
