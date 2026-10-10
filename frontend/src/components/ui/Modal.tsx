import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  maxWidth?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = '680px',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
        display: 'grid',
        placeItems: 'center',
        zIndex: 9990,
        padding: '1rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="nb-card"
        style={{
          width: '100%',
          maxWidth,
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: 'var(--shadow-xl)',
          backgroundColor: 'var(--bg-surface)',
          padding: '1.75rem',
          position: 'relative',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: 'var(--border-width) solid var(--border-color)',
            paddingBottom: '0.85rem',
            marginBottom: '1.25rem',
          }}
        >
          <h2 style={{ fontSize: '1.35rem', margin: 0 }}>{title}</h2>
          <button
            onClick={onClose}
            className="nb-btn nb-btn-secondary nb-btn-sm"
            style={{ padding: '0.35rem' }}
            aria-label="Close dialog"
          >
            <X size={18} strokeWidth={2.5} />
          </button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
};
