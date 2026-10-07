import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  PlayCircle,
  Activity,
  GitPullRequest,
  ShieldCheck,
  FileCheck,
  History,
  Settings,
  Cpu,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { api, HealthInfo } from '../../services/api';

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/projects', label: 'Projects', icon: FolderGit2 },
  { to: '/analysis/new', label: 'New Analysis', icon: PlayCircle },
  { to: '/activity', label: 'Agent Activity', icon: Activity },
  { to: '/patches', label: 'Patch Review', icon: GitPullRequest },
  { to: '/regression', label: 'Regression Guardian', icon: ShieldCheck, highlight: true },
  { to: '/reports', label: 'Verification Reports', icon: FileCheck },
  { to: '/history', label: 'Fix History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const [health, setHealth] = useState<HealthInfo | null>(null);

  useEffect(() => {
    const fetchHealth = () => {
      api.get('/health')
        .then(res => setHealth(res.data))
        .catch(() => setHealth(null));
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="w-64 bg-white border-r border-[#E6E9F2] flex flex-col h-screen fixed left-0 top-0 select-none z-30">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#E6E9F2]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-[#5B5CE2] to-[#7C73E6] flex items-center justify-center text-white shadow-sm">
            {/* Original Connected-Node / Code-Bracket SVG Logo */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m7 8-4 4 4 4" />
              <path d="m17 8 4 4-4 4" />
              <circle cx="12" cy="12" r="2.5" />
              <path d="M12 4v4" />
              <path d="M12 16v4" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-[#182033] text-[16px] tracking-tight">CodePilot</span>
              <span className="font-semibold text-[#5B5CE2] text-[14px]">AI</span>
            </div>
            <div className="text-[10px] uppercase font-bold tracking-wider text-[#68738A] bg-[#F7F8FC] px-1.5 py-0.5 rounded border border-[#E6E9F2] inline-block mt-0.5">
              PSI09 AGENT
            </div>
          </div>
        </div>
        <p className="text-[11px] text-[#68738A] mt-2.5 font-medium leading-relaxed">
          Autonomous Software Engineering & Regression Guardian
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-[13px] font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-[#5B5CE2]/10 text-[#5B5CE2] font-semibold border-l-3 border-[#5B5CE2]'
                    : 'text-[#68738A] hover:text-[#182033] hover:bg-[#F7F8FC]'
                } ${item.highlight ? 'relative' : ''}`
              }
            >
              <Icon size={17} className="shrink-0" />
              <span>{item.label}</span>
              {item.highlight && (
                <span className="ml-auto w-2 h-2 rounded-full bg-[#159A72]" title="Core Innovation" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Status Footer */}
      <div className="p-3.5 border-t border-[#E6E9F2] bg-[#F7F8FC]/50 space-y-2 text-[11px]">
        {/* Execution Mode */}
        <div className="flex items-center justify-between py-1 px-2 rounded bg-white border border-[#E6E9F2]">
          <span className="text-[#68738A] flex items-center gap-1.5">
            <Cpu size={13} className="text-[#5B5CE2]" /> Sandbox
          </span>
          <span className="font-semibold text-[#182033] uppercase text-[10px] tracking-wide">
            {health?.execution_mode === 'docker' ? 'Docker Isolated' : 'Safe Subprocess'}
          </span>
        </div>

        {/* AI Provider Status */}
        <div className="flex items-center justify-between py-1 px-2 rounded bg-white border border-[#E6E9F2]">
          <span className="text-[#68738A] flex items-center gap-1.5">
            {health?.ai_provider?.configured ? (
              <CheckCircle2 size={13} className="text-[#159A72]" />
            ) : (
              <AlertCircle size={13} className="text-[#D99522]" />
            )}
            AI Engine
          </span>
          <span className="font-medium text-[#182033] truncate max-w-[100px]" title={health?.ai_provider?.model}>
            {health?.ai_provider?.configured ? health.ai_provider.provider.toUpperCase() : 'AST Heuristics'}
          </span>
        </div>

        {/* Version */}
        <div className="flex items-center justify-between text-[#68738A] px-1 pt-1">
          <span>Engine Build</span>
          <span className="font-mono text-[10px] text-[#68738A]">{health?.version || 'v1.0.0-hackathon'}</span>
        </div>
      </div>
    </aside>
  );
};

