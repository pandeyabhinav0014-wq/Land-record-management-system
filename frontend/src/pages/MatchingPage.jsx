import React, { useState } from 'react';
import { 
  GitMerge, 
  Play, 
  Sliders, 
  Search, 
  Filter, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  ChevronRight, 
  Info,
  ShieldCheck,
  MapPin,
  FileText
} from 'lucide-react';
import { api } from '../services/api';

export default function MatchingPage({ 
  candidatePairs, 
  onRunMatching, 
  loading,
  onNavigateToConflict
}) {
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPair, setSelectedPair] = useState(null);
  
  // Matching configuration panel
  const [showConfig, setShowConfig] = useState(false);
  const [highThreshold, setHighThreshold] = useState(0.80);
  const [mediumThreshold, setMediumThreshold] = useState(0.55);
  const [areaTolerance, setAreaTolerance] = useState(0.30);
  const [enableSurvey, setEnableSurvey] = useState(true);
  const [enableSpatial, setEnableSpatial] = useState(true);
  const [enableLocalityArea, setEnableLocalityArea] = useState(true);

  const handleApplyAndRun = () => {
    onRunMatching({
      high_threshold: parseFloat(highThreshold),
      medium_threshold: parseFloat(mediumThreshold),
      area_tolerance_ratio: parseFloat(areaTolerance),
      enable_survey_blocking: enableSurvey,
      enable_spatial_blocking: enableSpatial,
      enable_locality_area_blocking: enableLocalityArea
    });
  };

  const filteredPairs = candidatePairs.filter(p => {
    if (filterDecision !== 'ALL' && p.match_decision !== filterDecision) {
      return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const sA = (p.record_a?.parcel_or_survey_number || '').toLowerCase();
      const sB = (p.record_b?.parcel_or_survey_number || '').toLowerCase();
      const oA = (p.record_a?.owner_name || '').toLowerCase();
      const oB = (p.record_b?.owner_name || '').toLowerCase();
      const pId = p.pair_id.toLowerCase();
      return sA.includes(q) || sB.includes(q) || oA.includes(q) || oB.includes(q) || pId.includes(q);
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Header & Trigger */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Entity Matching & Similarity Analysis</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Stage A–E multi-stage entity resolution pipeline integrating GIS geometry, fuzzy attributes & business rules.
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-medium text-xs shadow-sm transition-colors"
          >
            <Sliders className="w-4 h-4" />
            <span>{showConfig ? 'Close Parameters' : 'Tune Parameters'}</span>
          </button>
          <button
            onClick={handleApplyAndRun}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs shadow-sm transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>{loading ? 'Running Matching...' : 'Run Matching'}</span>
          </button>
        </div>
      </div>

      {/* Config Panel Drawer */}
      {showConfig && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-2">
            <h2 className="text-sm font-semibold text-slate-800 flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-emerald-600" />
              <span>Pipeline Calibration & Blocking Parameters</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
            {/* Thresholds */}
            <div className="space-y-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
              <div className="font-semibold text-slate-800">Confidence Thresholds</div>
              <div>
                <div className="flex justify-between mb-1 text-slate-600">
                  <span>High (Auto-Match Target):</span>
                  <span className="font-mono font-bold text-emerald-700">{highThreshold}</span>
                </div>
                <input
                  type="range"
                  min="0.65"
                  max="0.95"
                  step="0.05"
                  value={highThreshold}
                  onChange={(e) => setHighThreshold(e.target.value)}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1 text-slate-600">
                  <span>Medium (Manual Review Cutoff):</span>
                  <span className="font-mono font-bold text-amber-700">{mediumThreshold}</span>
                </div>
                <input
                  type="range"
                  min="0.40"
                  max="0.75"
                  step="0.05"
                  value={mediumThreshold}
                  onChange={(e) => setMediumThreshold(e.target.value)}
                  className="w-full accent-amber-600"
                />
              </div>
            </div>

            {/* Tolerances */}
            <div className="space-y-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
              <div className="font-semibold text-slate-800">Geometric & Area Tolerances</div>
              <div>
                <div className="flex justify-between mb-1 text-slate-600">
                  <span>Area Tolerance Ratio:</span>
                  <span className="font-mono font-bold text-slate-800">{(areaTolerance * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.60"
                  step="0.05"
                  value={areaTolerance}
                  onChange={(e) => setAreaTolerance(e.target.value)}
                  className="w-full accent-slate-700"
                />
              </div>
              <p className="text-[11px] text-slate-500">
                Pairs with relative area differences above this tolerance are penalized and flagged for review.
              </p>
            </div>

            {/* Blocking Rules */}
            <div className="space-y-2 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
              <div className="font-semibold text-slate-800">Stage A Blocking Strategies</div>
              <label className="flex items-center space-x-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableSurvey}
                  onChange={(e) => setEnableSurvey(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500"
                />
                <span>Survey Number & Root Blocking</span>
              </label>
              <label className="flex items-center space-x-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableSpatial}
                  onChange={(e) => setEnableSpatial(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500"
                />
                <span>Spatial Bounding Box / Distance Blocking</span>
              </label>
              <label className="flex items-center space-x-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableLocalityArea}
                  onChange={(e) => setEnableLocalityArea(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500"
                />
                <span>Locality & Area Similarity Blocking</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-center gap-3 bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by survey, owner, ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto text-xs">
          {[
            { id: 'ALL', label: 'All Pairs' },
            { id: 'HIGH_CONFIDENCE', label: 'High Confidence (Auto)' },
            { id: 'MEDIUM_CONFIDENCE', label: 'Medium Confidence (Review)' },
            { id: 'LOW_CONFIDENCE', label: 'Low Confidence (Reject)' }
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setFilterDecision(f.id)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors shrink-0 ${
                filterDecision === f.id
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Candidate Pairs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Pair ID</th>
                <th className="py-2.5 px-4">Source Record A</th>
                <th className="py-2.5 px-4">Source Record B</th>
                <th className="py-2.5 px-4">Survey Numbers</th>
                <th className="py-2.5 px-4">Area Comparison</th>
                <th className="py-2.5 px-4">Confidence Score</th>
                <th className="py-2.5 px-4">Decision</th>
                <th className="py-2.5 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredPairs.map((p) => {
                const isHigh = p.match_decision === 'HIGH_CONFIDENCE';
                const isMed = p.match_decision === 'MEDIUM_CONFIDENCE';
                const scorePct = (p.final_confidence * 100).toFixed(1);

                return (
                  <tr 
                    key={p.pair_id} 
                    onClick={() => setSelectedPair(p)}
                    className="hover:bg-slate-50/70 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-slate-700">{p.pair_id}</td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">{p.source_a_name}</div>
                      <div className="text-[11px] font-mono text-slate-500">{p.source_record_id_a}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">{p.source_b_name}</div>
                      <div className="text-[11px] font-mono text-slate-500">{p.source_record_id_b}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-mono text-slate-900 font-medium">
                        {p.raw_metrics?.survey_a || p.record_a?.parcel_or_survey_number}
                        <span className="text-slate-400 mx-1">↔</span>
                        {p.raw_metrics?.survey_b || p.record_b?.parcel_or_survey_number}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-700">
                      <div>
                        {p.raw_metrics?.area_a_sqm ? `${p.raw_metrics.area_a_sqm} m²` : '—'} vs {p.raw_metrics?.area_b_sqm ? `${p.raw_metrics.area_b_sqm} m²` : '—'}
                      </div>
                      {p.raw_metrics?.relative_area_difference !== undefined && (
                        <div className="text-[10px] text-slate-500">
                          Diff: {(p.raw_metrics.relative_area_difference * 100).toFixed(1)}%
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${
                              isHigh ? 'bg-emerald-500' : isMed ? 'bg-amber-500' : 'bg-slate-400'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, p.final_confidence * 100))}%` }}
                          />
                        </div>
                        <span className="font-mono font-semibold text-slate-800">{scorePct}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                        isHigh 
                          ? 'bg-emerald-100 text-emerald-800' 
                          : isMed 
                          ? 'bg-amber-100 text-amber-800' 
                          : 'bg-slate-100 text-slate-600'
                      }`}>
                        {p.reviewer_decision ? `RESOLVED (${p.reviewer_decision})` : p.match_decision.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <ChevronRight className="w-4 h-4 text-slate-400 inline" />
                    </td>
                  </tr>
                );
              })}
              {filteredPairs.length === 0 && (
                <tr>
                  <td colSpan="8" className="py-10 text-center text-slate-400 text-xs">
                    No candidate pairs match the active filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Explainable AI (XAI) Modal / Inspection Drawer */}
      {selectedPair && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex justify-end">
          <div className="bg-white w-full max-w-2xl h-full shadow-2xl p-6 overflow-y-auto space-y-6">
            <div className="flex justify-between items-start border-b border-slate-100 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                    {selectedPair.pair_id}
                  </span>
                  <span className={`text-xs px-2.5 py-0.5 rounded font-bold ${
                    selectedPair.match_decision === 'HIGH_CONFIDENCE'
                      ? 'bg-emerald-100 text-emerald-800'
                      : selectedPair.match_decision === 'MEDIUM_CONFIDENCE'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    Score: {(selectedPair.final_confidence * 100).toFixed(1)}% • {selectedPair.match_decision}
                  </span>
                </div>
                <h2 className="text-base font-bold text-slate-900 mt-1">Explainable AI Match Breakdown</h2>
              </div>
              <button
                onClick={() => setSelectedPair(null)}
                className="text-slate-400 hover:text-slate-700 text-xl font-bold p-1"
              >
                &times;
              </button>
            </div>

            {/* Natural Language Explanation Box */}
            <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-1.5 text-xs text-slate-800">
              <div className="font-semibold text-emerald-900 flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Auditable Decision Explanation</span>
              </div>
              <p className="leading-relaxed font-serif text-slate-700">
                "{selectedPair.explanation?.summary}"
              </p>
              <p className="text-[10px] text-slate-500 pt-1">
                Notice: Algorithmic decision-support recommendation only; does not declare statutory legal ownership.
              </p>
            </div>

            {/* Positive vs Negative vs Missing Evidence */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 bg-emerald-50/40 rounded-lg border border-emerald-100 space-y-2">
                <div className="font-semibold text-emerald-800 flex items-center space-x-1">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Supporting Positive Evidence</span>
                </div>
                <ul className="space-y-1 text-slate-700 list-disc list-inside">
                  {selectedPair.explanation?.positive_evidence?.map((e, idx) => (
                    <li key={idx} className="leading-tight">{e}</li>
                  ))}
                  {(!selectedPair.explanation?.positive_evidence || selectedPair.explanation?.positive_evidence.length === 0) && (
                    <li className="text-slate-400 italic">None recorded.</li>
                  )}
                </ul>
              </div>

              <div className="p-3.5 bg-rose-50/40 rounded-lg border border-rose-100 space-y-2">
                <div className="font-semibold text-rose-800 flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>Divergent / Negative Evidence</span>
                </div>
                <ul className="space-y-1 text-slate-700 list-disc list-inside">
                  {selectedPair.explanation?.negative_evidence?.map((e, idx) => (
                    <li key={idx} className="leading-tight text-rose-700 font-medium">{e}</li>
                  ))}
                  {(!selectedPair.explanation?.negative_evidence || selectedPair.explanation?.negative_evidence.length === 0) && (
                    <li className="text-slate-400 italic">No contradictory signals detected.</li>
                  )}
                </ul>
              </div>
            </div>

            {/* Component Feature Contributions */}
            <div className="space-y-3">
              <h3 className="font-semibold text-xs text-slate-800 uppercase tracking-wider">
                Component Similarity Scores & Effective Weights
              </h3>
              <div className="space-y-2 text-xs">
                {Object.entries(selectedPair.feature_scores || {}).map(([feat, score]) => {
                  const wt = selectedPair.effective_weights?.[feat] || 0;
                  const pct = (score * 100).toFixed(1);
                  return (
                    <div key={feat} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between gap-4">
                      <div className="w-1/3">
                        <span className="font-mono text-slate-800 block truncate capitalize">
                          {feat.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[10px] text-slate-500">Weight: {(wt * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-1/2 flex items-center space-x-2">
                        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div 
                            className="bg-emerald-600 h-full rounded-full" 
                            style={{ width: `${Math.min(100, Math.max(0, score * 100))}%` }}
                          />
                        </div>
                        <span className="font-mono font-medium text-slate-700 w-12 text-right">{pct}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Triggered Business Rules */}
            <div className="space-y-2">
              <h3 className="font-semibold text-xs text-slate-800 uppercase tracking-wider">
                Triggered Knowledge Rules
              </h3>
              <div className="space-y-2">
                {selectedPair.triggered_rules?.map((r, i) => (
                  <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-bold text-slate-800">{r.rule_id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.severity === 'HIGH' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {r.severity}
                      </span>
                    </div>
                    <div className="text-slate-600">{r.audit_explanation}</div>
                    <div className="text-[11px] text-slate-500">Action: <span className="font-mono text-slate-700">{r.action}</span> (Delta: {r.confidence_delta})</div>
                  </div>
                ))}
                {(!selectedPair.triggered_rules || selectedPair.triggered_rules.length === 0) && (
                  <div className="text-xs text-slate-400 italic">No business rule overrides triggered for this pair.</div>
                )}
              </div>
            </div>

            {/* Routing to Conflict Resolution Desk */}
            <div className="pt-4 border-t border-slate-100 flex justify-end space-x-3">
              <button
                onClick={() => {
                  const pId = selectedPair.pair_id;
                  setSelectedPair(null);
                  onNavigateToConflict(pId);
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs rounded-lg transition-colors"
              >
                Open in Conflict Resolution Desk
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

