import React, { useEffect, useState } from 'react';
import {
  History,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  FileCode,
  Clock,
  Sparkles
} from 'lucide-react';
import { api, HistoryItem } from '../services/api';

export const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [search, setSearch] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchHistory = () => {
    setLoading(true);
    let url = `/history?`;
    if (search) url += `q=${encodeURIComponent(search)}&`;
    if (outcomeFilter) url += `outcome=${encodeURIComponent(outcomeFilter)}&`;

    api.get(url)
      .then(res => setHistory(res.data.history || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
  }, [search, outcomeFilter]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-[#182033] flex items-center gap-2">
          <History size={20} className="text-[#5B5CE2]" /> Fix History & Project Memory
        </h2>
        <p className="text-[13px] text-[#68738A] mt-0.5">
          Persistent memory of past bug diagnoses, applied patches, and Regression Guardian outcomes
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-4 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search size={15} className="absolute left-3 top-3 text-[#68738A]" />
          <input
            type="text"
            placeholder="Search by bug title, root cause, or repository..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-[13px] rounded-lg border border-[#E6E9F2] focus:border-[#5B5CE2] focus:outline-none"
          />
        </div>

        <select
          value={outcomeFilter}
          onChange={(e) => setOutcomeFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-[#E6E9F2] text-[13px] font-semibold text-[#182033] bg-white focus:outline-none"
        >
          <option value="">All Outcomes</option>
          <option value="FIX_VERIFIED">FIX_VERIFIED</option>
          <option value="REGRESSION_DETECTED">REGRESSION_DETECTED</option>
          <option value="VERIFICATION_FAILED">VERIFICATION_FAILED</option>
        </select>
      </div>

      {/* History Cards */}
      {loading ? (
        <div className="text-center py-20 text-[#68738A]">Querying project memory...</div>
      ) : history.length === 0 ? (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-12 text-center text-[#68738A]">
          No past fixes found matching criteria.
        </div>
      ) : (
        <div className="space-y-3.5">
          {history.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-xl border border-[#E6E9F2] p-5 shadow-xs hover:border-[#5B5CE2]/40 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[15px] text-[#182033]">{item.bug_title}</span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#F7F8FC] border border-[#E6E9F2] text-[#68738A]">
                    {item.project_name}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${
                    item.outcome === 'FIX_VERIFIED'
                      ? 'bg-[#159A72]/10 text-[#159A72]'
                      : 'bg-[#D94F62]/10 text-[#D94F62]'
                  }`}>
                    {item.outcome}
                  </span>
                  <span className="text-[11px] text-[#68738A] flex items-center gap-1">
                    <Clock size={11} /> {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="text-[12px] text-[#68738A] space-y-1 mt-2">
                <div>
                  <strong className="text-[#182033]">Root Cause:</strong> {item.root_cause_summary}
                </div>
                {item.target_file && (
                  <div>
                    <strong className="text-[#182033]">Target File:</strong>{' '}
                    <code className="text-[#5B5CE2] font-mono text-[11px] bg-[#5B5CE2]/5 px-1 rounded">
                      {item.target_file}
                    </code>
                  </div>
                )}
                {item.patch_summary && (
                  <div>
                    <strong className="text-[#182033]">Applied Fix:</strong> {item.patch_summary}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

