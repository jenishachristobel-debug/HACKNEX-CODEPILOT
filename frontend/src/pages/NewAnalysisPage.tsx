import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  PlayCircle,
  FolderGit2,
  Sparkles,
  ShieldCheck,
  FileText,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  ArrowLeft
} from 'lucide-react';
import { api, ProjectItem, formatApiError } from '../services/api';

export const NewAnalysisPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialProjectId = searchParams.get('projectId');

  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    initialProjectId ? parseInt(initialProjectId, 10) : null
  );

  const [step, setStep] = useState(1);
  const [bugTitle, setBugTitle] = useState('');
  const [bugDescription, setBugDescription] = useState('');
  const [errorTraceback, setErrorTraceback] = useState('');
  const [expectedBehavior, setExpectedBehavior] = useState('');
  const [actualBehavior, setActualBehavior] = useState('');
  const [mode, setMode] = useState('patch_and_verify'); // 'analysis_only', 'patch_proposal', 'patch_and_verify'

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectBugReport, setProjectBugReport] = useState<any>(null);

  useEffect(() => {
    api.get('/projects')
      .then(res => {
        const list = res.data.projects || [];
        setProjects(list);
        if (!selectedProjectId && list.length > 0) {
          setSelectedProjectId(list[0].id);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedProjectId) {
      setProjectBugReport(null);
      return;
    }
    api.get(`/projects/${selectedProjectId}`)
      .then(res => {
        setProjectBugReport(res.data.bug_report || res.data.scan?.bug_report || null);
      })
      .catch(() => setProjectBugReport(null));
  }, [selectedProjectId]);

  const handleLoadFromBugReport = () => {
    if (!projectBugReport) return;
    const t = projectBugReport.suggested_task || {};
    setBugTitle(t.bug_title || projectBugReport.title || '');
    setBugDescription(t.bug_description || projectBugReport.description || '');
    setExpectedBehavior(t.expected_behavior || 'Pass all unit tests and satisfy documented requirements.');
    setActualBehavior(t.actual_behavior || 'Unit test suite fails due to edge case or boundary logic.');
    setErrorTraceback(t.reproduction_steps ? `Reproduction command: ${t.reproduction_steps}` : '');
  };

  const handlePrefillDemo = () => {
    setBugTitle('Orders of exactly $100 fail to receive Tier-1 discount');
    setBugDescription(
      'Customer orders of exactly $100.00 receive $0.0 discount instead of the expected 10% ($10.00). The boundary check `total > 100` mistakenly excludes the $100.00 threshold.'
    );
    setErrorTraceback(
      'AssertionError: assert calculate_discount(100.0) == 10.0, got 0.0\n  File "tests/test_calculator.py", line 18, in test_discount_boundary'
    );
    setExpectedBehavior('calculate_discount(100.0) returns 10.0 (10% discount applies to orders >= 100).');
    setActualBehavior('calculate_discount(100.0) returns 0.0 with full price charged.');
  };

  const handleStartAnalysis = async () => {
    if (!selectedProjectId || !bugTitle.trim() || !bugDescription.trim()) {
      setError('Please provide bug title and description.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      // 1. Create task
      const taskRes = await api.post('/tasks', {
        project_id: selectedProjectId,
        bug_title: bugTitle.trim(),
        bug_description: bugDescription.trim(),
        error_traceback: errorTraceback.trim(),
        expected_behavior: expectedBehavior.trim(),
        actual_behavior: actualBehavior.trim(),
        mode: mode
      });
      const taskId = taskRes.data.id;

      // 2. Trigger Autonomous Investigation
      await api.post(`/tasks/${taskId}/analyze`);

      // 3. Navigate to Patch Review
      navigate(`/patches?taskId=${taskId}`);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to start analysis task. Check the backend logs.'));
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-7">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-[#182033] tracking-tight">New Autonomous Bug Investigation</h2>
        <p className="text-[13px] text-[#68738A] mt-0.5">
          Provide bug context or tracebacks. CodePilot AI investigates root cause and prepares minimal patches.
        </p>
      </div>

      {/* Stepper Indicator */}
      <div className="flex items-center justify-between border-b border-[#E6E9F2] pb-4">
        {[
          { num: 1, title: 'Select Project' },
          { num: 2, title: 'Describe Bug' },
          { num: 3, title: 'Execution Mode' },
          { num: 4, title: 'Launch Agent' },
        ].map((s) => (
          <div key={s.num} className="flex items-center gap-2">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-[12px] font-bold ${
                step >= s.num ? 'bg-[#5B5CE2] text-white' : 'bg-[#E6E9F2] text-[#68738A]'
              }`}
            >
              {s.num}
            </div>
            <span
              className={`text-[13px] font-semibold ${
                step >= s.num ? 'text-[#182033]' : 'text-[#68738A]'
              }`}
            >
              {s.title}
            </span>
          </div>
        ))}
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-[#D94F62]/10 border border-[#D94F62]/30 text-[#D94F62] text-[13px] flex items-center gap-2">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Step 1: Select Project */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-6 shadow-xs space-y-5">
          <h3 className="text-[15px] font-bold text-[#182033]">Step 1: Choose Target Repository</h3>

          {projects.length === 0 ? (
            <div className="text-center py-8">
              <FolderGit2 size={36} className="mx-auto text-[#68738A]/50 mb-2" />
              <p className="text-[13px] font-semibold text-[#182033]">No repositories available</p>
              <div className="flex justify-center gap-2.5 mt-3">
                <button
                  onClick={async () => {
                    try {
                      setSubmitting(true);
                      const res = await api.post('/projects/demo/load');
                      const listRes = await api.get('/projects');
                      const list = listRes.data.projects || [];
                      setProjects(list);
                      setSelectedProjectId(res.data.project.id);
                    } catch (err: any) {
                      setError(formatApiError(err, 'Failed to load demo project.'));
                    } finally {
                      setSubmitting(false);
                    }
                  }}
                  className="px-4 py-2 bg-[#5B5CE2] text-white text-[12px] font-semibold rounded-lg cursor-pointer hover:bg-[#4F50D6]"
                >
                  Load Demo Project
                </button>
                <button
                  onClick={() => navigate('/projects')}
                  className="px-4 py-2 bg-[#F7F8FC] border border-[#E6E9F2] text-[#182033] text-[12px] font-semibold rounded-lg cursor-pointer hover:bg-[#E6E9F2]"
                >
                  Go to Projects
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {projects.map((p) => {
                const isSelected = selectedProjectId === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedProjectId(p.id)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-[#5B5CE2] bg-[#5B5CE2]/5 shadow-xs'
                        : 'border-[#E6E9F2] hover:bg-[#F7F8FC]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FolderGit2 size={16} className={isSelected ? 'text-[#5B5CE2]' : 'text-[#68738A]'} />
                        <span className="font-semibold text-[14px] text-[#182033]">{p.name}</span>
                      </div>
                      {p.source_type === 'demo' && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-[#5B5CE2]/10 text-[#5B5CE2]">
                          DEMO
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-[#68738A] mt-1.5">{p.file_count} files • Python</p>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex justify-end pt-3">
            <button
              onClick={() => setStep(2)}
              disabled={!selectedProjectId}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#5B5CE2] hover:bg-[#4F50D6] text-white text-[13px] font-semibold rounded-xl cursor-pointer disabled:opacity-50"
            >
              <span>Continue to Bug Details</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Describe Bug */}
      {step === 2 && (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-[15px] font-bold text-[#182033]">Step 2: Describe Bug & Provide Traceback</h3>
            <div className="flex items-center gap-2">
              {projectBugReport && (
                <button
                  type="button"
                  onClick={handleLoadFromBugReport}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#159A72]/10 text-[#159A72] border border-[#159A72]/30 text-[12px] font-semibold hover:bg-[#159A72]/20 cursor-pointer transition-colors"
                >
                  <FileText size={14} />
                  <span>Load from BUG_REPORT.md</span>
                </button>
              )}
              <button
                type="button"
                onClick={handlePrefillDemo}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#5B5CE2]/10 text-[#5B5CE2] text-[12px] font-semibold hover:bg-[#5B5CE2]/20 cursor-pointer transition-colors"
              >
                <Sparkles size={14} />
                <span>Fill Sample Bug (Demo)</span>
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-[12px] font-semibold text-[#182033] mb-1">Bug Title *</label>
              <input
                type="text"
                required
                placeholder="e.g. Orders of exactly $100 fail to receive Tier-1 discount"
                value={bugTitle}
                onChange={(e) => setBugTitle(e.target.value)}
                className="w-full px-3 py-2 text-[13px] rounded-lg border border-[#E6E9F2] focus:border-[#5B5CE2] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-[#182033] mb-1">Bug Description *</label>
              <textarea
                rows={3}
                required
                placeholder="Detailed explanation of the unexpected behavior..."
                value={bugDescription}
                onChange={(e) => setBugDescription(e.target.value)}
                className="w-full px-3 py-2 text-[13px] rounded-lg border border-[#E6E9F2] focus:border-[#5B5CE2] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-[#182033] mb-1">
                Error Message or Traceback (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="Paste traceback or AssertionError output here..."
                value={errorTraceback}
                onChange={(e) => setErrorTraceback(e.target.value)}
                className="w-full px-3 py-2 text-[12px] font-mono rounded-lg border border-[#E6E9F2] focus:border-[#5B5CE2] focus:outline-none bg-[#F7F8FC]"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[12px] font-semibold text-[#182033] mb-1">Expected Behavior</label>
                <input
                  type="text"
                  placeholder="e.g. calculate_discount(100.0) should return 10.0"
                  value={expectedBehavior}
                  onChange={(e) => setExpectedBehavior(e.target.value)}
                  className="w-full px-3 py-2 text-[13px] rounded-lg border border-[#E6E9F2] focus:border-[#5B5CE2] focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-[#182033] mb-1">Actual Behavior</label>
                <input
                  type="text"
                  placeholder="e.g. Returned 0.0"
                  value={actualBehavior}
                  onChange={(e) => setActualBehavior(e.target.value)}
                  className="w-full px-3 py-2 text-[13px] rounded-lg border border-[#E6E9F2] focus:border-[#5B5CE2] focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-between pt-3">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium text-[#68738A] hover:bg-[#F7F8FC] rounded-lg cursor-pointer"
            >
              <ArrowLeft size={14} /> Back
            </button>
            <button
              onClick={() => setStep(3)}
              disabled={!bugTitle.trim() || !bugDescription.trim()}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#5B5CE2] hover:bg-[#4F50D6] text-white text-[13px] font-semibold rounded-xl cursor-pointer disabled:opacity-50"
            >
              <span>Continue to Mode</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Configure Mode */}
      {step === 3 && (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-6 shadow-xs space-y-5">
          <h3 className="text-[15px] font-bold text-[#182033]">Step 3: Select Verification Workflow</h3>

          <div className="space-y-3">
            {[
              {
                id: 'patch_and_verify',
                title: 'Patch + Regression Guardian (Recommended)',
                desc: 'Generates minimal patch, runs pre-patch baseline tests, applies fix in isolated sandbox, executes regression tests, and guarantees zero regressions.',
                badge: 'Full Autonomous Pipeline'
              },
              {
                id: 'patch_proposal',
                title: 'Patch Proposal Mode',
                desc: 'Investigates root cause and synthesizes patch with Monaco Diff preview, but does not execute test suites automatically.',
                badge: 'Review Only'
              },
              {
                id: 'analysis_only',
                title: 'Analysis Only',
                desc: 'Extracts relevant AST snippets and diagnoses the root cause without generating code modifications.',
                badge: 'Diagnostic'
              }
            ].map((m) => {
              const isSelected = mode === m.id;
              return (
                <div
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-[#5B5CE2] bg-[#5B5CE2]/5 shadow-xs'
                      : 'border-[#E6E9F2] hover:bg-[#F7F8FC]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[14px] text-[#182033]">{m.title}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#5B5CE2]/10 text-[#5B5CE2]">
                      {m.badge}
                    </span>
                  </div>
                  <p className="text-[12px] text-[#68738A] mt-1">{m.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="flex justify-between pt-3">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium text-[#68738A] hover:bg-[#F7F8FC] rounded-lg cursor-pointer"
            >
              <ArrowLeft size={14} /> Back
            </button>
            <button
              onClick={() => setStep(4)}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#5B5CE2] hover:bg-[#4F50D6] text-white text-[13px] font-semibold rounded-xl cursor-pointer"
            >
              <span>Review & Launch</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Review & Launch */}
      {step === 4 && (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-6 shadow-xs space-y-6">
          <h3 className="text-[15px] font-bold text-[#182033]">Step 4: Launch Agent Pipeline</h3>

          <div className="bg-[#F7F8FC] p-4 rounded-xl border border-[#E6E9F2] space-y-3 text-[13px]">
            <div>
              <span className="text-[#68738A] text-[11px] uppercase font-bold">Target Repository</span>
              <p className="font-semibold text-[#182033]">
                {projects.find(p => p.id === selectedProjectId)?.name || 'Selected Project'}
              </p>
            </div>
            <div>
              <span className="text-[#68738A] text-[11px] uppercase font-bold">Bug Title</span>
              <p className="font-semibold text-[#182033]">{bugTitle}</p>
            </div>
            <div>
              <span className="text-[#68738A] text-[11px] uppercase font-bold">Workflow Mode</span>
              <p className="font-semibold text-[#5B5CE2] uppercase text-[12px]">{mode.replace(/_/g, ' ')}</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#159A72]/10 border border-[#159A72]/30 text-[12px] text-[#182033]">
            <strong>Safety & Isolation:</strong> The repository will be duplicated into an isolated sandbox. Original sources are preserved with snapshot rollback guarantees.
          </div>

          <div className="flex justify-between pt-2">
            <button
              onClick={() => setStep(3)}
              disabled={submitting}
              className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium text-[#68738A] hover:bg-[#F7F8FC] rounded-lg cursor-pointer"
            >
              <ArrowLeft size={14} /> Back
            </button>
            <button
              onClick={handleStartAnalysis}
              disabled={submitting}
              className="flex items-center gap-2 px-6 py-2.5 bg-[#5B5CE2] hover:bg-[#4F50D6] text-white text-[13px] font-semibold rounded-xl cursor-pointer disabled:opacity-50 shadow-sm"
            >
              <PlayCircle size={16} />
              <span>{submitting ? 'Investigating & Synthesizing...' : 'Start Investigation'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

