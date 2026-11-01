/**
 * API Service for Land Record Matching Backend
 */

const BASE_URL = '/api';

export const api = {
  // Health
  getHealth: async () => {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  },

  // Sources
  listSources: async () => {
    const res = await fetch(`${BASE_URL}/sources`);
    if (!res.ok) throw new Error('Failed to fetch sources');
    return res.json();
  },

  getSourceRecords: async (sourceId, limit = 100) => {
    const res = await fetch(`${BASE_URL}/sources/${sourceId}/records?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch records');
    return res.json();
  },

  getSourceQuality: async (sourceId) => {
    const res = await fetch(`${BASE_URL}/sources/${sourceId}/quality`);
    if (!res.ok) throw new Error('Failed to fetch quality report');
    return res.json();
  },

  uploadSource: async (formData) => {
    const res = await fetch(`${BASE_URL}/sources/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  loadSampleBenchmarks: async () => {
    const res = await fetch(`${BASE_URL}/sources/load-sample-benchmarks`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to load sample benchmarks');
    return res.json();
  },

  // Matching
  runMatching: async (config) => {
    const res = await fetch(`${BASE_URL}/matching/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Matching run failed');
    }
    return res.json();
  },

  getMatchingResults: async (params = {}) => {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${BASE_URL}/matching/results?${query}`);
    if (!res.ok) throw new Error('Failed to fetch matching results');
    return res.json();
  },

  getPairDetail: async (pairId) => {
    const res = await fetch(`${BASE_URL}/matching/${pairId}`);
    if (!res.ok) throw new Error('Failed to fetch pair detail');
    return res.json();
  },

  resolvePair: async (pairId, payload) => {
    const res = await fetch(`${BASE_URL}/matching/${pairId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to resolve pair');
    return res.json();
  },

  // Conflicts
  getConflicts: async (params = {}) => {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${BASE_URL}/conflicts?${query}`);
    if (!res.ok) throw new Error('Failed to fetch conflicts');
    return res.json();
  },

  resolveConflict: async (conflictId, payload) => {
    const res = await fetch(`${BASE_URL}/conflicts/${conflictId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to resolve conflict');
    return res.json();
  },

  // Evaluation
  getEvaluationMetrics: async () => {
    const res = await fetch(`${BASE_URL}/evaluation/metrics`);
    if (!res.ok) throw new Error('Failed to fetch evaluation metrics');
    return res.json();
  },

  getThresholdAnalysis: async () => {
    const res = await fetch(`${BASE_URL}/evaluation/threshold-analysis`);
    if (!res.ok) throw new Error('Failed to fetch threshold analysis');
    return res.json();
  },

  // Rules
  getRules: async () => {
    const res = await fetch(`${BASE_URL}/rules`);
    if (!res.ok) throw new Error('Failed to fetch rules');
    return res.json();
  },

  // Audit
  getAuditTrail: async (targetId = null) => {
    const query = targetId ? `?target_id=${encodeURIComponent(targetId)}` : '';
    const res = await fetch(`${BASE_URL}/audit${query}`);
    if (!res.ok) throw new Error('Failed to fetch audit log');
    return res.json();
  },

  // Export URLs
  getExportUrl: (exportType, format = 'csv') => {
    return `${BASE_URL}/exports/${exportType}?format=${format}`;
  }
};

