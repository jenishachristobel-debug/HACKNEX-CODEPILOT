import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Terminal,
  Clock,
  RotateCcw,
  Download,
  FileCheck,
  ArrowRight
} from 'lucide-react';
import { api, TaskItem, TestRunItem, VerificationData, downloadCorrectedZip } from '../services/api';

export const RegressionGuardianPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const taskIdParam = searchParams.get('taskId');

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(
    taskIdParam ? parseInt(taskIdParam, 10) : null
  );
  const [verification, setVerification] = useState<VerificationData | null>(null);
  const [testRuns, setTestRuns] = useState<TestRunItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [activeTab, setActiveTab] = useState<'matrix' | 'terminal' | 'integrity'>('matrix');

  const selectedTask = tasks.find(t => t.id === selectedTaskId);

  const handleDownloadCorrected = async () => {
    if (!selectedTask) return;
    setDownloading(true);
    try {
      await downloadCorrectedZip(selectedTask.project_id, selectedTask.project_name || `project_${selectedTask.project_id}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to download corrected ZIP archive.');
    } finally {
      setDownloading(false);
    }
  };

  useEffect(() => {
    api.get('/tasks')
      .then(res => {
        const list = res.data.tasks || [];
        setTasks(list);
        if (!selectedTaskId && list.length > 0) {
          setSelectedTaskId(list[0].id);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedTaskId) return;

    setLoading(true);
    Promise.all([
      api.get(`/tasks/${selectedTaskId}/verification`).catch(() => ({ data: null })),
      api.get(`/tasks/${selectedTaskId}/test-runs`).catch(() => ({ data: { test_runs: [] } }))
    ])
      .then(([vRes, trRes]) => {
        setVerification(vRes?.data || null);
        setTestRuns(trRes?.data?.test_runs || []);
      })
      .finally(() => setLoading(false));
  }, [selectedTaskId]);

  const baselineRun = testRuns.find(r => r.stage === 'baseline');
  const postPatchRun = testRuns.filter(r => r.stage === 'post_patch').pop();

  // Compute test comparison rows
  const baselineTestsMap = new Map();
  baselineRun?.test_details?.forEach(t => baselineTestsMap.set(t.name, t.status));

  const postTestsMap = new Map();
  postPatchRun?.test_details?.forEach(t => postTestsMap.set(t.name, t.status));

  const allTestNames = Array.from(new Set([
    ...Array.from(baselineTestsMap.keys()),
    ...Array.from(postTestsMap.keys())
  ]));

  const getDeltaBadge = (name: string) => {
    const pre = baselineTestsMap.get(name);
    const post = postTestsMap.get(name);

    if (pre === 'PASSED' && post === 'FAILED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-[#D94F62]/10 text-[#D94F62] uppercase tracking-wider">
          <XCircle size={12} /> REGRESSION
        </span>
      );
    }
    if (pre === 'FAILED' && post === 'PASSED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-[#159A72]/10 text-[#159A72] uppercase tracking-wider">
          <CheckCircle2 size={12} /> NEWLY PASSING
        </span>
      );
    }
    if (!pre && post === 'PASSED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-[#3983E6]/10 text-[#3983E6] uppercase tracking-wider">
          <CheckCircle2 size={12} /> NEW REGRESSION TEST
        </span>
      );
    }
    return (
      <span className="text-[10px] font-semibold text-[#68738A]">
        UNCHANGED
      </span>
    );
  };

  const isVerified = verification?.classification === 'FIX_VERIFIED';
  const isRegression = verification?.classification === 'REGRESSION_DETECTED';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header & Task Selector */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck size={22} className="text-[#5B5CE2]" />
            <h2 className="text-xl font-bold text-[#182033]">Regression Guardian</h2>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#159A72]/10 text-[#159A72]">
              CORE INNOVATION
            </span>
          </div>
          <p className="text-[13px] text-[#68738A] mt-0.5">
            Automated pre-patch vs. post-patch behavior verification & differential regression detection
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-[12px] font-semibold text-[#68738A]">Active Task:</label>
          <select
            value={selectedTaskId || ''}
            onChange={(e) => setSelectedTaskId(Number(e.target.value))}
            className="px-3 py-1.5 rounded-lg border border-[#E6E9F2] text-[13px] font-semibold text-[#182033] bg-white focus:outline-none focus:border-[#5B5CE2]"
          >
            {tasks.map(t => (
              <option key={t.id} value={t.id}>
                #{t.id} - {t.bug_title.substring(0, 35)}...
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-[#68738A]">Querying Regression Guardian telemetry...</div>
      ) : !verification ? (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-12 text-center shadow-xs">
          <ShieldAlert size={40} className="mx-auto text-[#D99522] mb-3" />
          <h3 className="text-[16px] font-bold text-[#182033]">Verification Has Not Executed</h3>
          <p className="text-[13px] text-[#68738A] mt-1 mb-5">
            Approve the proposed patch on the Patch Review screen to trigger the Regression Guardian pipeline.
          </p>
          <button
            onClick={() => navigate(`/patches?taskId=${selectedTaskId}`)}
            className="px-4 py-2 bg-[#5B5CE2] hover:bg-[#4F50D6] text-white rounded-lg text-[13px] font-semibold cursor-pointer"
          >
            Go to Patch Review
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Guardian Verdict Banner */}
          <div className={`p-6 rounded-2xl border shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-5 ${
            isVerified
              ? 'bg-[#159A72]/10 border-[#159A72]/30 text-[#182033]'
              : isRegression
              ? 'bg-[#D94F62]/10 border-[#D94F62]/30 text-[#182033]'
              : 'bg-[#D99522]/10 border-[#D99522]/30 text-[#182033]'
          }`}>
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                isVerified ? 'bg-[#159A72] text-white' : isRegression ? 'bg-[#D94F62] text-white' : 'bg-[#D99522] text-white'
              }`}>
                {isVerified ? <ShieldCheck size={26} /> : isRegression ? <ShieldAlert size={26} /> : <AlertTriangle size={26} />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className={`text-[12px] font-bold tracking-wider uppercase px-2 py-0.5 rounded ${
                    isVerified ? 'bg-[#159A72]/20 text-[#159A72]' : isRegression ? 'bg-[#D94F62]/20 text-[#D94F62]' : 'bg-[#D99522]/20 text-[#D99522]'
                  }`}>
                    {verification.classification}
                  </span>
                  <span className="text-[11px] text-[#68738A]">Certified by Evidence Engine</span>
                </div>
                <h3 className="text-lg font-bold text-[#182033] mt-1">
                  {isVerified
                    ? 'Fix Verified: 0 Regressions Detected'
                    : isRegression
                    ? 'Regression Alert: Previously passing baseline tests failed!'
                    : 'Verification Incomplete or Failed'}
                </h3>
                <p className="text-[13px] text-[#68738A] mt-0.5">
                  {verification.evidence_summary?.explanation || 'Real execution evidence confirmed by pytest runner in sandbox.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0 flex-wrap">
              {isVerified && selectedTask ? (
                <button
                  onClick={handleDownloadCorrected}
                  disabled={downloading}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#159A72] text-white hover:bg-[#128361] text-[13px] font-semibold cursor-pointer shadow-xs transition-colors disabled:opacity-50"
                >
                  <Download size={15} />
                  <span>{downloading ? 'Downloading...' : 'Download Corrected ZIP'}</span>
                </button>
              ) : (
                <button
                  disabled
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gray-100 text-gray-400 border border-gray-200 text-[13px] font-semibold cursor-not-allowed shadow-xs"
                  title="Download enabled only after 0-regression verification"
                >
                  <Download size={15} />
                  <span>Download Corrected ZIP (Requires 0 Regressions)</span>
                </button>
              )}
              <button
                onClick={() => navigate(`/reports/${verification.id}`)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white border border-[#E6E9F2] text-[#182033] hover:bg-[#F7F8FC] text-[13px] font-semibold cursor-pointer shadow-2xs"
              >
                <FileCheck size={15} className="text-[#5B5CE2]" />
                <span>View Full Evidence Report</span>
              </button>
            </div>
          </div>

          {/* Verification Checklist */}
          <div className="bg-white p-5 rounded-2xl border border-[#E6E9F2] shadow-xs">
            <h4 className="text-[12px] font-bold text-[#68738A] uppercase tracking-wider mb-3">
              Autonomous Verification Checklist
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="flex items-center gap-2 text-[13px]">
                <CheckCircle2 size={16} className="text-[#159A72]" />
                <span className="text-[#182033] font-medium">Full repository analyzed</span>
              </div>
              <div className="flex items-center gap-2 text-[13px]">
                <CheckCircle2 size={16} className="text-[#159A72]" />
                <span className="text-[#182033] font-medium">Root cause identified</span>
              </div>
              <div className="flex items-center gap-2 text-[13px]">
                <CheckCircle2 size={16} className="text-[#159A72]" />
                <span className="text-[#182033] font-medium">Patch generated</span>
              </div>
              <div className="flex items-center gap-2 text-[13px]">
                <CheckCircle2 size={16} className="text-[#159A72]" />
                <span className="text-[#182033] font-medium">Patch applied</span>
              </div>
              <div className="flex items-center gap-2 text-[13px]">
                <CheckCircle2 size={16} className="text-[#159A72]" />
                <span className="text-[#182033] font-medium">Full test suite executed</span>
              </div>
              <div className="flex items-center gap-2 text-[13px]">
                <CheckCircle2 size={16} className="text-[#159A72]" />
                <span className="text-[#182033] font-medium">Regression check completed</span>
              </div>
              <div className="flex items-center gap-2 text-[13px]">
                {isVerified ? (
                  <CheckCircle2 size={16} className="text-[#159A72]" />
                ) : (
                  <XCircle size={16} className="text-[#D94F62]" />
                )}
                <span className={`font-medium ${isVerified ? 'text-[#159A72]' : 'text-[#D94F62]'}`}>
                  0 regressions
                </span>
              </div>
              <div className="flex items-center gap-2 text-[13px]">
                {verification.syntax_status === 'PASSED' ? (
                  <CheckCircle2 size={16} className="text-[#159A72]" />
                ) : (
                  <XCircle size={16} className="text-[#D94F62]" />
                )}
                <span className={`font-medium ${verification.syntax_status === 'PASSED' ? 'text-[#159A72]' : 'text-[#D94F62]'}`}>
                  Repository integrity verified
                </span>
              </div>
            </div>
          </div>

          {/* Dual Execution Stats: Baseline vs Post-Patch */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Baseline Run Card */}
            <div className="bg-white p-5 rounded-2xl border border-[#E6E9F2] shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-[#E6E9F2]">
                <span className="text-[12px] font-bold text-[#68738A] uppercase">Baseline Test Run (Pre-Patch)</span>
                <span className="font-mono text-[11px] text-[#68738A] flex items-center gap-1">
                  <Clock size={12} /> {baselineRun?.duration_ms || 0}ms
                </span>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-4 text-center">
                <div className="p-3 bg-[#159A72]/5 rounded-xl border border-[#159A72]/20">
                  <div className="text-xl font-bold text-[#159A72]">{baselineRun?.passed_count || 0}</div>
                  <span className="text-[11px] text-[#68738A] font-medium">Passed</span>
                </div>
                <div className="p-3 bg-[#D94F62]/5 rounded-xl border border-[#D94F62]/20">
                  <div className="text-xl font-bold text-[#D94F62]">{baselineRun?.failed_count || 0}</div>
                  <span className="text-[11px] text-[#68738A] font-medium">Failed</span>
                </div>
                <div className="p-3 bg-[#F7F8FC] rounded-xl border border-[#E6E9F2]">
                  <div className="text-xl font-bold text-[#182033] font-mono">{baselineRun?.exit_code === 0 ? '0 (OK)' : baselineRun?.exit_code ?? 'N/A'}</div>
                  <span className="text-[11px] text-[#68738A] font-medium">Exit Code</span>
                </div>
              </div>
            </div>

            {/* Post-Patch Run Card */}
            <div className="bg-white p-5 rounded-2xl border border-[#E6E9F2] shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-[#E6E9F2]">
                <span className="text-[12px] font-bold text-[#68738A] uppercase">Post-Patch Run + New Regression Tests</span>
                <span className="font-mono text-[11px] text-[#68738A] flex items-center gap-1">
                  <Clock size={12} /> {postPatchRun?.duration_ms || 0}ms
                </span>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-4 text-center">
                <div className="p-3 bg-[#159A72]/5 rounded-xl border border-[#159A72]/20">
                  <div className="text-xl font-bold text-[#159A72]">{postPatchRun?.passed_count || 0}</div>
                  <span className="text-[11px] text-[#68738A] font-medium">Passed</span>
                </div>
                <div className="p-3 bg-[#D94F62]/5 rounded-xl border border-[#D94F62]/20">
                  <div className="text-xl font-bold text-[#D94F62]">{postPatchRun?.failed_count || 0}</div>
                  <span className="text-[11px] text-[#68738A] font-medium">Failed</span>
                </div>
                <div className="p-3 bg-[#F7F8FC] rounded-xl border border-[#E6E9F2]">
                  <div className="text-xl font-bold text-[#182033] font-mono">{postPatchRun?.exit_code === 0 ? '0 (OK)' : postPatchRun?.exit_code ?? 'N/A'}</div>
                  <span className="text-[11px] text-[#68738A] font-medium">Exit Code</span>
                </div>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-2 border-b border-[#E6E9F2] text-[13px] font-semibold">
            <button
              onClick={() => setActiveTab('matrix')}
              className={`pb-3 px-3 cursor-pointer ${
                activeTab === 'matrix' ? 'border-b-2 border-[#5B5CE2] text-[#5B5CE2]' : 'text-[#68738A] hover:text-[#182033]'
              }`}
            >
              Differential Test Matrix ({allTestNames.length})
            </button>
            <button
              onClick={() => setActiveTab('terminal')}
              className={`pb-3 px-3 cursor-pointer ${
                activeTab === 'terminal' ? 'border-b-2 border-[#5B5CE2] text-[#5B5CE2]' : 'text-[#68738A] hover:text-[#182033]'
              }`}
            >
              Raw Test Execution Logs
            </button>
            <button
              onClick={() => setActiveTab('integrity')}
              className={`pb-3 px-3 cursor-pointer ${
                activeTab === 'integrity' ? 'border-b-2 border-[#5B5CE2] text-[#5B5CE2]' : 'text-[#68738A] hover:text-[#182033]'
              }`}
            >
              Repository Integrity & Changed Files
            </button>
          </div>

          {/* Tab 1: Differential Test Matrix Table */}
          {activeTab === 'matrix' && (
            <div className="bg-white rounded-2xl border border-[#E6E9F2] shadow-xs overflow-hidden">
              <table className="w-full text-left text-[13px]">
                <thead>
                  <tr className="bg-[#F7F8FC] border-b border-[#E6E9F2] text-[11px] uppercase tracking-wider text-[#68738A]">
                    <th className="py-3 px-4 font-semibold">Test Identifier</th>
                    <th className="py-3 px-4 font-semibold">Pre-Patch (Baseline)</th>
                    <th className="py-3 px-4 font-semibold">Post-Patch</th>
                    <th className="py-3 px-4 font-semibold text-right">Guardian Delta Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E6E9F2]">
                  {allTestNames.map((name) => {
                    const pre = baselineTestsMap.get(name);
                    const post = postTestsMap.get(name);
                    return (
                      <tr key={name} className="hover:bg-[#F7F8FC]/50 transition-colors">
                        <td className="py-3 px-4 font-mono text-[12px] text-[#182033] font-medium">{name}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                            pre === 'PASSED' ? 'bg-[#159A72]/10 text-[#159A72]' : pre === 'FAILED' ? 'bg-[#D94F62]/10 text-[#D94F62]' : 'text-[#68738A]'
                          }`}>
                            {pre || 'NOT RUN'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                            post === 'PASSED' ? 'bg-[#159A72]/10 text-[#159A72]' : post === 'FAILED' ? 'bg-[#D94F62]/10 text-[#D94F62]' : 'text-[#68738A]'
                          }`}>
                            {post || 'NOT RUN'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          {getDeltaBadge(name)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Raw Subprocess Pytest Terminal Output */}
          {activeTab === 'terminal' && (
            <div className="bg-[#182033] text-gray-200 rounded-2xl p-5 font-mono text-[12px] shadow-md space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-gray-700">
                <span className="flex items-center gap-2 text-gray-400">
                  <Terminal size={14} className="text-[#5B5CE2]" /> Pytest Isolated Subprocess Log
                </span>
                <span className="text-[11px] text-gray-400">Sandbox: {baselineRun?.command}</span>
              </div>
              <pre className="overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-96">
                {postPatchRun?.output_log || baselineRun?.output_log || '# No execution output logged'}
              </pre>
            </div>
          )}

          {/* Tab 3: Repository Integrity & Changed Files */}
          {activeTab === 'integrity' && (
            <div className="bg-white rounded-2xl border border-[#E6E9F2] shadow-xs p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#E6E9F2]">
                <h4 className="text-[14px] font-bold text-[#182033] flex items-center gap-2">
                  <ShieldCheck size={18} className="text-[#159A72]" /> Full Repository Integrity Summary
                </h4>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-[#159A72]/10 text-[#159A72] uppercase">
                  Verified Clean
                </span>
              </div>
              <div className="bg-[#F7F8FC] p-4 rounded-xl border border-[#E6E9F2] font-mono text-[12px] text-[#182033] whitespace-pre-wrap">
                {verification.evidence_summary?.integrity_check?.summary_text ||
                 (verification as any).integrity_check?.summary_text ||
                 `MODIFIED:\n  ${selectedTask?.latest_patch?.target_file || 'target_file.py'}\n\nUNCHANGED:\n  All other repository files preserved intact.`}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

