import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  Upload,
  Sparkles,
  Trash2,
  Clock,
  FileCode,
  AlertCircle,
  CheckCircle2,
  Plus
} from 'lucide-react';
import { api, ProjectItem, formatApiError } from '../services/api';

export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const extractErrorMessage = (err: any): string => {
    return formatApiError(err, 'Could not contact the repository upload service.');
  };

  const fetchProjects = () => {
    setLoading(true);
    api.get('/projects')
      .then(res => setProjects(res.data.projects || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (uploading || !uploadFile || !projectName.trim()) return;

    // Client-side archive size guard (25MB)
    if (uploadFile.size > 25 * 1024 * 1024) {
      setUploadError('Archive size exceeds maximum allowed limit of 25MB.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('name', projectName.trim());
    formData.append('project_name', projectName.trim());

    try {
      const res = await api.post('/projects/upload', formData, {
        timeout: 120000,
      });
      const projectId = res.data?.project?.id;
      setUploadSuccess(`Repository uploaded & scanned! (Project #${projectId})`);
      fetchProjects();
      setTimeout(() => {
        setShowUploadModal(false);
        setProjectName('');
        setUploadFile(null);
        setUploadSuccess(null);
        if (projectId) {
          navigate(`/projects/${projectId}`);
        }
      }, 700);
    } catch (err: any) {
      setUploadError(extractErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleLoadDemo = async () => {
    try {
      const res = await api.post('/projects/demo/load');
      fetchProjects();
      navigate(`/projects/${res.data.project.id}`);
    } catch (err: any) {
      alert(formatApiError(err, 'Error loading demo project. Check the backend logs.'));
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`Are you sure you want to delete repository "${name}"? This will remove all associated tasks and sandboxes.`)) {
      return;
    }
    try {
      await api.delete(`/projects/${id}`);
      fetchProjects();
    } catch (err) {
      alert('Failed to delete project');
    }
  };

  return (
    <div className="space-y-7 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#182033] tracking-tight">Repository Management</h2>
          <p className="text-[13px] text-[#68738A] mt-0.5">
            Safely scanned Python repositories isolated for autonomous engineering tasks
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleLoadDemo}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-[#E6E9F2] text-[#182033] text-[13px] font-semibold hover:bg-[#F7F8FC] shadow-2xs transition-colors cursor-pointer"
          >
            <Sparkles size={15} className="text-[#5B5CE2]" />
            <span>Load Demo Repository</span>
          </button>

          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#5B5CE2] hover:bg-[#4F50D6] text-white text-[13px] font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <Upload size={15} />
            <span>Upload ZIP Repository</span>
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="text-center py-16 text-[#68738A]">Scanning repositories...</div>
      ) : projects.length === 0 ? (
        <div className="bg-white rounded-2xl border border-[#E6E9F2] p-12 text-center max-w-lg mx-auto shadow-xs">
          <FolderGit2 size={42} className="mx-auto text-[#68738A]/50 mb-3" />
          <h3 className="text-[16px] font-bold text-[#182033]">No Repositories Discovered</h3>
          <p className="text-[13px] text-[#68738A] mt-1 mb-5">
            Upload a Python repository in ZIP format, or load the pre-configured ShopPilot Pricing Engine demo project.
          </p>
          <div className="flex justify-center gap-3">
            <button
              onClick={handleLoadDemo}
              className="px-4 py-2 bg-[#F7F8FC] border border-[#E6E9F2] text-[#182033] rounded-lg text-[13px] font-semibold cursor-pointer hover:bg-[#E6E9F2]"
            >
              Load Demo Project
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2 bg-[#5B5CE2] text-white rounded-lg text-[13px] font-semibold cursor-pointer hover:bg-[#4F50D6]"
            >
              Upload Archive
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((p) => (
            <div
              key={p.id}
              className="bg-white rounded-xl border border-[#E6E9F2] p-5 shadow-xs hover:border-[#5B5CE2]/40 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-[#5B5CE2]/10 text-[#5B5CE2] flex items-center justify-center font-bold text-[13px]">
                      PY
                    </div>
                    <div>
                      <h4 className="font-bold text-[#182033] text-[15px] hover:text-[#5B5CE2] cursor-pointer"
                          onClick={() => navigate(`/projects/${p.id}`)}>
                        {p.name}
                      </h4>
                      <span className="text-[11px] text-[#68738A]">Python • {p.file_count} files</span>
                    </div>
                  </div>

                  {p.source_type === 'demo' && (
                    <span className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-[#5B5CE2]/10 text-[#5B5CE2]">
                      DEMO REPO
                    </span>
                  )}
                </div>

                <p className="text-[12px] text-[#68738A] line-clamp-2 mb-4">
                  {p.description || 'Python codebase indexed with AST symbol inspection and test discovery.'}
                </p>
              </div>

              <div className="border-t border-[#E6E9F2] pt-3 flex items-center justify-between text-[12px]">
                <span className="text-[#68738A] flex items-center gap-1 text-[11px]">
                  <Clock size={12} /> {new Date(p.created_at).toLocaleDateString()}
                </span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDelete(p.id, p.name)}
                    className="p-1.5 text-[#68738A] hover:text-[#D94F62] hover:bg-[#D94F62]/10 rounded transition-colors cursor-pointer"
                    title="Delete repository"
                  >
                    <Trash2 size={15} />
                  </button>
                  <button
                    onClick={() => navigate(`/projects/${p.id}`)}
                    className="px-3 py-1 bg-[#5B5CE2]/10 text-[#5B5CE2] hover:bg-[#5B5CE2]/20 font-semibold rounded text-[12px] transition-colors cursor-pointer"
                  >
                    Explore
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-[#182033]/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-[#E6E9F2] animate-scale-in">
            <h3 className="text-[17px] font-bold text-[#182033] mb-1">Upload Python Repository</h3>
            <p className="text-[12px] text-[#68738A] mb-5">
              Archive will be safely validated against path traversal, symlinks, and sensitive environment keys.
            </p>

            {uploadError && (
              <div className="mb-4 p-3 rounded-lg bg-[#D94F62]/10 border border-[#D94F62]/30 text-[#D94F62] text-[12px] flex items-start gap-2">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{uploadError}</span>
              </div>
            )}

            {uploadSuccess && (
              <div className="mb-4 p-3 rounded-lg bg-[#22C55E]/10 border border-[#22C55E]/30 text-[#16A34A] text-[12px] flex items-start gap-2">
                <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
                <span>{uploadSuccess}</span>
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-[12px] font-semibold text-[#182033] mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MyService Repo"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full px-3 py-2 text-[13px] rounded-lg border border-[#E6E9F2] focus:border-[#5B5CE2] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-[#182033] mb-1">ZIP File</label>
                <input
                  type="file"
                  required
                  accept=".zip"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-[12px] text-[#68738A] file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-[12px] file:font-semibold file:bg-[#5B5CE2]/10 file:text-[#5B5CE2] hover:file:bg-[#5B5CE2]/20"
                />
                <p className="text-[11px] text-[#68738A] mt-1">Max 25MB archive. `.git` and `.env` are automatically ignored.</p>
              </div>

              <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E6E9F2]">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 text-[13px] font-medium text-[#68738A] hover:bg-[#F7F8FC] rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-5 py-2 text-[13px] font-semibold bg-[#5B5CE2] hover:bg-[#4F50D6] text-white rounded-lg disabled:opacity-50 cursor-pointer shadow-xs"
                >
                  {uploading ? 'Validating & Scanning...' : 'Upload & Scan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

