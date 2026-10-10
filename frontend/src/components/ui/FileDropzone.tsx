import React, { useRef, useState } from 'react';
import { Upload, File as FileIcon, X } from 'lucide-react';
import { formatBytes } from '../../utilities/formatters';

export interface FileDropzoneProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  title?: string;
  subtitle?: string;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  files,
  onFilesChange,
  accept,
  multiple = true,
  title = 'DROP FILES HERE OR CLICK TO BROWSE',
  subtitle = 'Supports all standard file types up to 100MB per file',
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      if (multiple) {
        onFilesChange([...files, ...droppedFiles]);
      } else {
        onFilesChange([droppedFiles[0]]);
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = Array.from(e.target.files);
      if (multiple) {
        onFilesChange([...files, ...selected]);
      } else {
        onFilesChange([selected[0]]);
      }
    }
    // reset input so same file can be selected again if needed
    if (inputRef.current) inputRef.current.value = '';
  };

  const removeFile = (idx: number) => {
    const updated = files.filter((_, i) => i !== idx);
    onFilesChange(updated);
  };

  const clearAll = () => {
    onFilesChange([]);
  };

  return (
    <div>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border: '3px dashed var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: isDragOver ? 'var(--accent-yellow)' : 'var(--bg-surface-subtle)',
          padding: '2.5rem 1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
          boxShadow: isDragOver ? 'var(--shadow-lg)' : 'var(--shadow-sm)',
          transform: isDragOver ? 'translate(-2px, -2px)' : 'none',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          style={{ display: 'none' }}
          onChange={handleFileInput}
        />
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              backgroundColor: 'var(--bg-surface)',
              border: 'var(--border-width) solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              boxShadow: 'var(--shadow-sm)',
              display: 'grid',
              placeContent: 'center',
            }}
          >
            <Upload size={28} strokeWidth={2.5} color="var(--text-main)" />
          </div>
          <h4 style={{ fontSize: '1.1rem', margin: 0 }}>{title}</h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>{subtitle}</p>
          <span className="nb-badge nb-badge-yellow nb-badge-pill" style={{ marginTop: '0.25rem' }}>
            CLICK OR DRAG & DROP
          </span>
        </div>
      </div>

      {files.length > 0 && (
        <div style={{ marginTop: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700 }}>
              SELECTED ({files.length} {files.length === 1 ? 'FILE' : 'FILES'} · {formatBytes(files.reduce((a, b) => a + b.size, 0))})
            </span>
            <button
              onClick={clearAll}
              className="nb-btn nb-btn-secondary nb-btn-sm"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
            >
              Clear All
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
            {files.map((file, idx) => (
              <div
                key={`${file.name}-${idx}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.5rem 0.85rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: 'var(--border-width) solid var(--border-color)',
                  borderRadius: 'var(--radius-xs)',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', overflow: 'hidden' }}>
                  <FileIcon size={18} strokeWidth={2.5} style={{ flexShrink: 0 }} />
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {file.name}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', flexShrink: 0 }}>
                    ({formatBytes(file.size)})
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="nb-btn nb-btn-danger nb-btn-sm"
                  style={{ padding: '0.2rem 0.4rem', border: '1.5px solid var(--border-color)' }}
                  aria-label="Remove file"
                >
                  <X size={14} strokeWidth={2.5} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
