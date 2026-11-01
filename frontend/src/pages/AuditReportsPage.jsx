import React, { useState, useEffect } from 'react';
import { 
  History, 
  Download, 
  FileSpreadsheet, 
  FileJson, 
  ShieldCheck, 
  User, 
  Calendar,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { api } from '../services/api';

export default function AuditReportsPage() {
  const [auditEntries, setAuditEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const res = await api.getAuditTrail();
        setAuditEntries(res.audit_entries || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAudit();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Audit Trail & Regulatory Reports</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Immutable historical ledger of administrative reconciliation decisions, reviewer notes, and data export.
        </p>
      </div>

      {/* Export Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Export Matching Results */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-slate-900">Matching Results</div>
            <p className="text-[11px] text-slate-500 mt-1">
              All candidate pairs, confidence scores, component features & XAI summaries.
            </p>
          </div>
          <div className="flex space-x-2 mt-4">
            <a
              href={api.getExportUrl('matching', 'csv')}
              download="matching_results.csv"
              className="flex-1 py-1.5 px-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-center font-medium text-xs border border-emerald-200 transition-colors"
            >
              CSV
            </a>
            <a
              href={api.getExportUrl('matching', 'json')}
              download="matching_results.json"
              className="flex-1 py-1.5 px-2 bg-slate-50 text-slate-700 hover:bg-slate-100 rounded text-center font-medium text-xs border border-slate-200 transition-colors"
            >
              JSON
            </a>
          </div>
        </div>

        {/* Export Conflicts */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-slate-900">Detected Conflicts</div>
            <p className="text-[11px] text-slate-500 mt-1">
              Discrepancies, field comparisons, suggested values & resolution statuses.
            </p>
          </div>
          <div className="flex space-x-2 mt-4">
            <a
              href={api.getExportUrl('conflicts', 'csv')}
              download="conflicts.csv"
              className="flex-1 py-1.5 px-2 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded text-center font-medium text-xs border border-rose-200 transition-colors"
            >
              CSV
            </a>
            <a
              href={api.getExportUrl('conflicts', 'json')}
              download="conflicts.json"
              className="flex-1 py-1.5 px-2 bg-slate-50 text-slate-700 hover:bg-slate-100 rounded text-center font-medium text-xs border border-slate-200 transition-colors"
            >
              JSON
            </a>
          </div>
        </div>

        {/* Export Audit Log */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-slate-900">Decision Audit Ledger</div>
            <p className="text-[11px] text-slate-500 mt-1">
              Reviewer actions, timestamps, reasons, state changes & notes.
            </p>
          </div>
          <div className="flex space-x-2 mt-4">
            <a
              href={api.getExportUrl('audit', 'csv')}
              download="audit_log.csv"
              className="flex-1 py-1.5 px-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded text-center font-medium text-xs border border-blue-200 transition-colors"
            >
              CSV
            </a>
            <a
              href={api.getExportUrl('audit', 'json')}
              download="audit_log.json"
              className="flex-1 py-1.5 px-2 bg-slate-50 text-slate-700 hover:bg-slate-100 rounded text-center font-medium text-xs border border-slate-200 transition-colors"
            >
              JSON
            </a>
          </div>
        </div>

        {/* Export Evaluation Benchmark */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-slate-900">Evaluation Report</div>
            <p className="text-[11px] text-slate-500 mt-1">
              Multi-threshold precision, recall, PR curves & software reproducibility parameters.
            </p>
          </div>
          <div className="mt-4">
            <a
              href={api.getExportUrl('evaluation', 'json')}
              download="evaluation_report.json"
              className="w-full block py-1.5 px-2 bg-slate-900 text-white hover:bg-slate-800 rounded text-center font-medium text-xs transition-colors"
            >
              Download JSON Report
            </a>
          </div>
        </div>
      </div>

      {/* Decision History Audit Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
            <History className="w-4 h-4 text-slate-600" />
            <span>Complete Audit Trail ({auditEntries.length} Actions)</span>
          </h2>
          <span className="text-[11px] text-slate-400">Append-Only Cryptographic Log</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Audit ID</th>
                <th className="py-2.5 px-4">Timestamp (UTC)</th>
                <th className="py-2.5 px-4">Reviewer ID</th>
                <th className="py-2.5 px-4">Action</th>
                <th className="py-2.5 px-4">Target ID</th>
                <th className="py-2.5 px-4">State Transition</th>
                <th className="py-2.5 px-4">Justification Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {auditEntries.map((a) => (
                <tr key={a.audit_id} className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-mono font-medium text-slate-800">{a.audit_id}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-500">{a.timestamp}</td>
                  <td className="py-3 px-4 font-medium text-slate-800">{a.reviewer_id}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      a.action === 'CONFIRM_MATCH' 
                        ? 'bg-emerald-100 text-emerald-800' 
                        : a.action === 'REJECT_MATCH' 
                        ? 'bg-rose-100 text-rose-800' 
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {a.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-700">{a.target_id || a.pair_id}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                    {a.previous_state || 'INIT'} &rarr; <span className="font-bold text-slate-800">{a.new_state}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-700 max-w-xs">{a.reason}</td>
                </tr>
              ))}

              {auditEntries.length === 0 && (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-400 text-xs">
                    No decisions logged in this session yet. Decisions made in the Conflict Resolution Desk will appear here in real time.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

