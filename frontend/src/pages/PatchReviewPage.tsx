import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { DiffEditor } from '@monaco-editor/react';
import {
  GitPullRequest,
  CheckCircle2,
  XCircle,
  RotateCcw,
  ShieldCheck,
  FileCode,
  AlertTriangle,
  PlayCircle,
  Clock,
  Sparkles
} from 'lucide-react';
import { api, PatchItem, TaskItem } from '../services/api';

export const PatchReviewPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const taskIdParam = searchParams.get('taskId');

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(
    taskIdParam ? parseInt(taskIdParam, 10) : null
  );
  const [patches, setPatches] = useState<PatchItem[]>([]);
  const [selectedPatch, setSelectedPatch] = useState<PatchItem | null>(null);
  const [taskDetail, setTaskDetail] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

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
    api.get(`/tasks/${selectedTaskId}`)
      .then(res => setTaskDetail(res.data))
      .catch(console.error);

    api.get(`/tasks/${selectedTaskId}/analysis`)
      .then(res => setAnalysis(res.data))
      .catch(() => setAnalysis(null));

    api.get(`/tasks/${selectedTaskId}/patches`)
      .then(res => {
        const pList = res.data.patches || [];
        setPatches(pList);
        if (pList.length > 0) {
          setSelectedPatch(pList[0]);
        } else {
          setSelectedPatch(null);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedTaskId]);

  const handleApproveAndVerify = async () => {
    if (!selectedPatch || !selectedTaskId) return;
    setActionLoading(true);
    try {
      // 1. Approve
      await api.post(`/patches/${selectedPatch.id}/approve`);
      // 2. Trigger Verification with Regression Guardian
      await api.post(`/tasks/${selectedTaskId}/verify`);
      // 3. Navigate to Regression Guardian page
      navigate(`/regression?taskId=${selectedTaskId}`);
    } catch (err: any) {
      alert(`Verification failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedPatch) return;
    setActionLoading(true);
    try {
      await api.post(`/patches/${selectedPatch.id}/reject`);
      // Refresh
      const res = await api.get(`/tasks/${selectedTaskId}/patches`);
      setPatches(res.data.patches || []);
    } catch (err: any) {
      alert('Failed to reject patch');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRollback = async () => {
    if (!selectedPatch) return;
    if (!window.confirm('Restore workspace sandbox to original pre-patch state?')) return;
    setActionLoading(true);
    try {
      await api.post(`/patches/${selectedPatch.id}/rollback`);
      alert('Sandbox restored to baseline snapshot.');
      const res = await api.get(`/tasks/${selectedTaskId}/patches`);
      setPatches(res.data.patches || []);
    } catch (err: any) {
      alert('Failed to rollback');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Controls Bar */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#182033] flex items-center gap-2">
            <GitPullRequest size={20} className="text-[#5B5CE2]" /> Patch Diff Review
          </h2>
          <p className="text-[13px] text-[#68738A] mt-0.5">
            Side-by-side verification of proposed minimal code changes before sandbox application
          </p>
        </div>

        {/* Task Selector */}
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
        <div className="text-center py-20 text-[#68738A]">Loading patch diff...</div>
      ) : !selectedPatch ? (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-12 text-center shadow-xs">
          <GitPullRequest size={38} className="mx-auto text-[#68738A]/50 mb-3" />
          <h3 className="text-[16px] font-bold text-[#182033]">No Patches Synthesized Yet</h3>
          <p className="text-[13px] text-[#68738A] mt-1 mb-4">
            Analysis has not generated a patch for this task yet.
          </p>
          <button
            onClick={() => navigate('/analysis/new')}
            className="px-4 py-2 bg-[#5B5CE2] text-white rounded-lg text-[13px] font-semibold cursor-pointer"
          >
            Start New Analysis
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Patch Details & Actions Bar */}
          <div className="bg-white rounded-2xl border border-[#E6E9F2] p-5 shadow-xs flex flex-col gap-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <FileCode size={18} className="text-[#5B5CE2]" />
                  <span className="font-mono text-[14px] font-bold text-[#182033]">
                    {selectedPatch.target_file}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                    selectedPatch.status === 'approved' || selectedPatch.status === 'applied'
                      ? 'bg-[#159A72]/10 text-[#159A72]'
                      : selectedPatch.status === 'rejected'
                      ? 'bg-[#D94F62]/10 text-[#D94F62]'
                      : 'bg-[#5B5CE2]/10 text-[#5B5CE2]'
                  }`}>
                    {selectedPatch.status}
                  </span>
                  <span className="text-[11px] text-[#68738A]">
                    Attempt #{selectedPatch.attempt_number}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2.5 shrink-0">
                <button
                  onClick={handleRollback}
                  disabled={actionLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E6E9F2] bg-[#F7F8FC] hover:bg-[#E6E9F2] text-[#182033] text-[12px] font-semibold cursor-pointer transition-colors"
                  title="Revert sandbox changes"
                >
                  <RotateCcw size={14} />
                  <span>Rollback</span>
                </button>

                <button
                  onClick={handleReject}
                  disabled={actionLoading || selectedPatch.status === 'rejected'}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D94F62]/30 bg-[#D94F62]/10 hover:bg-[#D94F62]/20 text-[#D94F62] text-[12px] font-semibold cursor-pointer transition-colors disabled:opacity-50"
                >
                  <XCircle size={14} />
                  <span>Reject Patch</span>
                </button>

                <button
                  onClick={handleApproveAndVerify}
                  disabled={actionLoading}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#159A72] hover:bg-[#128361] text-white text-[13px] font-semibold shadow-xs cursor-pointer transition-colors disabled:opacity-50"
                >
                  <ShieldCheck size={16} />
                  <span>{actionLoading ? 'Executing Guardian...' : 'Approve Patch'}</span>
                </button>
              </div>
            </div>

            {/* Rich Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-[#E6E9F2] text-[12px]">
              <div className="bg-[#F7F8FC] p-3 rounded-xl border border-[#E6E9F2]">
                <span className="text-[10px] font-bold text-[#68738A] uppercase tracking-wider block mb-1">Affected Files</span>
                <span className="font-mono text-[#182033] font-medium break-all">
                  {analysis?.affected_files?.join(', ') || selectedPatch.target_file}
                </span>
              </div>
              <div className="bg-[#F7F8FC] p-3 rounded-xl border border-[#E6E9F2]">
                <span className="text-[10px] font-bold text-[#68738A] uppercase tracking-wider block mb-1">Root Cause</span>
                <span className="text-[#182033] font-medium line-clamp-2">
                  {analysis?.root_cause || taskDetail?.bug_title || 'Identified boundary condition error'}
                </span>
              </div>
              <div className="bg-[#F7F8FC] p-3 rounded-xl border border-[#E6E9F2]">
                <span className="text-[10px] font-bold text-[#68738A] uppercase tracking-wider block mb-1">Call Path</span>
                <span className="font-mono text-[#5B5CE2] font-semibold break-all">
                  {analysis?.call_path || `${selectedPatch.target_file}`}
                </span>
              </div>
              <div className="bg-[#F7F8FC] p-3 rounded-xl border border-[#E6E9F2]">
                <span className="text-[10px] font-bold text-[#68738A] uppercase tracking-wider block mb-1">Risk Level</span>
                <span className="inline-flex items-center gap-1 font-semibold text-[#159A72]">
                  <CheckCircle2 size={13} /> {selectedPatch.potential_impact || 'Minimal (isolated fix)'}
                </span>
              </div>
            </div>

            <div className="text-[12px] text-[#68738A] pt-1">
              <strong className="text-[#182033]">Explanation:</strong> {selectedPatch.explanation}
            </div>
          </div>

          {/* Monaco Side-by-Side Diff Editor */}
          <div className="bg-white rounded-2xl border border-[#E6E9F2] shadow-xs overflow-hidden h-[540px] flex flex-col">
            <div className="p-3 border-b border-[#E6E9F2] bg-[#F7F8FC] text-[12px] font-semibold text-[#68738A] flex justify-between items-center px-4">
              <span>Original (Pre-Patch)</span>
              <span>Proposed Minimal Patch (Post-Patch)</span>
            </div>
            <div className="flex-1 relative">
              <DiffEditor
                height="100%"
                language="python"
                original={selectedPatch.original_code}
                modified={selectedPatch.new_code}
                theme="light"
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  fontSize: 13,
                  renderSideBySide: true,
                  automaticLayout: true,
                  scrollBeyondLastLine: false,
                  wordWrap: 'on'
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

