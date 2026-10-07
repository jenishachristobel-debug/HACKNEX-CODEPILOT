import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Sparkles, Plus, CheckCircle, ShieldAlert, Terminal } from 'lucide-react';
import { api, formatApiError } from '../../services/api';

export const Topbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleLoadDemo = async () => {
    try {
      setLoadingDemo(true);
      const res = await api.post('/projects/demo/load');
      const project = res.data.project;
      setToastMessage(`Loaded "${project.name}" demo repository!`);
      setTimeout(() => setToastMessage(null), 4000);
      navigate(`/projects/${project.id}`);
    } catch (err: any) {
      alert(formatApiError(err, 'Failed to load demo project. Check the backend logs.'));
    } finally {
      setLoadingDemo(false);
    }
  };

  const getPageTitle = () => {
    const p = location.pathname;
    if (p === '/') return 'System Overview';
    if (p.startsWith('/projects')) return 'Project Intelligence & Source Browser';
    if (p.startsWith('/analysis/new')) return 'New Autonomous Analysis';
    if (p.startsWith('/activity')) return 'Agent Activity & Audit Trail';
    if (p.startsWith('/patches')) return 'Patch Review & Unified Diff';
    if (p.startsWith('/regression')) return 'Regression Guardian Verification Engine';
    if (p.startsWith('/reports')) return 'Evidence-Based Verification Reports';
    if (p.startsWith('/history')) return 'Fix History & Project Memory';
    if (p.startsWith('/settings')) return 'System & Model Settings';
    return 'CodePilot AI';
  };

  return (
    <header className="h-16 bg-white border-b border-[#E6E9F2] fixed top-0 right-0 left-64 z-20 flex items-center justify-between px-8 select-none">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-[17px] font-bold text-[#182033] tracking-tight">{getPageTitle()}</h1>
          <p className="text-[12px] text-[#68738A]">
            Fix the bug. Verify the change. Trust the evidence.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {toastMessage && (
          <div className="flex items-center gap-2 bg-[#159A72]/10 border border-[#159A72]/30 text-[#159A72] text-[12px] font-semibold px-3 py-1.5 rounded-lg animate-fade-in">
            <CheckCircle size={14} />
            <span>{toastMessage}</span>
          </div>
        )}

        <button
          onClick={handleLoadDemo}
          disabled={loadingDemo}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-[13px] font-semibold bg-[#F7F8FC] hover:bg-[#E6E9F2] text-[#182033] border border-[#E6E9F2] transition-colors cursor-pointer disabled:opacity-50"
          title="Instant zero-setup sample with reproducible boundary bug"
        >
          <Sparkles size={15} className="text-[#5B5CE2]" />
          <span>{loadingDemo ? 'Provisioning...' : 'Load Demo Project'}</span>
        </button>

        <button
          onClick={() => navigate('/analysis/new')}
          className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-[13px] font-semibold bg-[#5B5CE2] hover:bg-[#4F50D6] text-white shadow-sm transition-colors cursor-pointer"
        >
          <Plus size={16} />
          <span>New Analysis</span>
        </button>
      </div>
    </header>
  );
};

