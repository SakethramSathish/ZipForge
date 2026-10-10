import type {
  CompressionResponse,
  DecompressPreviewResponse,
  DecompressExtractResponse,
  ImageOptimizeResponse,
  BenchmarkResponse,
  InspectResponse,
  AlgorithmInfo,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  baseUrl: API_BASE,

  async checkHealth(): Promise<{ status: string; app: string }> {
    const res = await fetch(`${API_BASE}/api/health`);
    return handleResponse(res);
  },

  async getAlgorithms(): Promise<{ algorithms: AlgorithmInfo[] }> {
    const res = await fetch(`${API_BASE}/api/algorithms`);
    return handleResponse(res);
  },

  async compress(formData: FormData): Promise<CompressionResponse> {
    const res = await fetch(`${API_BASE}/api/compress`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  async previewArchive(file: File): Promise<DecompressPreviewResponse> {
    const fd = new FormData();
    fd.append('archive', file);
    const res = await fetch(`${API_BASE}/api/decompress/preview`, {
      method: 'POST',
      body: fd,
    });
    return handleResponse(res);
  },

  async extractArchive(file: File): Promise<DecompressExtractResponse> {
    const fd = new FormData();
    fd.append('archive', file);
    const res = await fetch(`${API_BASE}/api/decompress/extract`, {
      method: 'POST',
      body: fd,
    });
    return handleResponse(res);
  },

  async optimizeImage(formData: FormData): Promise<ImageOptimizeResponse> {
    const res = await fetch(`${API_BASE}/api/image/optimize`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  async runBenchmark(file: File): Promise<BenchmarkResponse> {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/api/benchmark`, {
      method: 'POST',
      body: fd,
    });
    return handleResponse(res);
  },

  async inspectArchive(file: File): Promise<InspectResponse> {
    const fd = new FormData();
    fd.append('archive', file);
    const res = await fetch(`${API_BASE}/api/inspect`, {
      method: 'POST',
      body: fd,
    });
    return handleResponse(res);
  },

  getDownloadArchiveUrl(jobId: string): string {
    return `${API_BASE}/api/download/archive/${jobId}`;
  },

  getDownloadProcessedFileUrl(jobId: string, index: number): string {
    return `${API_BASE}/api/download/file/${jobId}/${index}`;
  },

  getDownloadExtractedFileUrl(jobId: string, index: number): string {
    return `${API_BASE}/api/download/extracted/${jobId}/${index}`;
  },

  getDownloadImageUrl(jobId: string): string {
    return `${API_BASE}/api/download/image/${jobId}`;
  },
};
