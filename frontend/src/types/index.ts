export type Theme = 'light' | 'dark';

export type CompressionLevel = 'EXTREME' | 'RECOMMENDED' | 'LESS';

export type AlgorithmType = 'AUTO' | 'HUFFMAN' | 'LZW' | 'RLE' | 'STORE';

export interface CompressionFileDetail {
  name: string;
  original_size: number;
  compressed_size: number;
  reduction_percent: number;
  compression_ratio: number;
  algorithm: string;
  duration_ms: number;
  sha256: string;
}

export interface CompressionResponse {
  success: boolean;
  job_id: string;
  archive_name: string;
  total_input: number;
  total_compressed: number;
  reduction_percent: number;
  compression_ratio: number;
  elapsed_seconds: number;
  target_status: 'ACHIEVED' | 'ACHIEVED_LOSSY' | 'BEST_EFFORT' | null;
  is_single_file: boolean;
  single_file_name?: string;
  single_file_mime?: string;
  files: CompressionFileDetail[];
}

export interface ArchiveEntry {
  path: string;
  algorithm: string;
  original_size: number;
  compressed_size: number;
  reduction_percent: number;
  integrity_status: 'VALID' | 'CORRUPTED' | 'UNVERIFIED';
  sha256?: string;
}

export interface DecompressPreviewResponse {
  success: boolean;
  version: number;
  entry_count: number;
  total_original: number;
  overall_reduction_percent: number;
  entries: ArchiveEntry[];
}

export interface ExtractedFileItem {
  index: number;
  path: string;
  name: string;
  size: number;
  mime: string;
}

export interface DecompressExtractResponse {
  success: boolean;
  job_id: string;
  count: number;
  files: ExtractedFileItem[];
}

export interface ImageOptimizeResponse {
  success: boolean;
  job_id: string;
  original_size: number;
  final_size: number;
  reduction_percent: number;
  quality: number;
  output_format: string;
  target_status: 'ACHIEVED' | 'BEST_EFFORT' | null;
  iterations: number;
  dimensions: {
    original: { width: number; height: number };
    optimized: { width: number; height: number };
  };
  original_preview: string;
  optimized_preview: string;
  download_filename: string;
}

export interface BenchmarkItem {
  algorithm: string;
  original_size: number;
  compressed_size: number;
  reduction_percent: number;
  compression_ratio: number;
  compress_duration_ms: number;
  decompress_duration_ms: number;
  speed_kbps: number;
  verified: boolean;
  is_best?: boolean;
  error?: string | null;
}

export interface BenchmarkResponse {
  success: boolean;
  filename: string;
  original_size: number;
  best_algorithm: string;
  results: BenchmarkItem[];
}

export interface AlgorithmInfo {
  id: string;
  name: string;
  tag: string;
  description: string;
  best_for?: string;
  is_default?: boolean;
}

export interface InspectResponse {
  success: boolean;
  filename: string;
  version: number;
  entry_count: number;
  total_original: number;
  overall_reduction_percent: number;
  entries: ArchiveEntry[];
}
