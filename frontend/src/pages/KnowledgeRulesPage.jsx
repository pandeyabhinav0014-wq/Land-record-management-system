import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  ShieldAlert, 
  Sliders, 
  CheckCircle2, 
  AlertTriangle, 
  Info,
  Scale
} from 'lucide-react';
import { api } from '../services/api';

export default function KnowledgeRulesPage() {
  const [rules, setRules] = useState([]);
  const [sourcePriority, setSourcePriority] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const res = await api.getRules();
        setRules(res.rules || []);
        setSourcePriority(res.source_priority || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchRules();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-500">Loading business rules...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Knowledge Representation & Business Rules</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Explicit domain rules, administrative source-priorities, and confidence adjustment logic.
        </p>
      </div>

      {/* Administrative Source-Priority Notice Box */}
      <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 space-y-1">
        <div className="font-bold flex items-center space-x-1.5 text-amber-950">
          <Scale className="w-4 h-4 text-amber-700 shrink-0" />
          <span>Statutory Governance Disclaimer</span>
        </div>
        <p className="leading-relaxed">
          The source-priority order specified below represents an <strong>administrative preference policy</strong> for 
          suggesting reconciliation defaults. It does <strong>not constitute legal proof of title or conclusive statutory ownership</strong>.
          Authorized human reviewers retain final discretion.
        </p>
      </div>

      {/* Source Priority Policy Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
        <h2 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-emerald-600" />
          <span>Administrative Source-Priority Hierarchy</span>
        </h2>
        <div className="flex flex-col sm:flex-row items-center gap-2 text-xs">
          {sourcePriority.map((src, idx) => (
            <React.Fragment key={src}>
              <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-lg font-medium text-slate-800">
                <span className="w-5 h-5 rounded-full bg-emerald-700 text-white flex items-center justify-center font-bold text-[10px]">
                  {idx + 1}
                </span>
                <span>{src}</span>
              </div>
              {idx < sourcePriority.length - 1 && (
                <span className="text-slate-400 font-bold hidden sm:inline">&gt;</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Rules Catalog Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <h2 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
            <BookOpen className="w-4 h-4 text-slate-600" />
            <span>Auditable Business Rules ({rules.length})</span>
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Rule ID</th>
                <th className="py-2.5 px-4">Description & Intent</th>
                <th className="py-2.5 px-4">Severity</th>
                <th className="py-2.5 px-4">Action</th>
                <th className="py-2.5 px-4">Confidence Delta</th>
                <th className="py-2.5 px-4">Evidence Fields</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rules.map((r) => (
                <tr key={r.rule_id} className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">{r.rule_id}</td>
                  <td className="py-3 px-4 font-medium text-slate-700 max-w-sm">{r.description}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      r.severity === 'HIGH' 
                        ? 'bg-rose-100 text-rose-800' 
                        : r.severity === 'WARNING' 
                        ? 'bg-amber-100 text-amber-800' 
                        : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {r.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-800 font-semibold">{r.action}</td>
                  <td className="py-3 px-4 font-mono font-bold">
                    <span className={r.confidence_delta > 0 ? 'text-emerald-700' : r.confidence_delta < 0 ? 'text-rose-700' : 'text-slate-400'}>
                      {r.confidence_delta > 0 ? `+${r.confidence_delta}` : r.confidence_delta}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                    {r.evidence_fields?.join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

