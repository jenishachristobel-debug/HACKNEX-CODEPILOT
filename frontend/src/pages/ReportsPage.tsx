import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileCheck,
  Download,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  FileText
} from 'lucide-react';
import { api } from '../services/api';

export const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/reports')
      .then(res => setReports(res.data.reports || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = (id: number, format: 'markdown' | 'json') => {
    window.open(`/api/reports/${id}/export?format=${format}`, '_blank');
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#182033] flex items-center gap-2">
            <FileCheck size={20} className="text-[#5B5CE2]" /> Evidence-Based Verification Reports
          </h2>
          <p className="text-[13px] text-[#68738A] mt-0.5">
            Cryptographically grounded verification evidence with test logs, diffs, and sandbox certifications
          </p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-[#68738A]">Loading reports...</div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-12 text-center shadow-xs">
          <FileText size={40} className="mx-auto text-[#68738A]/50 mb-3" />
          <h3 className="text-[16px] font-bold text-[#182033]">No Verification Reports Yet</h3>
          <p className="text-[13px] text-[#68738A] mt-1 mb-4">
            Reports are automatically generated when patches undergo Regression Guardian verification.
          </p>
          <button
            onClick={() => navigate('/analysis/new')}
            className="px-4 py-2 bg-[#5B5CE2] hover:bg-[#4F50D6] text-white rounded-lg text-[13px] font-semibold cursor-pointer"
          >
            Run an Analysis
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] shadow-xs overflow-hidden">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="bg-[#F7F8FC] border-b border-[#E6E9F2] text-[11px] uppercase tracking-wider text-[#68738A]">
                <th className="py-3 px-4 font-semibold">Report ID</th>
                <th className="py-3 px-4 font-semibold">Repository</th>
                <th className="py-3 px-4 font-semibold">Bug Title</th>
                <th className="py-3 px-4 font-semibold">Classification</th>
                <th className="py-3 px-4 font-semibold">Date</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E6E9F2]">
              {reports.map((r) => (
                <tr key={r.id} className="hover:bg-[#F7F8FC]/50 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-[12px] text-[#68738A]">#{r.id}</td>
                  <td className="py-3.5 px-4 font-semibold text-[#182033]">{r.project_name}</td>
                  <td className="py-3.5 px-4 text-[#182033] max-w-xs truncate">{r.bug_title}</td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${
                      r.classification === 'FIX_VERIFIED'
                        ? 'bg-[#159A72]/10 text-[#159A72]'
                        : 'bg-[#D94F62]/10 text-[#D94F62]'
                    }`}>
                      {r.classification}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-[#68738A] text-[12px]">
                    {new Date(r.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleDownload(r.id, 'markdown')}
                        className="px-2.5 py-1 text-[11px] font-semibold border border-[#E6E9F2] bg-[#F7F8FC] hover:bg-[#E6E9F2] text-[#182033] rounded cursor-pointer"
                        title="Download Markdown Report"
                      >
                        MD
                      </button>
                      <button
                        onClick={() => handleDownload(r.id, 'json')}
                        className="px-2.5 py-1 text-[11px] font-semibold border border-[#E6E9F2] bg-[#F7F8FC] hover:bg-[#E6E9F2] text-[#182033] rounded cursor-pointer"
                        title="Download JSON Report"
                      >
                        JSON
                      </button>
                      <button
                        onClick={() => navigate(`/reports/${r.id}`)}
                        className="px-3 py-1 bg-[#5B5CE2]/10 text-[#5B5CE2] hover:bg-[#5B5CE2]/20 font-semibold rounded text-[12px] cursor-pointer"
                      >
                        Inspect
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

