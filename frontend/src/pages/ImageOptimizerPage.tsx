import React, { useState } from 'react';
import confetti from 'canvas-confetti';
import {
  Sparkles,
  Download,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { FileDropzone } from '../components/ui/FileDropzone';
import { api } from '../utilities/api';
import { formatBytes, formatPercent } from '../utilities/formatters';
import type { ImageOptimizeResponse } from '../types';

export const ImageOptimizerPage: React.FC = () => {
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [mode, setMode] = useState<'profile' | 'target'>('profile');
  const [profileName, setProfileName] = useState('RECOMMENDED');
  const [outputFormat, setOutputFormat] = useState('Auto');
  const [preserveMetadata, setPreserveMetadata] = useState(false);
  const [targetKb, setTargetKb] = useState(150);
  const [targetFormat, setTargetFormat] = useState<'JPEG' | 'WEBP'>('JPEG');

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ImageOptimizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedFile = imageFiles[0] || null;

  const handleOptimize = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('mode', mode);

    if (mode === 'profile') {
      formData.append('profile_name', profileName);
      formData.append('output_format', outputFormat);
      formData.append('preserve_metadata', preserveMetadata ? 'true' : 'false');
    } else {
      formData.append('target_size_bytes', String(Math.floor(targetKb * 1024)));
      formData.append('output_format', targetFormat);
    }

    try {
      const res = await api.optimizeImage(formData);
      setResult(res);
      try {
        confetti({ particleCount: 40, spread: 50, origin: { y: 0.7 } });
      } catch {}
    } catch (err: any) {
      setError(err.message || 'Image optimization failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
          <h1 style={{ fontSize: '2rem', margin: 0 }}>🖼️ Dedicated Image Optimizer</h1>
          <span className="nb-badge nb-badge-coral nb-badge-pill">WEBP · JPEG · PNG</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
          Profile-based quantization and binary-search target-size budgeting for high-performance web images.
        </p>
      </div>

      {/* Upload */}
      <Card title="1. Select Image" badge={<span className="nb-badge nb-badge-yellow">IMAGE INPUT</span>}>
        <FileDropzone
          files={imageFiles}
          onFilesChange={(files) => {
            setImageFiles(files.slice(-1));
            setResult(null);
            setError(null);
          }}
          multiple={false}
          accept="image/jpeg,image/png,image/webp,image/bmp"
          title="DROP IMAGE HERE (JPEG, PNG, WEBP, BMP)"
          subtitle="Transparency preserved automatically for RGBA PNGs and WebP images"
        />
      </Card>

      {/* Settings */}
      {selectedFile && (
        <Card title="2. Optimization Configuration" badge={<span className="nb-badge nb-badge-gray">TUNING</span>}>
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <button
              onClick={() => setMode('profile')}
              className={`nb-btn nb-btn-sm ${mode === 'profile' ? 'nb-btn-primary' : 'nb-btn-secondary'}`}
              style={{ fontWeight: 800 }}
            >
              🎨 PROFILE MODE
            </button>
            <button
              onClick={() => setMode('target')}
              className={`nb-btn nb-btn-sm ${mode === 'target' ? 'nb-btn-primary' : 'nb-btn-secondary'}`}
              style={{ fontWeight: 800 }}
            >
              🎯 TARGET SIZE BUDGET
            </button>
          </div>

          {mode === 'profile' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div>
                <label className="nb-label">Quality Profile</label>
                <select
                  className="nb-select"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                >
                  <option value="RECOMMENDED">RECOMMENDED (Balanced Web Quality)</option>
                  <option value="EXTREME">EXTREME (Maximum Compression)</option>
                  <option value="LESS_COMPRESSION">LESS COMPRESSION (Ultra High Fidelity)</option>
                </select>
              </div>

              <div>
                <label className="nb-label">Output Format</label>
                <select
                  className="nb-select"
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                >
                  <option value="Auto">Auto (Keep Original Format)</option>
                  <option value="WEBP">WebP (Modern Compact)</option>
                  <option value="JPEG">JPEG (Universal)</option>
                  <option value="PNG">PNG (Lossless Transparency)</option>
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', marginTop: '1.6rem' }}>
                <label className="nb-checkbox-label">
                  <input
                    type="checkbox"
                    className="nb-checkbox"
                    checked={preserveMetadata}
                    onChange={(e) => setPreserveMetadata(e.target.checked)}
                  />
                  <span>Preserve EXIF Metadata</span>
                </label>
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div>
                <label className="nb-label">Target Size Budget (KB)</label>
                <input
                  type="number"
                  className="nb-input"
                  min={1}
                  max={20000}
                  value={targetKb}
                  onChange={(e) => setTargetKb(Number(e.target.value))}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Binary search will calculate maximum quality under {targetKb} KB.
                </span>
              </div>

              <div>
                <label className="nb-label">Re-encode Format</label>
                <select
                  className="nb-select"
                  value={targetFormat}
                  onChange={(e) => setTargetFormat(e.target.value as 'JPEG' | 'WEBP')}
                >
                  <option value="JPEG">JPEG</option>
                  <option value="WEBP">WebP</option>
                </select>
              </div>
            </div>
          )}

          <div style={{ marginTop: '1.5rem' }}>
            <Button
              variant="coral"
              size="lg"
              onClick={handleOptimize}
              isLoading={isLoading}
              disabled={isLoading}
              icon={<Sparkles size={20} strokeWidth={2.5} />}
              style={{ width: '100%' }}
            >
              {isLoading ? 'OPTIMIZING IMAGE PAYLOAD…' : '✨ OPTIMIZE IMAGE NOW'}
            </Button>
          </div>

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
                <span>Optimization Failed</span>
              </div>
              <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.85rem' }}>{error}</p>
            </div>
          )}
        </Card>
      )}

      {/* Results */}
      {result && (
        <Card
          title="3. Optimized Output & Side-by-Side Comparison"
          badge={<span className="nb-badge nb-badge-mint">DONE</span>}
          accent="mint"
        >
          {result.target_status && (
            <div style={{ marginBottom: '1.25rem' }}>
              {result.target_status === 'ACHIEVED' ? (
                <div
                  className="nb-card"
                  style={{
                    backgroundColor: 'rgba(0, 229, 153, 0.15)',
                    borderColor: 'var(--accent-mint)',
                    padding: '0.85rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <CheckCircle2 size={20} color="var(--accent-mint)" strokeWidth={2.8} />
                  <span>
                    <strong>Target Achieved:</strong> Final size of {formatBytes(result.final_size)} is within requested {targetKb} KB budget in {result.iterations} iterations!
                  </span>
                </div>
              ) : (
                <div
                  className="nb-card"
                  style={{
                    backgroundColor: 'rgba(255, 230, 0, 0.15)',
                    borderColor: 'var(--accent-yellow)',
                    padding: '0.85rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <AlertTriangle size={20} strokeWidth={2.8} />
                  <span>
                    <strong>Target Unachievable:</strong> Smallest possible high-fidelity result generated.
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Metrics */}
          <div className="nb-metric-grid">
            <MetricCard
              value={formatBytes(result.original_size)}
              label="ORIGINAL FILE"
            />
            <MetricCard
              value={formatBytes(result.final_size)}
              label="OPTIMIZED FILE"
              delta={`-${formatPercent(result.reduction_percent)}`}
              deltaType="positive"
              accent="mint"
            />
            <MetricCard
              value={formatPercent(result.reduction_percent)}
              label="REDUCTION"
              accent="yellow"
            />
            <MetricCard
              value={result.quality ? `${result.quality}/100` : 'Auto'}
              label="QUALITY SETTING"
            />
          </div>

          {/* Side-by-Side Preview */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem', marginTop: '1.5rem' }}>
            <div className="nb-card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span className="nb-badge nb-badge-gray">ORIGINAL</span>
                <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                  {result.dimensions.original.width} × {result.dimensions.original.height} px
                </span>
              </div>
              <div style={{ border: 'var(--border-width) solid var(--border-color)', borderRadius: 'var(--radius-xs)', overflow: 'hidden', maxHeight: '360px', display: 'grid', placeContent: 'center', backgroundColor: '#000000' }}>
                <img
                  src={result.original_preview}
                  alt="Original"
                  style={{ maxWidth: '100%', maxHeight: '360px', objectFit: 'contain' }}
                />
              </div>
            </div>

            <div className="nb-card nb-card-accent-mint" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span className="nb-badge nb-badge-mint">OPTIMIZED ({result.output_format})</span>
                <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                  {result.dimensions.optimized.width} × {result.dimensions.optimized.height} px
                </span>
              </div>
              <div style={{ border: 'var(--border-width) solid var(--border-color)', borderRadius: 'var(--radius-xs)', overflow: 'hidden', maxHeight: '360px', display: 'grid', placeContent: 'center', backgroundColor: '#000000' }}>
                <img
                  src={result.optimized_preview}
                  alt="Optimized"
                  style={{ maxWidth: '100%', maxHeight: '360px', objectFit: 'contain' }}
                />
              </div>
            </div>
          </div>

          {/* Download button */}
          <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            <a
              href={api.getDownloadImageUrl(result.job_id)}
              download={result.download_filename}
              className="nb-btn nb-btn-primary nb-btn-lg"
              style={{ display: 'inline-flex' }}
            >
              <Download size={22} strokeWidth={2.8} />
              DOWNLOAD OPTIMIZED IMAGE ({formatBytes(result.final_size)})
            </a>
          </div>
        </Card>
      )}
    </div>
  );
};
