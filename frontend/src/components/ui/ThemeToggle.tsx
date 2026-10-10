import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className="nb-btn nb-btn-secondary nb-btn-sm"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Current: ${isDark ? 'Dark' : 'Light'} Mode (Click to toggle)`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.45rem',
        padding: '0.45rem 0.85rem',
        backgroundColor: isDark ? 'var(--accent-yellow)' : 'var(--bg-surface-subtle)',
        color: isDark ? '#121316' : 'var(--text-main)',
      }}
    >
      {isDark ? (
        <>
          <Sun size={17} strokeWidth={2.5} />
          <span style={{ fontSize: '0.8rem', fontWeight: 800 }}>LIGHT</span>
        </>
      ) : (
        <>
          <Moon size={17} strokeWidth={2.5} />
          <span style={{ fontSize: '0.8rem', fontWeight: 800 }}>DARK</span>
        </>
      )}
    </button>
  );
};
