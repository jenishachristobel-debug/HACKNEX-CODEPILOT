import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  PlayCircle,
  ShieldCheck,
  GitPullRequest,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Clock
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { api, ProjectItem, TaskItem } from '../services/api';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/projects'),
      api.get('/tasks')
    ])
      .then(([pRes, tRes]) => {
        setProjects(pRes.data.projects || []);
        setTasks(tRes.data.tasks || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Compute metrics dynamically from backend data
  const totalTasks = tasks.length;
  const patchesProposed = tasks.filter(t => t.status !== 'pending' && t.status !== 'investigating').length;
  const verifiedFixes = tasks.filter(t => t.status === 'verified').length;
  const regressionFailures = tasks.filter(t => t.status === 'regression_failed').length;

  const chartData = [
    { name: 'Total Analyzed', count: totalTasks },
    { name: 'Patches Proposed', count: patchesProposed },
    { name: 'Verified Fixes', count: verifiedFixes },
    { name: 'Regressions Caught', count: regressionFailures },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="bg-white rounded-2xl p-7 border border-[#E6E9F2] shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#5B5CE2]/10 text-[#5B5CE2] text-[11px] font-bold uppercase tracking-wider mb-2">
            <Sparkles size={13} />
            PSI09 Autonomous Software Engineering Agent
          </div>
          <h2 className="text-2xl font-bold text-[#182033] tracking-tight">
            Welcome to CodePilot AI
          </h2>
          <p className="text-[#68738A] text-[14px] mt-1 max-w-2xl leading-relaxed">
            Autonomous repository investigation, minimal patch synthesis, and strict evidence-based verification.
            Powered by the <strong className="text-[#182033]">Regression Guardian</strong> to catch regressions before they ship.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => navigate('/analysis/new')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#5B5CE2] hover:bg-[#4F50D6] text-white text-[13px] font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <PlayCircle size={16} />
            <span>New Analysis</span>
          </button>
          <button
            onClick={() => navigate('/projects')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#F7F8FC] hover:bg-[#E6E9F2] text-[#182033] border border-[#E6E9F2] text-[13px] font-semibold transition-colors cursor-pointer"
          >
            <FolderGit2 size={16} />
            <span>Manage Repos</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-[#E6E9F2] shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[12px] font-semibold text-[#68738A] uppercase tracking-wider">Analysis Tasks</span>
            <div className="w-8 h-8 rounded-lg bg-[#5B5CE2]/10 text-[#5B5CE2] flex items-center justify-center">
              <PlayCircle size={17} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#182033] mt-2">{totalTasks}</div>
          <p className="text-[11px] text-[#68738A] mt-1">Total bug investigations</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E6E9F2] shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[12px] font-semibold text-[#68738A] uppercase tracking-wider">Patches Proposed</span>
            <div className="w-8 h-8 rounded-lg bg-[#3983E6]/10 text-[#3983E6] flex items-center justify-center">
              <GitPullRequest size={17} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#182033] mt-2">{patchesProposed}</div>
          <p className="text-[11px] text-[#68738A] mt-1">Minimal code fixes</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E6E9F2] shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[12px] font-semibold text-[#68738A] uppercase tracking-wider">Verified Fixes</span>
            <div className="w-8 h-8 rounded-lg bg-[#159A72]/10 text-[#159A72] flex items-center justify-center">
              <CheckCircle2 size={17} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#159A72] mt-2">{verifiedFixes}</div>
          <p className="text-[11px] text-[#68738A] mt-1">Certified 0 regressions</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E6E9F2] shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[12px] font-semibold text-[#68738A] uppercase tracking-wider">Regressions Caught</span>
            <div className="w-8 h-8 rounded-lg bg-[#D94F62]/10 text-[#D94F62] flex items-center justify-center">
              <ShieldCheck size={17} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#D94F62] mt-2">{regressionFailures}</div>
          <p className="text-[11px] text-[#68738A] mt-1">Guardian protected builds</p>
        </div>
      </div>

      {/* Main Grid: Projects & Verification Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-7">
        {/* Recent Projects (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-[#E6E9F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-[16px] font-bold text-[#182033]">Active Repositories</h3>
              <p className="text-[12px] text-[#68738A]">Scanned Python workspaces</p>
            </div>
            <button
              onClick={() => navigate('/projects')}
              className="text-[12px] font-semibold text-[#5B5CE2] hover:underline flex items-center gap-1 cursor-pointer"
            >
              View all <ArrowRight size={13} />
            </button>
          </div>

          {projects.length === 0 ? (
            <div className="text-center py-10 border border-dashed border-[#E6E9F2] rounded-xl bg-[#F7F8FC]">
              <FolderGit2 size={36} className="mx-auto text-[#68738A]/50 mb-2" />
              <p className="text-[14px] font-semibold text-[#182033]">No projects uploaded yet</p>
              <p className="text-[12px] text-[#68738A] mt-1">Upload a Python repository or use the demo project to get started.</p>
              <button
                onClick={() => navigate('/projects')}
                className="mt-4 px-4 py-2 bg-[#5B5CE2] text-white rounded-lg text-[12px] font-semibold cursor-pointer"
              >
                Upload Project
              </button>
            </div>
          ) : (
            <div className="divide-y divide-[#E6E9F2]">
              {projects.slice(0, 4).map((p) => (
                <div
                  key={p.id}
                  onClick={() => navigate(`/projects/${p.id}`)}
                  className="py-3.5 flex items-center justify-between hover:bg-[#F7F8FC] px-2 rounded-lg transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#5B5CE2]/10 text-[#5B5CE2] flex items-center justify-center font-bold text-[12px]">
                      PY
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-[#182033] text-[13px]">{p.name}</span>
                        {p.source_type === 'demo' && (
                          <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#5B5CE2]/10 text-[#5B5CE2]">
                            DEMO
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-[#68738A]">
                        {p.file_count} files discovered • Python
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-[#68738A] text-[12px]">
                    <Clock size={12} />
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Verification Summary Chart (1 col) */}
        <div className="bg-white rounded-xl border border-[#E6E9F2] p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#182033] font-bold text-[16px]">
              <TrendingUp size={18} className="text-[#5B5CE2]" />
              <h3>Verification Pipeline</h3>
            </div>
            <p className="text-[12px] text-[#68738A] mt-0.5 mb-4">Pipeline conversion & regression rate</p>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 9 }} interval={0} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                <Bar dataKey="count" fill="#5B5CE2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="p-3 bg-[#F7F8FC] rounded-lg border border-[#E6E9F2] text-[11px] text-[#68738A] mt-4">
            Regression Guardian guarantees that <strong>100%</strong> of accepted fixes maintain zero regressions across all baseline tests.
          </div>
        </div>
      </div>

      {/* Recent Agent Runs */}
      <div className="bg-white rounded-xl border border-[#E6E9F2] p-6 shadow-xs">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-[16px] font-bold text-[#182033]">Recent Agent Bug Runs</h3>
            <p className="text-[12px] text-[#68738A]">Live status of automated repair tasks</p>
          </div>
          <button
            onClick={() => navigate('/activity')}
            className="text-[12px] font-semibold text-[#5B5CE2] hover:underline flex items-center gap-1 cursor-pointer"
          >
            Audit Log <ArrowRight size={13} />
          </button>
        </div>

        {tasks.length === 0 ? (
          <div className="text-center py-8 text-[#68738A] text-[13px]">
            No bug analysis tasks started yet. Launch an analysis or run the demo project!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#E6E9F2] text-[11px] uppercase tracking-wider text-[#68738A]">
                  <th className="pb-3 font-semibold">Task ID</th>
                  <th className="pb-3 font-semibold">Repository</th>
                  <th className="pb-3 font-semibold">Bug Description</th>
                  <th className="pb-3 font-semibold">Workflow Status</th>
                  <th className="pb-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E6E9F2]">
                {tasks.slice(0, 5).map((t) => (
                  <tr key={t.id} className="hover:bg-[#F7F8FC] transition-colors">
                    <td className="py-3 font-mono text-[12px] text-[#68738A]">#{t.id}</td>
                    <td className="py-3 font-semibold text-[#182033]">{t.project_name || `Project #${t.project_id}`}</td>
                    <td className="py-3 text-[#182033] max-w-xs truncate">{t.bug_title}</td>
                    <td className="py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                        t.status === 'verified'
                          ? 'bg-[#159A72]/10 text-[#159A72]'
                          : t.status === 'regression_failed'
                          ? 'bg-[#D94F62]/10 text-[#D94F62]'
                          : t.status === 'patch_ready'
                          ? 'bg-[#3983E6]/10 text-[#3983E6]'
                          : 'bg-[#D99522]/10 text-[#D99522]'
                      }`}>
                        {t.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => navigate('/patches')}
                        className="text-[12px] font-semibold text-[#5B5CE2] hover:underline cursor-pointer"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

