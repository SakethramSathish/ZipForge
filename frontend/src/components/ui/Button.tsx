import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'coral' | 'mint' | 'cyan' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  icon,
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const variantClass = {
    primary: 'nb-btn-primary',
    secondary: 'nb-btn-secondary',
    coral: 'nb-btn-coral',
    mint: 'nb-btn-mint',
    cyan: 'nb-btn-cyan',
    danger: 'nb-btn-danger',
  }[variant];

  const sizeClass = {
    sm: 'nb-btn-sm',
    md: '',
    lg: 'nb-btn-lg',
  }[size];

  return (
    <button
      className={`nb-btn ${variantClass} ${sizeClass} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="animate-spin mr-1">⏳</span>
      ) : (
        icon && <span className="nb-btn-icon-wrap">{icon}</span>
      )}
      {children}
    </button>
  );
};
