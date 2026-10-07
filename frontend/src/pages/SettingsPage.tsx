import React, { useEffect, useState } from 'react';
import {
  Settings,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Key,
  Sliders,
  Terminal
} from 'lucide-react';
import { api, HealthInfo } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = () => {
    setLoading(true);
    api.get('/health')
      .then(res => setHealth(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-[#182033] flex items-center gap-2">
          <Settings size={20} className="text-[#5B5CE2]" /> Platform Configuration & Telemetry
        </h2>
        <p className="text-[13px] text-[#68738A] mt-0.5">
          Execution environment, AI model reasoning mode, and safety policy parameters
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-6 shadow-xs space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#E6E9F2]">
          <h3 className="text-[15px] font-bold text-[#182033] flex items-center gap-2">
            <Sliders size={17} className="text-[#5B5CE2]" /> Runtime Parameters
          </h3>
          <button
            onClick={fetchHealth}
            className="flex items-center gap-1.5 px-3 py-1 bg-[#F7F8FC] hover:bg-[#E6E9F2] text-[#182033] rounded-lg text-[12px] font-semibold cursor-pointer transition-colors"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Health</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-[#E6E9F2] bg-[#F7F8FC]">
            <span className="text-[11px] font-semibold text-[#68738A] uppercase">Active Execution Engine</span>
            <div className="text-[15px] font-bold text-[#182033] mt-1 flex items-center gap-2">
              <Cpu size={16} className="text-[#5B5CE2]" />
              {health?.execution_mode === 'docker' ? 'Docker Isolated Container' : 'Safe Subprocess Sandbox'}
            </div>
            <p className="text-[11px] text-[#68738A] mt-1">
              Isolated workspace cloning with 30s timeouts and pytest allowlist policy.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-[#E6E9F2] bg-[#F7F8FC]">
            <span className="text-[11px] font-semibold text-[#68738A] uppercase">Reasoning Engine</span>
            <div className="text-[15px] font-bold text-[#182033] mt-1 flex items-center gap-2">
              {health?.ai_provider?.configured ? (
                <CheckCircle2 size={16} className="text-[#159A72]" />
              ) : (
                <AlertCircle size={16} className="text-[#D99522]" />
              )}
              {health?.ai_provider?.configured
                ? `Live LLM (${health.ai_provider.provider.toUpperCase()} - ${health.ai_provider.model})`
                : 'Offline AST Static Engine (Zero-Config)'}
            </div>
            <p className="text-[11px] text-[#68738A] mt-1">
              {health?.ai_provider?.message}
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[#E6E9F2] space-y-3">
          <h4 className="text-[13px] font-bold text-[#182033]">Safety & Retry Limits</h4>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 bg-[#F7F8FC] rounded-lg">
              <span className="text-[11px] text-[#68738A] block">Max Self-Repair Retries</span>
              <span className="text-lg font-bold text-[#182033]">2 attempts</span>
            </div>
            <div className="p-3 bg-[#F7F8FC] rounded-lg">
              <span className="text-[11px] text-[#68738A] block">Subprocess Timeout</span>
              <span className="text-lg font-bold text-[#182033]">30 seconds</span>
            </div>
            <div className="p-3 bg-[#F7F8FC] rounded-lg">
              <span className="text-[11px] text-[#68738A] block">Max Upload Archive</span>
              <span className="text-lg font-bold text-[#182033]">25 MB</span>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#5B5CE2]/5 border border-[#5B5CE2]/20 text-[12px] text-[#182033] space-y-2">
          <div className="font-bold text-[#5B5CE2] flex items-center gap-1.5">
            <Key size={14} /> AI Provider Credentials Guide
          </div>
          <p className="text-[#68738A]">
            To connect a live LLM model, configure your API key in the environment or <code className="bg-white px-1.5 py-0.5 rounded border text-[#182033]">.env</code> file:
          </p>
          <pre className="p-2.5 bg-white rounded-lg border border-[#E6E9F2] text-[11px] font-mono text-[#182033]">
            GEMINI_API_KEY=your_key_here
          </pre>
          <p className="text-[11px] text-[#68738A]">
            CodePilot works completely offline out of the box using its AST structural reasoning engine for fast, reproducible hackathon testing!
          </p>
        </div>
      </div>
    </div>
  );
};

