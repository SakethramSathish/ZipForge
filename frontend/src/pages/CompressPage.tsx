import React, { useState } from 'react';
import confetti from 'canvas-confetti';
import {
  Zap,
  Target,
  Download,
  FileArchive,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { ProgressBar } from '../components/ui/ProgressBar';
import { FileDropzone } from '../components/ui/FileDropzone';
import { api } from '../utilities/api';
import {
  formatBytes,
  formatPercent,
  formatRatio,
  formatMs,
  formatSeconds,
} from '../utilities/formatters';
import type {
  CompressionLevel,
  CompressionResponse,
  AlgorithmType,
} from '../types';

export const CompressPage: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [level, setLevel] = useState<CompressionLevel>('RECOMMENDED');
  const [useTargetSize, setUseTargetSize] = useState(false);
  const [targetSizeVal, setTargetSizeVal] = useState(500);
  const [targetSizeUnit, setTargetSizeUnit] = useState<'KB' | 'MB'>('KB');
  const [archiveName, setArchiveName] = useState('archive');
  const [overrideAlgo, setOverrideAlgo] = useState<AlgorithmType | ''>('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Compressing…');
  const [result, setResult] = useState<CompressionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const levels: { id: CompressionLevel; title: string; desc: string; badge: string; accent: 'coral' | 'yellow' | 'mint' }[] = [
    {
      id: 'EXTREME',
      title: 'EXTREME COMPRESSION',
      desc: 'Deep multi-engine evaluation. Maximum size reduction.',
      badge: 'MAX REDUCTION',
      accent: 'coral',
    },
    {
      id: 'RECOMMENDED',
      title: 'RECOMMENDED BALANCED',
      desc: 'Optimal tradeoff between speed and compression ratio.',
      badge: 'OPTIMAL',
      accent: 'yellow',
    },
    {
      id: 'LESS',
      title: 'STORE (ZERO COMPRESSION)',
      desc: 'Verbatim storage with full SHA-256 cryptographic hashes.',
      badge: 'PASSTHROUGH',
      accent: 'mint',
    },
  ];

  const handleCompress = async () => {
    if (files.length === 0) return;
    setIsLoading(true);
    setProgress(15);
    setProgressLabel('Evaluating file payloads…');
    setError(null);
    setResult(null);

    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    formData.append('level', level);
    if (overrideAlgo) {
      formData.append('algorithm', overrideAlgo);
    }
    formData.append('archive_name', archiveName);
    formData.append('use_target_size', useTargetSize ? 'true' : 'false');
    if (useTargetSize) {
      const multiplier = targetSizeUnit === 'KB' ? 1024 : 1024 * 1024;
      formData.append('target_size_bytes', String(Math.floor(targetSizeVal * multiplier)));
    }

    try {
      setProgress(45);
      setProgressLabel('Running compression engines (Huffman / LZW / RLE)…');
      const res = await api.compress(formData);
      setProgress(100);
      setProgressLabel('Compression complete!');
      setResult(res);

      // Trigger celebratory confetti on reduction
      try {
        confetti({
          particleCount: 50,
          spread: 60,
          origin: { y: 0.7 },
        });
      } catch {
        // ignore if not supported
      }
    } catch (err: any) {
      setError(err.message || 'Compression failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Page Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
          <h1 style={{ fontSize: '2rem', margin: 0 }}>🗜️ Multi-Engine Compression</h1>
          <span className="nb-badge nb-badge-yellow nb-badge-pill">UNIVERSAL .ZIP READY</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
          Compress files using auto-selected algorithmic engines or target an exact file size budget.
        </p>
      </div>

      {/* File Upload Zone */}
      <Card title="1. Select Files" badge={<span className="nb-badge nb-badge-gray">STEP 1</span>}>
        <FileDropzone
          files={files}
          onFilesChange={(newFiles) => {
            setFiles(newFiles);
            setResult(null);
          }}
          title="DROP FILES TO COMPRESS"
          subtitle="Supports text, binary, images, audio, PDF, source code, and documents"
        />
      </Card>

      {/* Compression Level & Configuration */}
      <Card title="2. Compression Strategy" badge={<span className="nb-badge nb-badge-gray">STEP 2</span>}>
        <label className="nb-label">Choose Optimization Profile</label>
        <div className="nb-level-grid">
          {levels.map((lvl) => {
            const isSelected = level === lvl.id && !overrideAlgo;
            return (
              <div
                key={lvl.id}
                onClick={() => {
                  setLevel(lvl.id);
                  setOverrideAlgo('');
                }}
                className={`nb-level-card ${isSelected ? 'selected' : ''}`}
                style={{
                  borderTop: `6px solid var(--accent-${lvl.accent})`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '0.85rem' }}>
                    {lvl.title}
                  </span>
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>{lvl.desc}</p>
                <div style={{ marginTop: '0.6rem' }}>
                  <span className={`nb-badge nb-badge-${lvl.accent}`}>{lvl.badge}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Advanced Target Size & Engine Controls */}
        <div style={{ borderTop: '1.5px solid var(--border-color)', paddingTop: '1.25rem', marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Target Size Mode */}
          <div
            style={{
              padding: '1rem',
              backgroundColor: useTargetSize ? 'var(--bg-card-hover)' : 'var(--bg-surface-subtle)',
              border: 'var(--border-width) solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <label className="nb-checkbox-label" style={{ marginBottom: useTargetSize ? '0.75rem' : 0 }}>
              <input
                type="checkbox"
                className="nb-checkbox"
                checked={useTargetSize}
                onChange={(e) => setUseTargetSize(e.target.checked)}
              />
              <span>🎯 Enable Target-Size Budgeting Mode</span>
            </label>

            {useTargetSize && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                <div style={{ flex: '1 1 200px' }}>
                  <label className="nb-label">Max Target Size</label>
                  <input
                    type="number"
                    className="nb-input"
                    min={1}
                    max={50000}
                    value={targetSizeVal}
                    onChange={(e) => setTargetSizeVal(Number(e.target.value))}
                  />
                </div>
                <div style={{ width: '110px' }}>
                  <label className="nb-label">Unit</label>
                  <select
                    className="nb-select"
                    value={targetSizeUnit}
                    onChange={(e) => setTargetSizeUnit(e.target.value as 'KB' | 'MB')}
                  >
                    <option value="KB">KB</option>
                    <option value="MB">MB</option>
                  </select>
                </div>
                <div style={{ flex: '1 1 200px' }}>
                  <span className="nb-badge nb-badge-yellow" style={{ display: 'inline-block', marginTop: '1.6rem' }}>
                    GUARANTEE: &le; {targetSizeVal} {targetSizeUnit}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Archive Name & Explicit Engine Override */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            <div>
              <label className="nb-label">Output Archive Name</label>
              <input
                type="text"
                className="nb-input"
                value={archiveName}
                placeholder="archive"
                onChange={(e) => setArchiveName(e.target.value)}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Will produce {archiveName || 'archive'}.zip
              </span>
            </div>

            <div>
              <label className="nb-label">Explicit Engine Override (Optional)</label>
              <select
                className="nb-select"
                value={overrideAlgo}
                onChange={(e) => setOverrideAlgo(e.target.value as AlgorithmType | '')}
              >
                <option value="">Auto-Selected by Strategy</option>
                <option value="HUFFMAN">Force Huffman Coding (Optimal Prefix Tree)</option>
                <option value="LZW">Force LZW (Dynamic Dictionary)</option>
                <option value="RLE">Force RLE (Run-Length Tokenizer)</option>
                <option value="STORE">Force STORE (Verbatim Pass-Through)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div style={{ marginTop: '1.5rem' }}>
          <Button
            variant="primary"
            size="lg"
            onClick={handleCompress}
            disabled={files.length === 0 || isLoading}
            isLoading={isLoading}
            icon={<Zap size={20} strokeWidth={2.8} />}
            style={{ width: '100%' }}
          >
            {isLoading ? 'EXECUTING COMPRESSION…' : '🚀 COMPRESS FILES NOW'}
          </Button>
        </div>

        {isLoading && (
          <div style={{ marginTop: '1.25rem' }}>
            <ProgressBar progress={progress} label={progressLabel} />
          </div>
        )}

        {error && (
          <div
            className="nb-card"
            style={{
              borderColor: 'var(--accent-red)',
              backgroundColor: 'rgba(255, 59, 48, 0.1)',
              marginTop: '1.25rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-red)', fontWeight: 700 }}>
              <AlertTriangle size={18} strokeWidth={2.5} />
              <span>Compression Failed</span>
            </div>
            <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.85rem' }}>{error}</p>
          </div>
        )}
      </Card>

      {/* Results Section */}
      {result && (
        <Card
          title="3. Compression Results & Downloads"
          badge={<span className="nb-badge nb-badge-mint">SUCCESS</span>}
          accent="yellow"
        >
          {/* Target Status Banner */}
          {result.target_status && (
            <div style={{ marginBottom: '1.25rem' }}>
              {result.target_status === 'ACHIEVED' && (
                <div
                  className="nb-card"
                  style={{
                    backgroundColor: 'rgba(0, 229, 153, 0.15)',
                    border: 'var(--border-width) solid var(--accent-mint)',
                    padding: '0.85rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <CheckCircle2 size={20} color="var(--accent-mint)" strokeWidth={2.8} />
                  <div>
                    <strong style={{ color: 'var(--accent-mint)' }}>Target Budget Achieved (Lossless)!</strong>
                    <p style={{ margin: 0, fontSize: '0.82rem' }}>All files fit within your requested size constraint with zero loss.</p>
                  </div>
                </div>
              )}
              {result.target_status === 'ACHIEVED_LOSSY' && (
                <div
                  className="nb-card"
                  style={{
                    backgroundColor: 'rgba(255, 230, 0, 0.15)',
                    border: 'var(--border-width) solid var(--accent-yellow)',
                    padding: '0.85rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <AlertTriangle size={20} color="#E6B800" strokeWidth={2.8} />
                  <div>
                    <strong>Target Met with Quality Reduction:</strong>
                    <p style={{ margin: 0, fontSize: '0.82rem' }}>
                      Images were re-encoded at calibrated quality to satisfy your target size budget.
                    </p>
                  </div>
                </div>
              )}
              {result.target_status === 'BEST_EFFORT' && (
                <div
                  className="nb-card"
                  style={{
                    backgroundColor: 'rgba(255, 90, 54, 0.15)',
                    border: 'var(--border-width) solid var(--accent-coral)',
                    padding: '0.85rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <XCircle size={20} color="var(--accent-coral)" strokeWidth={2.8} />
                  <div>
                    <strong style={{ color: 'var(--accent-coral)' }}>Target Unachievable:</strong>
                    <p style={{ margin: 0, fontSize: '0.82rem' }}>
                      Input data is already high-entropy. Showing smallest possible lossless output.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Metrics Row */}
          <div className="nb-metric-grid">
            <MetricCard
              value={formatBytes(result.total_input)}
              label="ORIGINAL PAYLOAD"
              icon={<FileText size={24} />}
            />
            <MetricCard
              value={formatBytes(result.total_compressed)}
              label="COMPRESSED ARCHIVE"
              delta={result.reduction_percent > 0 ? `-${formatPercent(result.reduction_percent)}` : '0%'}
              deltaType={result.reduction_percent > 0 ? 'positive' : 'neutral'}
              icon={<FileArchive size={24} />}
              accent="yellow"
            />
            <MetricCard
              value={formatPercent(result.reduction_percent)}
              label="SPACE SAVED"
              delta={`${formatRatio(result.compression_ratio)} RATIO`}
              deltaType="positive"
              icon={<Target size={24} />}
              accent="mint"
            />
            <MetricCard
              value={formatSeconds(result.elapsed_seconds)}
              label="EXECUTION TIME"
              icon={<Zap size={24} />}
            />
          </div>

          {/* Per-File Breakdown Table */}
          <h4 style={{ margin: '1.5rem 0 0.5rem 0' }}>📋 Per-File Algorithmic Breakdown</h4>
          <div className="nb-table-wrapper">
            <table className="nb-table">
              <thead>
                <tr>
                  <th>FILE NAME</th>
                  <th>ENGINE SELECTED</th>
                  <th>ORIGINAL</th>
                  <th>COMPRESSED</th>
                  <th>SAVINGS</th>
                  <th>RATIO</th>
                  <th>TIME</th>
                </tr>
              </thead>
              <tbody>
                {result.files.map((file, i) => (
                  <tr key={i}>
                    <td>
                      <code style={{ fontWeight: 700 }}>{file.name}</code>
                    </td>
                    <td>
                      <span className="nb-badge nb-badge-yellow">{file.algorithm}</span>
                    </td>
                    <td>{formatBytes(file.original_size)}</td>
                    <td>{formatBytes(file.compressed_size)}</td>
                    <td>
                      <span
                        style={{
                          color: file.reduction_percent > 0 ? 'var(--accent-mint)' : 'var(--text-muted)',
                          fontWeight: 700,
                        }}
                      >
                        {formatPercent(file.reduction_percent)}
                      </span>
                    </td>
                    <td>{formatRatio(file.compression_ratio)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{formatMs(file.duration_ms)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Downloads Section */}
          <div style={{ marginTop: '1.75rem', borderTop: '2px solid var(--border-color)', paddingTop: '1.5rem' }}>
            <h4 style={{ margin: '0 0 1rem 0' }}>⬇️ Download Artifacts</h4>

            {result.is_single_file && result.single_file_name ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                {/* Direct same-extension download */}
                <div className="nb-card nb-card-accent-mint" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <span className="nb-badge nb-badge-mint" style={{ alignSelf: 'flex-start' }}>
                    DIRECT SAME-EXTENSION DOWNLOAD
                  </span>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                    Download single file directly with its native extension (no unzip required).
                  </p>
                  <a
                    href={api.getDownloadProcessedFileUrl(result.job_id, 0)}
                    download={result.single_file_name}
                    className="nb-btn nb-btn-mint"
                    style={{ marginTop: 'auto' }}
                  >
                    <Download size={18} strokeWidth={2.5} />
                    Download {result.single_file_name}
                  </a>
                </div>

                {/* Universal .zip download */}
                <div className="nb-card nb-card-accent-yellow" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <span className="nb-badge nb-badge-yellow" style={{ alignSelf: 'flex-start' }}>
                    UNIVERSAL .ZIP ARCHIVE
                  </span>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                    Standard ZIP archive entry compatible with Windows Explorer, 7-Zip, and macOS.
                  </p>
                  <a
                    href={api.getDownloadArchiveUrl(result.job_id)}
                    download={result.archive_name}
                    className="nb-btn nb-btn-primary"
                    style={{ marginTop: 'auto' }}
                  >
                    <FileArchive size={18} strokeWidth={2.5} />
                    Download as {result.archive_name} ({formatBytes(result.total_compressed)})
                  </a>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <a
                  href={api.getDownloadArchiveUrl(result.job_id)}
                  download={result.archive_name}
                  className="nb-btn nb-btn-primary nb-btn-lg"
                  style={{ alignSelf: 'flex-start' }}
                >
                  <FileArchive size={22} strokeWidth={2.5} />
                  Download Complete Universal Archive: {result.archive_name} ({formatBytes(result.total_compressed)})
                </a>

                <div>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                    OR DOWNLOAD INDIVIDUAL PROCESSED FILES:
                  </h5>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {result.files.map((file, idx) => (
                      <a
                        key={idx}
                        href={api.getDownloadProcessedFileUrl(result.job_id, idx)}
                        download={file.name}
                        className="nb-btn nb-btn-secondary nb-btn-sm"
                      >
                        <Download size={14} strokeWidth={2.5} />
                        {file.name} ({formatBytes(file.compressed_size)})
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
