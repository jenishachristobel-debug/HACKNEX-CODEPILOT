import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Activity,
  CheckCircle2,
  Clock,
  ShieldCheck,
  GitPullRequest,
  Search,
  Cpu,
  Layers,
  ChevronRight
} from 'lucide-react';
import { api, TaskItem } from '../services/api';

export const AgentActivityPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const taskIdParam = searchParams.get('taskId');

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(
    taskIdParam ? parseInt(taskIdParam, 10) : null
  );
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
    api.get(`/tasks/${selectedTaskId}/activity`)
      .then(res => setActivities(res.data.activity || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedTaskId]);

  const getEventIcon = (type: string) => {
    if (type.includes('UPLOAD')) return <Layers size={16} className="text-[#5B5CE2]" />;
    if (type.includes('ANALYSIS') || type.includes('INVESTIGATION')) return <Search size={16} className="text-[#3983E6]" />;
    if (type.includes('PATCH')) return <GitPullRequest size={16} className="text-[#D99522]" />;
    if (type.includes('VERIFICATION') || type.includes('GUARDIAN')) return <ShieldCheck size={16} className="text-[#159A72]" />;
    return <Cpu size={16} className="text-[#68738A]" />;
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#182033] flex items-center gap-2">
            <Activity size={20} className="text-[#5B5CE2]" /> Agent Activity & Audit Trail
          </h2>
          <p className="text-[13px] text-[#68738A] mt-0.5">
            Cryptographic sequence of actions performed by CodePilot autonomous agents
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-[12px] font-semibold text-[#68738A]">Task:</label>
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
        <div className="text-center py-20 text-[#68738A]">Querying agent event stream...</div>
      ) : activities.length === 0 ? (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-12 text-center text-[#68738A]">
          No audit logs recorded for this task yet.
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-6 shadow-xs">
          <div className="relative pl-6 border-l-2 border-[#E6E9F2] space-y-7 ml-3">
            {activities.map((act) => (
              <div key={act.id} className="relative group">
                {/* Dot Icon */}
                <div className="absolute -left-[35px] top-0.5 w-7 h-7 rounded-full bg-white border-2 border-[#E6E9F2] group-hover:border-[#5B5CE2] flex items-center justify-center transition-colors">
                  {getEventIcon(act.event_type)}
                </div>

                {/* Event Content */}
                <div className="bg-[#F7F8FC] p-4 rounded-xl border border-[#E6E9F2] hover:border-[#5B5CE2]/40 transition-colors">
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[13px] text-[#182033] font-mono">
                        {act.event_type}
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-white border border-[#E6E9F2] text-[#68738A]">
                        {act.actor}
                      </span>
                    </div>
                    <span className="text-[11px] text-[#68738A] flex items-center gap-1 font-mono">
                      <Clock size={11} />
                      {new Date(act.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  {act.details && Object.keys(act.details).length > 0 && (
                    <pre className="text-[11px] font-mono bg-white p-2.5 rounded-lg border border-[#E6E9F2] text-[#182033] mt-2 overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(act.details, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

