import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  ShieldCheck, 
  AlertTriangle, 
  ArrowLeftRight, 
  Check, 
  MessageSquare, 
  FileCheck,
  UserCheck
} from 'lucide-react';
import { api } from '../services/api';

export default function ConflictResolutionPage({ 
  candidatePairs, 
  conflicts, 
  onRefreshData,
  initialPairId
}) {
  const [selectedPairId, setSelectedPairId] = useState(initialPairId || '');
  const [activeTab, setActiveTab] = useState('PAIRS'); // 'PAIRS' or 'CONFLICTS'
  const [reviewerId, setReviewerId] = useState('Senior_Reviewer_01');
  const [reviewerReason, setReviewerReason] = useState('');
  const [reviewerNotes, setReviewerNotes] = useState('');
  const [resolving, setResolving] = useState(false);
  const [auditEntries, setAuditEntries] = useState([]);

  // Default to first ambiguous pair if none selected
  useEffect(() => {
    if (!selectedPairId && candidatePairs.length > 0) {
      const firstAmbiguous = candidatePairs.find(p => p.match_decision === 'MEDIUM_CONFIDENCE' || p.requires_manual_review);
      if (firstAmbiguous) {
        setSelectedPairId(firstAmbiguous.pair_id);
      } else {
        setSelectedPairId(candidatePairs[0].pair_id);
      }
    }
  }, [candidatePairs, selectedPairId]);

  // Load audit history
  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const res = await api.getAuditTrail(selectedPairId || null);
        setAuditEntries(res.audit_entries || []);
      } catch (err) {
        console.error(err);
      }
    };
    fetchAudit();
  }, [selectedPairId]);

  const currentPair = candidatePairs.find(p => p.pair_id === selectedPairId);
  const pairConflicts = conflicts.filter(c => c.pair_id === selectedPairId);

  const handleResolvePair = async (action) => {
    if (!reviewerReason.trim()) {
      alert('Please provide a mandatory justification / reason for the audit log.');
      return;
    }
    setResolving(true);
    try {
      await api.resolvePair(selectedPairId, {
        action,
        reviewer_id: reviewerId,
        reason: reviewerReason,
        reviewer_notes: reviewerNotes
      });
      setReviewerReason('');
      setReviewerNotes('');
      onRefreshData();
      alert(`Decision recorded in immutable audit log: ${action}`);
    } catch (err) {
      alert('Error recording decision: ' + err.message);
    } finally {
      setResolving(false);
    }
  };

  const handleResolveConflictAttribute = async (conflictId, selectedValue) => {
    const reason = prompt('Enter justification for selecting this preferred value:', 'Administrative source priority policy verified.');
    if (!reason) return;

    try {
      await api.resolveConflict(conflictId, {
        action: 'SELECT_PREFERRED_VALUE',
        reviewer_id: reviewerId,
        reason,
        selected_value: selectedValue
      });
      onRefreshData();
      alert('Attribute preference recorded and logged.');
    } catch (err) {
      alert('Error updating conflict: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Human-in-the-Loop Conflict Resolution Desk</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Side-by-side discrepancy reconciliation, field-level preferencing & immutable audit logging.
          </p>
        </div>

        {/* Reviewer Identifier Badge */}
        <div className="flex items-center space-x-2 text-xs bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm">
          <UserCheck className="w-4 h-4 text-emerald-600" />
          <span className="text-slate-500">Authorized Reviewer:</span>
          <input
            type="text"
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            className="font-medium text-slate-800 bg-transparent border-b border-slate-300 focus:outline-none focus:border-emerald-500 text-xs px-1"
          />
        </div>
      </div>

      {/* Main Grid: Pair Selector List & Side-by-Side Comparison Desk */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Col: Candidate Queue */}
        <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 shadow-sm p-4 space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Cases Awaiting Adjudication ({candidatePairs.length})
          </h2>

          <div className="space-y-2 max-h-[680px] overflow-y-auto pr-1">
            {candidatePairs.map(p => {
              const isSelected = p.pair_id === selectedPairId;
              const hasConflicts = conflicts.some(c => c.pair_id === p.pair_id);

              return (
                <div
                  key={p.pair_id}
                  onClick={() => setSelectedPairId(p.pair_id)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? 'border-emerald-600 bg-emerald-50/40 shadow-xs'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-slate-800">{p.pair_id}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      p.reviewer_decision
                        ? 'bg-slate-800 text-white'
                        : p.match_decision === 'HIGH_CONFIDENCE'
                        ? 'bg-emerald-100 text-emerald-800'
                        : p.match_decision === 'MEDIUM_CONFIDENCE'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}>
                      {p.reviewer_decision ? `RESOLVED: ${p.reviewer_decision}` : `${(p.final_confidence * 100).toFixed(0)}% • ${p.match_decision.replace('_', ' ')}`}
                    </span>
                  </div>

                  <div className="text-slate-600 truncate font-medium">
                    {p.source_a_name} ({p.source_record_id_a}) vs {p.source_b_name} ({p.source_record_id_b})
                  </div>

                  <div className="flex justify-between items-center text-[11px] text-slate-500 mt-1.5 pt-1 border-t border-slate-100">
                    <span>Survey: {p.record_a?.parcel_or_survey_number} ↔ {p.record_b?.parcel_or_survey_number}</span>
                    {hasConflicts && (
                      <span className="text-rose-600 font-semibold flex items-center space-x-0.5">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Conflicts</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Side-by-Side Comparison Workspace */}
        <div className="lg:col-span-8 space-y-6">
          {currentPair ? (
            <>
              {/* Side-by-Side Record Matrix */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
                  <div>
                    <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-100/60 px-2.5 py-1 rounded">
                      {currentPair.pair_id}
                    </span>
                    <span className="text-xs text-slate-500 ml-2">
                      Score: <strong className="text-slate-800">{(currentPair.final_confidence * 100).toFixed(1)}%</strong>
                      {currentPair.reviewer_decision && (
                        <span className="ml-2 font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                          Decision: {currentPair.reviewer_decision}
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 italic">
                    Administrative Review Mode
                  </div>
                </div>

                {/* Attribute Comparison Grid */}
                <div className="p-5">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[11px]">
                        <th className="py-2 w-1/4">Cadastral Attribute</th>
                        <th className="py-2 w-3/8 text-slate-800 font-bold">{currentPair.source_a_name}</th>
                        <th className="py-2 w-3/8 text-slate-800 font-bold">{currentPair.source_b_name}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {/* Survey Number */}
                      <tr>
                        <td className="py-2.5 font-semibold text-slate-600">Survey / Parcel No.</td>
                        <td className="py-2.5 font-mono font-medium text-slate-900 bg-emerald-50/30 px-2 rounded">
                          {currentPair.record_a?.parcel_or_survey_number}
                        </td>
                        <td className="py-2.5 font-mono font-medium text-slate-900 bg-emerald-50/30 px-2 rounded">
                          {currentPair.record_b?.parcel_or_survey_number}
                        </td>
                      </tr>

                      {/* Owner Name */}
                      <tr>
                        <td className="py-2.5 font-semibold text-slate-600">Owner Name</td>
                        <td className="py-2.5 text-slate-800">
                          {currentPair.record_a?.owner_name || <span className="text-slate-400 italic">&lt;Missing&gt;</span>}
                        </td>
                        <td className="py-2.5 text-slate-800">
                          {currentPair.record_b?.owner_name || <span className="text-slate-400 italic">&lt;Missing&gt;</span>}
                        </td>
                      </tr>

                      {/* Land Area */}
                      <tr>
                        <td className="py-2.5 font-semibold text-slate-600">Land Area</td>
                        <td className="py-2.5 text-slate-800">
                          {currentPair.record_a?.land_area ? `${currentPair.record_a.land_area} m²` : 'N/A'}
                        </td>
                        <td className="py-2.5 text-slate-800">
                          {currentPair.record_b?.land_area ? `${currentPair.record_b.land_area} m²` : 'N/A'}
                        </td>
                      </tr>

                      {/* Address / Locality */}
                      <tr>
                        <td className="py-2.5 font-semibold text-slate-600">Address / Village</td>
                        <td className="py-2.5 text-slate-800">
                          {currentPair.record_a?.property_address || currentPair.record_a?.village_or_locality}
                        </td>
                        <td className="py-2.5 text-slate-800">
                          {currentPair.record_b?.property_address || currentPair.record_b?.village_or_locality}
                        </td>
                      </tr>

                      {/* Coordinates */}
                      <tr>
                        <td className="py-2.5 font-semibold text-slate-600">Coordinates</td>
                        <td className="py-2.5 font-mono text-slate-700">
                          {currentPair.record_a?.latitude ? `${currentPair.record_a.latitude}, ${currentPair.record_a.longitude}` : 'No Centroid'}
                        </td>
                        <td className="py-2.5 font-mono text-slate-700">
                          {currentPair.record_b?.latitude ? `${currentPair.record_b.latitude}, ${currentPair.record_b.longitude}` : 'No Centroid'}
                        </td>
                      </tr>

                      {/* Land Use */}
                      <tr>
                        <td className="py-2.5 font-semibold text-slate-600">Land Use / Zoning</td>
                        <td className="py-2.5 text-slate-800">{currentPair.record_a?.land_use_category || 'N/A'}</td>
                        <td className="py-2.5 text-slate-800">{currentPair.record_b?.land_use_category || 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Detected Discrepancies & Preferred Value Selector */}
                {pairConflicts.length > 0 && (
                  <div className="bg-amber-50/50 p-5 border-t border-amber-200/60 space-y-3">
                    <div className="flex items-center space-x-2 text-xs font-bold text-amber-900">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      <span>Attribute Discrepancies Requiring Value Selection</span>
                    </div>

                    <div className="space-y-2 text-xs">
                      {pairConflicts.map(c => (
                        <div key={c.conflict_id} className="p-3 bg-white rounded-lg border border-amber-200 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                          <div>
                            <div className="font-semibold text-slate-800">
                              {c.category.replace(/_/g, ' ')}: <span className="text-amber-800 font-mono">{c.field}</span>
                            </div>
                            <div className="text-slate-600 mt-0.5">
                              {c.discrepancy_measure}
                            </div>
                            <div className="text-[11px] text-slate-500 mt-1 italic">
                              {c.suggested_value_rationale}
                            </div>
                            {c.resolved_value && (
                              <div className="text-emerald-700 font-bold mt-1">
                                ✓ Resolved Preferred Value: {c.resolved_value}
                              </div>
                            )}
                          </div>

                          <div className="flex items-center space-x-2 shrink-0">
                            <button
                              onClick={() => handleResolveConflictAttribute(c.conflict_id, c.value_a)}
                              className="px-2.5 py-1 rounded border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium"
                              title={`Adopt ${c.source_a} value`}
                            >
                              Choose {c.source_a}
                            </button>
                            <button
                              onClick={() => handleResolveConflictAttribute(c.conflict_id, c.value_b)}
                              className="px-2.5 py-1 rounded border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium"
                              title={`Adopt ${c.source_b} value`}
                            >
                              Choose {c.source_b}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Reviewer Adjudication Actions Box */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
                <h3 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Reviewer Resolution & Audit Confirmation</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Mandatory Decision Justification / Legal Basis *
                    </label>
                    <textarea
                      rows="2"
                      placeholder="e.g. Cross-referenced with Cadastral Map 14-B and tax assessment folio 401..."
                      value={reviewerReason}
                      onChange={(e) => setReviewerReason(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 text-xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Additional Administrative Notes (Optional)
                    </label>
                    <textarea
                      rows="2"
                      placeholder="e.g. Notice sent to municipal planning board regarding zoning variation."
                      value={reviewerNotes}
                      onChange={(e) => setReviewerNotes(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 text-xs"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                  <span className="text-[11px] text-slate-400 italic">
                    Original source records remain unaltered. Decision recorded into permanent ledger.
                  </span>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleResolvePair('REJECT_MATCH')}
                      disabled={resolving}
                      className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 font-medium text-xs transition-colors border border-rose-200"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Reject Match (Distinct)</span>
                    </button>

                    <button
                      onClick={() => handleResolvePair('MARK_UNRESOLVED')}
                      disabled={resolving}
                      className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 font-medium text-xs transition-colors border border-amber-200"
                    >
                      <HelpCircle className="w-4 h-4" />
                      <span>Mark as Unresolved</span>
                    </button>

                    <button
                      onClick={() => handleResolvePair('CONFIRM_MATCH')}
                      disabled={resolving}
                      className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-medium text-xs transition-colors shadow-sm"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Confirm Verified Match</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Audit History Log for this Pair */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
                <h3 className="font-semibold text-slate-900 text-xs uppercase tracking-wider">
                  Audit History for {currentPair.pair_id}
                </h3>
                {auditEntries.length === 0 ? (
                  <div className="text-xs text-slate-400 italic">No previous decisions logged for this pair yet.</div>
                ) : (
                  <div className="space-y-2 text-xs">
                    {auditEntries.map(a => (
                      <div key={a.audit_id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-mono font-bold text-slate-800">{a.action}</span>
                          <span className="text-[11px] text-slate-500 font-mono">{a.timestamp}</span>
                        </div>
                        <div className="text-slate-700">
                          Reviewer: <strong>{a.reviewer_id}</strong> • Justification: "{a.reason}"
                        </div>
                        {a.selected_value && (
                          <div className="text-emerald-700 font-medium">Selected Value: {a.selected_value}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200 text-xs">
              Select a candidate pair from the queue to start side-by-side reconciliation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

