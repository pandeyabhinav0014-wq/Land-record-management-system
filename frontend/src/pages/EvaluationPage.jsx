import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer, 
  LineChart, 
  Line,
  AreaChart,
  Area
} from 'recharts';
import { 
  CheckCircle, 
  AlertCircle, 
  TrendingUp, 
  Cpu, 
  FileCode, 
  HelpCircle,
  Hash,
  Activity
} from 'lucide-react';
import { api } from '../services/api';

export default function EvaluationPage() {
  const [metricsData, setMetricsData] = useState(null);
  const [thresholdData, setThresholdData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [m, t] = await Promise.all([
          api.getEvaluationMetrics(),
          api.getThresholdAnalysis()
        ]);
        setMetricsData(m);
        setThresholdData(t);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500 text-xs">
        <Activity className="w-6 h-6 animate-spin mx-auto text-emerald-600 mb-2" />
        <span>Computing real Scikit-Learn validation metrics against ground truth...</span>
      </div>
    );
  }

  const evalMetrics = metricsData?.evaluation_metrics || {};
  const cm = evalMetrics.confusion_matrix || { tp: 0, fp: 0, tn: 0, fn: 0 };
  const sensitivityList = thresholdData?.threshold_analysis || [];
  const repMeta = thresholdData?.reproducibility_metadata || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Empirical Evaluation & Threshold Sensitivity</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Validation metrics measured on ground-truth labeled benchmark pairs without fabricated statistics.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500 mb-1">Precision</div>
          <div className="text-2xl font-bold text-emerald-700">
            {((evalMetrics.precision || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-500 mt-1">TP / (TP + FP)</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500 mb-1">Recall</div>
          <div className="text-2xl font-bold text-blue-700">
            {((evalMetrics.recall || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-500 mt-1">TP / (TP + FN)</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500 mb-1">F1-Score</div>
          <div className="text-2xl font-bold text-indigo-700">
            {((evalMetrics.f1_score || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Harmonic mean of P & R</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500 mb-1">Labeled Pairs</div>
          <div className="text-2xl font-bold text-slate-800">
            {evalMetrics.sample_size || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Ground Truth Evaluations</div>
        </div>
      </div>

      {/* Confusion Matrix and Precision-Recall Trade-off Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Confusion Matrix Visualizer */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-slate-900 text-sm">Empirical Confusion Matrix</h2>
            <span className="text-[11px] text-slate-500">Evaluated at τ = 0.70</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            {/* TP */}
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
              <span className="text-[11px] font-semibold text-emerald-800 uppercase block">True Positives (TP)</span>
              <span className="text-3xl font-extrabold text-emerald-700 my-1 block">{cm.tp}</span>
              <span className="text-[10px] text-emerald-600">Correctly identified same parcels</span>
            </div>

            {/* FP */}
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-center">
              <span className="text-[11px] font-semibold text-rose-800 uppercase block">False Positives (FP)</span>
              <span className="text-3xl font-extrabold text-rose-700 my-1 block">{cm.fp}</span>
              <span className="text-[10px] text-rose-600">Spurious matches incorrectly linked</span>
            </div>

            {/* FN */}
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-center">
              <span className="text-[11px] font-semibold text-amber-800 uppercase block">False Negatives (FN)</span>
              <span className="text-3xl font-extrabold text-amber-700 my-1 block">{cm.fn}</span>
              <span className="text-[10px] text-amber-600">Omitted true matches</span>
            </div>

            {/* TN */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center">
              <span className="text-[11px] font-semibold text-slate-700 uppercase block">True Negatives (TN)</span>
              <span className="text-3xl font-extrabold text-slate-800 my-1 block">{cm.tn}</span>
              <span className="text-[10px] text-slate-500">Correctly rejected non-matches</span>
            </div>
          </div>

          <div className="text-[11px] text-slate-500 space-y-1 pt-1">
            <div>False Positive Rate (FPR): <strong className="font-mono text-slate-700">{((evalMetrics.false_positive_rate || 0) * 100).toFixed(1)}%</strong></div>
            <div>False Negative Rate (FNR): <strong className="font-mono text-slate-700">{((evalMetrics.false_negative_rate || 0) * 100).toFixed(1)}%</strong></div>
          </div>
        </div>

        {/* Precision vs Recall Curve Chart */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-slate-900 text-sm">Threshold Sensitivity (Precision vs. Recall)</h2>
            <span className="text-[11px] text-slate-500">Sweeping τ from 0.50 to 0.90</span>
          </div>

          <div className="h-64 w-full text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sensitivityList}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="threshold" label={{ value: 'Decision Threshold (τ)', position: 'insideBottom', offset: -5 }} />
                <YAxis domain={[0, 1.1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <Tooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
                <Legend verticalAlign="top" height={36} />
                <Line type="monotone" dataKey="precision" name="Precision" stroke="#10b981" strokeWidth={2.5} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="recall" name="Recall" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="f1_score" name="F1-Score" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="4 4" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Threshold Sensitivity Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
        <h2 className="font-semibold text-slate-900 text-sm">
          Multi-Threshold Trade-off Matrix & Operational Workload
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-y border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Threshold (τ)</th>
                <th className="py-2.5 px-4">Auto Matches</th>
                <th className="py-2.5 px-4">Sent to Review</th>
                <th className="py-2.5 px-4">Measured Precision</th>
                <th className="py-2.5 px-4">Measured Recall</th>
                <th className="py-2.5 px-4">F1-Score</th>
                <th className="py-2.5 px-4">False Positives</th>
                <th className="py-2.5 px-4">Unresolved Conflicts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {sensitivityList.map((row) => (
                <tr key={row.threshold} className="hover:bg-slate-50/50">
                  <td className="py-2.5 px-4 font-bold text-slate-900">{row.threshold.toFixed(2)}</td>
                  <td className="py-2.5 px-4 text-emerald-700 font-medium">{row.auto_accepted_count}</td>
                  <td className="py-2.5 px-4 text-amber-700 font-medium">{row.manual_review_count}</td>
                  <td className="py-2.5 px-4 text-slate-800 font-semibold">{(row.precision * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-4 text-slate-800 font-semibold">{(row.recall * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-4 text-slate-800 font-semibold">{(row.f1_score * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-4 text-rose-700 font-bold">{row.false_positives}</td>
                  <td className="py-2.5 px-4 text-slate-600">{row.unresolved_conflicts_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-slate-500 italic pt-1">
          {thresholdData?.observation}
        </p>
      </div>

      {/* Reproducibility Audit Metadata */}
      <div className="bg-slate-900 text-slate-200 rounded-xl p-5 shadow-sm space-y-3 font-mono text-xs">
        <div className="flex items-center space-x-2 text-emerald-400 font-bold">
          <Cpu className="w-4 h-4" />
          <span>Reproducibility & Experiment Provenance Ledger</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
          <div>
            <span className="text-slate-400 block text-[10px]">Python Engine:</span>
            <span className="text-slate-100">{repMeta.python_version} ({repMeta.os_platform})</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">Scikit-Learn Version:</span>
            <span className="text-slate-100">{repMeta.library_versions?.['scikit-learn']}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">Shapely GIS Version:</span>
            <span className="text-slate-100">{repMeta.library_versions?.shapely}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">Deterministic Seed & Hash:</span>
            <span className="text-slate-100">Seed {repMeta.random_seed} • SHA {repMeta.configuration_hash}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

