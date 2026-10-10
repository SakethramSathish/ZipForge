import { useState } from 'react';
import {
  Search,
  FileArchive,
  CheckCircle2,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { FileDropzone } from '../components/ui/FileDropzone';
import { api } from '../utilities/api';
import { formatBytes, formatPercent } from '../utilities/formatters';
import type { InspectResponse, ArchiveEntry } from '../types';

export const InspectPage: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<InspectResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const archiveFile = files[0] || null;

  const handleInspect = async () => {
    if (!archiveFile) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.inspectArchive(archiveFile);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Inspection failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
          <h1 style={{ fontSize: '2rem', margin: 0 }}>🔍 Zero-Extraction Archive Inspector</h1>
          <span className="nb-badge nb-badge-cyan nb-badge-pill">HEADER & INTEGRITY PARSER</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
          Inspect internal archive layout, file manifests, compression engines, and cryptographic SHA-256 checksums without writing to disk.
        </p>
      </div>

      {/* Upload */}
      <Card title="Upload Archive to Inspect" badge={<span className="nb-badge nb-badge-yellow">ZIP INPUT</span>}>
        <FileDropzone
          files={files}
          onFilesChange={(newFiles) => {
            setFiles(newFiles.slice(-1));
            setResult(null);
            setError(null);
          }}
          multiple={false}
          accept=".zip"
          title="DROP .ZIP ARCHIVE HERE FOR DEEP INSPECTION"
          subtitle="Directly parses local file headers and central directory records"
        />

        {archiveFile && (
          <div style={{ marginTop: '1.5rem' }}>
            <Button
              variant="cyan"
              size="lg"
              onClick={handleInspect}
              isLoading={isLoading}
              disabled={isLoading}
              icon={<Search size={20} strokeWidth={2.8} />}
              style={{ width: '100%' }}
            >
              {isLoading ? 'PARSING ARCHIVE HEADERS…' : '🔍 RUN ZERO-EXTRACTION INSPECTION NOW'}
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
              <span>Inspection Error</span>
            </div>
            <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.85rem' }}>{error}</p>
          </div>
        )}
      </Card>

      {/* Results */}
      {result && (
        <Card
          title="Archive Structure & Manifest Details"
          badge={<span className="nb-badge nb-badge-mint">PARSED</span>}
          accent="cyan"
        >
          <div className="nb-metric-grid">
            <MetricCard
              value={`v${result.version}`}
              label="ARCHIVE SPEC VERSION"
              icon={<FileArchive size={24} />}
            />
            <MetricCard
              value={result.entry_count}
              label="TOTAL FILE ENTRIES"
              icon={<FileText size={24} />}
            />
            <MetricCard
              value={formatBytes(result.total_original)}
              label="UNCOMPRESSED SIZE"
            />
            <MetricCard
              value={formatPercent(result.overall_reduction_percent)}
              label="OVERALL REDUCTION"
              accent="mint"
            />
          </div>

          <h4 style={{ margin: '1.5rem 0 0.5rem 0' }}>📋 Central Directory Manifest</h4>
          <div className="nb-table-wrapper">
            <table className="nb-table">
              <thead>
                <tr>
                  <th>PATH</th>
                  <th>ENGINE</th>
                  <th>ORIGINAL</th>
                  <th>COMPRESSED</th>
                  <th>REDUCTION</th>
                  <th>INTEGRITY STATUS</th>
                </tr>
              </thead>
              <tbody>
                {result.entries.map((entry: ArchiveEntry, idx: number) => (
                  <tr key={idx}>
                    <td>
                      <code>{entry.path}</code>
                    </td>
                    <td>
                      <span className="nb-badge nb-badge-yellow">{entry.algorithm}</span>
                    </td>
                    <td>{formatBytes(entry.original_size)}</td>
                    <td>{formatBytes(entry.compressed_size)}</td>
                    <td>{formatPercent(entry.reduction_percent)}</td>
                    <td>
                      {entry.integrity_status === 'VALID' ? (
                        <span className="nb-badge nb-badge-mint">
                          <CheckCircle2 size={12} strokeWidth={3} />
                          VALID SHA-256
                        </span>
                      ) : (
                        <span className="nb-badge nb-badge-red">
                          <AlertTriangle size={12} strokeWidth={3} />
                          {entry.integrity_status}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
