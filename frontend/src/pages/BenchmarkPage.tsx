import React, { useState } from 'react';
import {
  Award,
  CheckCircle2,
  AlertTriangle,
  Play,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { FileDropzone } from '../components/ui/FileDropzone';
import { api } from '../utilities/api';
import {
  formatBytes,
  formatPercent,
  formatRatio,
  formatMs,
} from '../utilities/formatters';
import type { BenchmarkResponse } from '../types';

export const BenchmarkPage: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<BenchmarkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedFile = files[0] || null;

  // Preset sample generators for quick benchmarking
  const loadPreset = (type: 'text' | 'repetitive' | 'json') => {
    let content = '';
    let filename = '';
    if (type === 'text') {
      content = 'The quick brown fox jumps over the lazy dog. '.repeat(400);
      filename = 'sample_prose.txt';
    } else if (type === 'repetitive') {
      content = 'A'.repeat(8000) + 'B'.repeat(5000) + 'C'.repeat(3000);
      filename = 'repetitive_runs.txt';
    } else {
      content = JSON.stringify({
        project: 'ZipForge',
        version: '2.0.0',
        engines: ['Huffman', 'LZW', 'RLE', 'STORE'],
        metrics: Array.from({ length: 150 }, (_, i) => ({ id: i, score: (i * 7) % 100 })),
      }, null, 2);
      filename = 'structured_data.json';
    }
    const blob = new Blob([content], { type: 'text/plain' });
    const file = new File([blob], filename, { type: 'text/plain' });
    setFiles([file]);
    setResult(null);
  };

  const handleRun = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.runBenchmark(selectedFile);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Benchmark run failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
          <h1 style={{ fontSize: '2rem', margin: 0 }}>📊 Multi-Engine Algorithmic Benchmark</h1>
          <span className="nb-badge nb-badge-yellow nb-badge-pill">HEAD-TO-HEAD SPEED & RATIO</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
          Execute RLE, Huffman, LZW, and STORE in parallel against your input data with real cryptographic roundtrip verification.
        </p>
      </div>

      {/* Upload or Preset */}
      <Card title="1. Select Test Input Payload" badge={<span className="nb-badge nb-badge-gray">INPUT</span>}>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            QUICK PRESETS:
          </span>
          <button
            onClick={() => loadPreset('text')}
            className="nb-btn nb-btn-secondary nb-btn-sm"
          >
            📜 Natural Text (Huffman Favored)
          </button>
          <button
            onClick={() => loadPreset('repetitive')}
            className="nb-btn nb-btn-secondary nb-btn-sm"
          >
            🔁 Repetitive Sequences (RLE Favored)
          </button>
          <button
            onClick={() => loadPreset('json')}
            className="nb-btn nb-btn-secondary nb-btn-sm"
          >
            🌲 Structured JSON (LZW Favored)
          </button>
        </div>

        <FileDropzone
          files={files}
          onFilesChange={(newFiles) => {
            setFiles(newFiles.slice(-1));
            setResult(null);
          }}
          multiple={false}
          title="UPLOAD ANY FILE TO BENCHMARK"
          subtitle="Test arbitrary binaries, archives, source files, or graphics"
        />

        {selectedFile && (
          <div style={{ marginTop: '1.5rem' }}>
            <Button
              variant="primary"
              size="lg"
              onClick={handleRun}
              isLoading={isLoading}
              disabled={isLoading}
              icon={<Play size={20} strokeWidth={2.8} />}
              style={{ width: '100%' }}
            >
              {isLoading ? 'EXECUTING ENGINES & VERIFYING ROUNDTRIP…' : '🏁 RUN MULTI-ENGINE BENCHMARK NOW'}
            </Button>
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
              <span>Benchmark Execution Error</span>
            </div>
            <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.85rem' }}>{error}</p>
          </div>
        )}
      </Card>

      {/* Results */}
      {result && (
        <Card
          title="2. Head-to-Head Performance Matrix"
          badge={<span className="nb-badge nb-badge-mint">COMPLETED</span>}
          accent="yellow"
        >
          {/* Winner Banner */}
          <div
            className="nb-card nb-card-accent-yellow"
            style={{
              backgroundColor: 'var(--bg-card-hover)',
              padding: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div
                style={{
                  width: '46px',
                  height: '46px',
                  backgroundColor: 'var(--accent-yellow)',
                  border: 'var(--border-width) solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  display: 'grid',
                  placeContent: 'center',
                }}
              >
                <Award size={28} strokeWidth={2.5} color="#121316" />
              </div>
              <div>
                <span className="nb-badge nb-badge-yellow" style={{ marginBottom: '0.25rem' }}>
                  OPTIMAL ENGINE FOR THIS PAYLOAD
                </span>
                <h3 style={{ margin: 0, fontSize: '1.35rem' }}>
                  {result.best_algorithm} ENGINE
                </h3>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                SAMPLE: {result.filename} ({formatBytes(result.original_size)})
              </div>
            </div>
          </div>

          {/* Detailed Table */}
          <div className="nb-table-wrapper">
            <table className="nb-table">
              <thead>
                <tr>
                  <th>ALGORITHM</th>
                  <th>ORIGINAL</th>
                  <th>COMPRESSED</th>
                  <th>SAVINGS</th>
                  <th>RATIO</th>
                  <th>COMPRESS TIME</th>
                  <th>DECOMPRESS TIME</th>
                  <th>SPEED</th>
                  <th>VERIFIED</th>
                </tr>
              </thead>
              <tbody>
                {result.results.map((item, idx) => (
                  <tr
                    key={idx}
                    style={{
                      backgroundColor: item.is_best ? 'var(--bg-card-hover)' : undefined,
                      fontWeight: item.is_best ? 700 : 500,
                    }}
                  >
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        {item.is_best && <span>⭐</span>}
                        <span className={`nb-badge ${item.is_best ? 'nb-badge-yellow' : 'nb-badge-gray'}`}>
                          {item.algorithm}
                        </span>
                      </div>
                    </td>
                    <td>{formatBytes(item.original_size)}</td>
                    <td>{formatBytes(item.compressed_size)}</td>
                    <td>
                      <span
                        style={{
                          color: item.reduction_percent > 0 ? 'var(--accent-mint)' : 'var(--text-muted)',
                        }}
                      >
                        {formatPercent(item.reduction_percent)}
                      </span>
                    </td>
                    <td>{formatRatio(item.compression_ratio)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                      {formatMs(item.compress_duration_ms)}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                      {formatMs(item.decompress_duration_ms)}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                      {item.speed_kbps > 0 ? `${item.speed_kbps.toFixed(0)} KB/s` : 'N/A'}
                    </td>
                    <td>
                      {item.verified ? (
                        <span className="nb-badge nb-badge-mint">
                          <CheckCircle2 size={12} strokeWidth={3} />
                          PASS
                        </span>
                      ) : (
                        <span className="nb-badge nb-badge-red">FAIL</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Visual bar graph representation */}
          <h4 style={{ margin: '1.5rem 0 0.75rem 0' }}>📈 Visual Compression Efficiency Comparison</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {result.results.map((item, idx) => {
              const pct = Math.max(0, item.reduction_percent);
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', fontFamily: 'var(--font-mono)', marginBottom: '0.25rem' }}>
                    <span>{item.algorithm}</span>
                    <span>{formatPercent(pct)} space saved</span>
                  </div>
                  <div
                    style={{
                      height: '24px',
                      backgroundColor: 'var(--bg-surface-subtle)',
                      border: 'var(--border-width) solid var(--border-color)',
                      borderRadius: 'var(--radius-xs)',
                      overflow: 'hidden',
                      position: 'relative',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${pct}%`,
                        backgroundColor: item.is_best ? 'var(--accent-yellow)' : 'var(--accent-cyan)',
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
};
