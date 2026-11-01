import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  Database, 
  GitMerge, 
  Map as MapIcon, 
  ShieldAlert, 
  BarChart3, 
  BookOpen, 
  FileText,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sparkles
} from 'lucide-react';

import { api } from './services/api';
import OverviewPage from './pages/OverviewPage';
import DataImportPage from './pages/DataImportPage';
import MatchingPage from './pages/MatchingPage';
import GisMapPage from './pages/GisMapPage';
import ConflictResolutionPage from './pages/ConflictResolutionPage';
import EvaluationPage from './pages/EvaluationPage';
import KnowledgeRulesPage from './pages/KnowledgeRulesPage';
import AuditReportsPage from './pages/AuditReportsPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [sources, setSources] = useState([]);
  const [candidatePairs, setCandidatePairs] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [meta, setMeta] = useState({});
  const [loading, setLoading] = useState(false);
  const [initialPairForResolution, setInitialPairForResolution] = useState(null);

  // Initial data loader
  const refreshAllData = async () => {
    setLoading(true);
    try {
      const [srcRes, matchRes, confRes] = await Promise.all([
        api.listSources(),
        api.getMatchingResults(),
        api.getConflicts()
      ]);
      setSources(srcRes.sources || []);
      setCandidatePairs(matchRes.candidate_pairs || []);
      setMeta(matchRes.metadata || {});
      setConflicts(confRes.conflicts || []);
    } catch (err) {
      console.error('Error fetching system state:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAllData();
  }, []);

  const handleRunMatching = async (config = {}) => {
    setLoading(true);
    try {
      await api.runMatching(config);
      await refreshAllData();
      alert('Matching pipeline executed successfully!');
    } catch (err) {
      alert('Error running matching: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetBenchmark = async () => {
    if (!window.confirm('Reset all sources and matching state to official benchmark datasets?')) return;
    setLoading(true);
    try {
      await api.loadSampleBenchmarks();
      await refreshAllData();
      alert('Benchmark datasets and baseline reconciliation loaded.');
    } catch (err) {
      alert('Error loading benchmarks: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const navigateTo = (tabName, params = {}) => {
    if (params.pairId) {
      setInitialPairForResolution(params.pairId);
    }
    setActiveTab(tabName);
  };

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Layers },
    { id: 'import', label: 'Data Import', icon: Database },
    { id: 'matching', label: 'Parcel Matching', icon: GitMerge },
    { id: 'gis', label: 'GIS Map', icon: MapIcon },
    { id: 'conflicts', label: 'Conflict Desk', icon: ShieldAlert, badge: conflicts.filter(c => c.resolution_status === 'PENDING').length },
    { id: 'evaluation', label: 'Evaluation', icon: BarChart3 },
    { id: 'rules', label: 'Knowledge & Rules', icon: BookOpen },
    { id: 'audit', label: 'Audit & Reports', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo / Brand */}
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('overview')}>
              <div className="w-9 h-9 rounded-lg bg-emerald-500 flex items-center justify-center text-slate-900 font-bold shadow-md">
                <GitMerge className="w-5 h-5 text-slate-950" />
              </div>
              <div>
                <div className="font-bold text-sm tracking-tight flex items-center space-x-1.5">
                  <span>LandMatch AI</span>
                  <span className="text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-700/50 px-1.5 py-0.5 rounded">
                    Cadastral Resolution
                  </span>
                </div>
                <div className="text-[10px] text-slate-400">Multi-Source Record Reconciliation & Decision Support</div>
              </div>
            </div>

            {/* Quick Actions & System Status */}
            <div className="flex items-center space-x-3">
              <div className="hidden md:flex items-center space-x-1.5 text-xs text-slate-300 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>FastAPI + Shapely Engine Active</span>
              </div>

              <button
                onClick={refreshAllData}
                disabled={loading}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Refresh State"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="bg-slate-950 border-t border-slate-800/80">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex space-x-1 overflow-x-auto py-2 text-xs scrollbar-none">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg font-medium transition-colors shrink-0 ${
                      isActive
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                    {item.badge !== undefined && item.badge > 0 && (
                      <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                        isActive ? 'bg-white text-emerald-800' : 'bg-rose-500 text-white'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Page Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <OverviewPage
            sources={sources}
            meta={meta}
            candidatePairs={candidatePairs}
            conflicts={conflicts}
            onNavigate={navigateTo}
            onRunMatching={() => handleRunMatching()}
            onResetBenchmark={handleResetBenchmark}
            loading={loading}
          />
        )}

        {activeTab === 'import' && (
          <DataImportPage
            sources={sources}
            onRefreshSources={refreshAllData}
          />
        )}

        {activeTab === 'matching' && (
          <MatchingPage
            candidatePairs={candidatePairs}
            onRunMatching={handleRunMatching}
            loading={loading}
            onNavigateToConflict={(pairId) => navigateTo('conflicts', { pairId })}
          />
        )}

        {activeTab === 'gis' && (
          <GisMapPage
            candidatePairs={candidatePairs}
            onNavigateToConflict={(pairId) => navigateTo('conflicts', { pairId })}
          />
        )}

        {activeTab === 'conflicts' && (
          <ConflictResolutionPage
            candidatePairs={candidatePairs}
            conflicts={conflicts}
            onRefreshData={refreshAllData}
            initialPairId={initialPairForResolution}
          />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationPage />
        )}

        {activeTab === 'rules' && (
          <KnowledgeRulesPage />
        )}

        {activeTab === 'audit' && (
          <AuditReportsPage />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <div>
            Multi-Source Land Record Matching & Conflict Resolution System &copy; 2026
          </div>
          <div className="text-[11px] text-slate-400">
            Decision-Support Only • Preserves Original Cadastral Provenance • SQLite / PostGIS Architecture
          </div>
        </div>
      </footer>
    </div>
  );
}

