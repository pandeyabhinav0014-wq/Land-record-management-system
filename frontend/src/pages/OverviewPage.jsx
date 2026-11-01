import React from 'react';
import { 
  Database, 
  GitMerge, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldAlert, 
  Play, 
  RefreshCw, 
  ArrowRight,
  MapPin,
  Sparkles
} from 'lucide-react';

export default function OverviewPage({ 
  sources = [], 
  meta = {}, 
  candidatePairs = [], 
  conflicts = [], 
  onNavigate,
  onRunMatching,
  onResetBenchmark,
  loading
}) {
  const totalRecords = sources.reduce((acc, s) => acc + (s.total_records || 0), 0);
  const totalWarnings = sources.reduce((acc, s) => acc + (s.warnings_count || 0), 0);
  const pendingReviews = candidatePairs.filter(p => p.match_decision === 'MEDIUM_CONFIDENCE' && !p.reviewer_decision).length;
  const highMatches = candidatePairs.filter(p => p.match_decision === 'HIGH_CONFIDENCE' || p.reviewer_decision === 'CONFIRM_MATCH').length;
  const pendingConflicts = conflicts.filter(c => c.resolution_status === 'PENDING').length;

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-emerald-800 to-teal-900 rounded-xl p-6 text-white shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2 text-emerald-300 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            <span>AI-Assisted Cadastral Reconciliation & Decision Support</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Multi-Source Land Record Matching & Conflict Resolution</h1>
          <p className="text-emerald-100/80 text-sm max-w-2xl mt-1">
            Disambiguates land parcels across revenue, municipal, and GIS boundaries with calibrated confidence scoring,
            transparent XAI explanations, and human-in-the-loop audit governance.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={onRunMatching}
            disabled={loading}
            className="flex items-center space-x-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-medium px-4 py-2 rounded-lg text-sm transition-colors shadow-sm disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-slate-900" />
            <span>{loading ? 'Processing...' : 'Run Matching Pipeline'}</span>
          </button>
          <button
            onClick={onResetBenchmark}
            disabled={loading}
            className="flex items-center space-x-2 bg-emerald-950/60 hover:bg-emerald-950 border border-emerald-700/50 text-emerald-200 px-3.5 py-2 rounded-lg text-sm transition-colors"
            title="Reloads official multi-agency benchmark dataset"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reset Benchmark</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase">Source Records</span>
            <Database className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalRecords}</div>
          <div className="text-xs text-slate-500 mt-1">{sources.length} Connected Sources</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase">Candidate Pairs</span>
            <GitMerge className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{candidatePairs.length}</div>
          <div className="text-xs text-slate-500 mt-1">Multi-stage Blocking</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase">High Matches</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-700">{highMatches}</div>
          <div className="text-xs text-emerald-600 mt-1">Confidence ≥ 0.80</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase">Review Queue</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-700">{pendingReviews}</div>
          <div className="text-xs text-amber-600 mt-1">Ambiguous Candidates</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase">Conflicts</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-700">{pendingConflicts}</div>
          <div className="text-xs text-rose-600 mt-1">Pending Resolution</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase">Data Warnings</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalWarnings}</div>
          <div className="text-xs text-slate-500 mt-1">Quality Pipeline Flags</div>
        </div>
      </div>

      {/* Two Column Layout: Connected Agencies & High-Priority Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Source Datasets */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
              <Database className="w-4 h-4 text-slate-600" />
              <span>Connected Data Sources</span>
            </h2>
            <button
              onClick={() => onNavigate('import')}
              className="text-xs text-emerald-700 hover:text-emerald-800 font-medium flex items-center space-x-1"
            >
              <span>Manage</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-3">
            {sources.map(s => (
              <div key={s.source_id} className="p-3 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-slate-800">{s.source_name}</div>
                  <div className="text-xs text-slate-500 mt-0.5">Format: <span className="font-mono">{s.file_format}</span> • {s.total_records} records</div>
                </div>
                <div className="text-right">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                    s.invalid_records > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                  }`}>
                    {s.invalid_records > 0 ? `${s.invalid_records} Invalid` : '100% Valid'}
                  </span>
                </div>
              </div>
            ))}
            {sources.length === 0 && (
              <div className="text-center py-6 text-slate-400 text-xs">No data sources connected yet.</div>
            )}
          </div>
        </div>

        {/* Middle & Right: Reconciliation Quick Queue */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-semibold text-slate-900 text-sm">Actionable Review Queue (Human-in-the-Loop)</h2>
              <p className="text-xs text-slate-500 mt-0.5">Borderline match pairs and attribute contradictions routed for administrative review.</p>
            </div>
            <button
              onClick={() => onNavigate('conflicts')}
              className="text-xs text-emerald-700 hover:text-emerald-800 font-medium flex items-center space-x-1"
            >
              <span>Full Resolution Desk</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {candidatePairs
              .filter(p => p.match_decision === 'MEDIUM_CONFIDENCE' || p.requires_manual_review)
              .slice(0, 4)
              .map(p => (
                <div key={p.pair_id} className="py-3 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-medium text-slate-700">{p.pair_id}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-medium">
                        Confidence: {(p.final_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="text-xs text-slate-600">
                      <span className="font-medium text-slate-800">{p.source_a_name} ({p.source_record_id_a})</span>
                      <span className="text-slate-400 mx-1.5">vs</span>
                      <span className="font-medium text-slate-800">{p.source_b_name} ({p.source_record_id_b})</span>
                    </div>
                    <div className="text-xs text-slate-500 line-clamp-1 italic">
                      "{p.explanation?.summary}"
                    </div>
                  </div>
                  <button
                    onClick={() => onNavigate('conflicts', { pairId: p.pair_id })}
                    className="shrink-0 text-xs px-3 py-1.5 rounded-lg border border-emerald-600 text-emerald-700 hover:bg-emerald-50 font-medium transition-colors"
                  >
                    Review Pair
                  </button>
                </div>
              ))}

            {candidatePairs.filter(p => p.match_decision === 'MEDIUM_CONFIDENCE').length === 0 && (
              <div className="text-center py-8 text-slate-400 text-xs">
                No pending ambiguous cases in the review queue. All candidate pairs resolved or categorized.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

