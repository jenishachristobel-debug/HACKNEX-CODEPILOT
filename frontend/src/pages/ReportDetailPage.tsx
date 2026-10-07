import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileCheck,
  Download,
  ArrowLeft,
  ShieldCheck,
  Code2,
  FileText
} from 'lucide-react';
import { api } from '../services/api';

export const ReportDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api.get(`/reports/${id}`)
      .then(res => setReport(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleDownload = (format: 'markdown' | 'json') => {
    window.open(`/api/reports/${id}/export?format=${format}`, '_blank');
  };

  if (loading) {
    return <div className="text-center py-20 text-[#68738A]">Loading verification report...</div>;
  }

  if (!report) {
    return (
      <div className="text-center py-20 text-[#68738A]">
        Report not found.
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/reports')}
            className="flex items-center gap-1.5 text-[12px] font-semibold text-[#68738A] hover:text-[#182033] mb-1.5 cursor-pointer"
          >
            <ArrowLeft size={14} /> Back to Reports
          </button>
          <div className="flex items-center gap-2.5">
            <h2 className="text-xl font-bold text-[#182033]">Verification Report #{report.id}</h2>
            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
              report.classification === 'FIX_VERIFIED'
                ? 'bg-[#159A72]/10 text-[#159A72]'
                : 'bg-[#D94F62]/10 text-[#D94F62]'
            }`}>
              {report.classification}
            </span>
          </div>
          <p className="text-[13px] text-[#68738A] mt-0.5">
            {report.project_name} • {report.bug_title}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => handleDownload('markdown')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F7F8FC] hover:bg-[#E6E9F2] text-[#182033] border border-[#E6E9F2] rounded-xl text-[12px] font-semibold cursor-pointer"
          >
            <Download size={14} />
            <span>Export Markdown</span>
          </button>
          <button
            onClick={() => handleDownload('json')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#5B5CE2] hover:bg-[#4F50D6] text-white rounded-xl text-[12px] font-semibold cursor-pointer"
          >
            <Download size={14} />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Markdown Document Display */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-8 shadow-xs">
        <pre className="font-mono text-[13px] text-[#182033] whitespace-pre-wrap leading-relaxed overflow-x-auto bg-[#F7F8FC] p-6 rounded-xl border border-[#E6E9F2]">
          {report.markdown_report}
        </pre>
      </div>
    </div>
  );
};

