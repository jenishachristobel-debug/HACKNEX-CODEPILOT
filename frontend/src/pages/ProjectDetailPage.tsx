import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import {
  Folder,
  FileCode,
  FileText,
  ChevronRight,
  ChevronDown,
  PlayCircle,
  Code2,
  CheckCircle,
  AlertTriangle,
  Layers,
  ArrowLeft,
  Download
} from 'lucide-react';
import { api, ProjectItem, downloadCorrectedZip } from '../services/api';

interface TreeNode {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number;
  children?: TreeNode[];
}

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectItem | null>(null);
  const [scanData, setScanData] = useState<any>(null);
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [loadingFile, setLoadingFile] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Record<string, boolean>>({});
  const [downloading, setDownloading] = useState(false);

  const handleDownloadCorrected = async () => {
    if (!id || !project) return;
    setDownloading(true);
    try {
      await downloadCorrectedZip(project.id, project.name);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Download failed: Project may not have a verified fix yet.');
    } finally {
      setDownloading(false);
    }
  };

  useEffect(() => {
    if (!id) return;

    api.get(`/projects/${id}`)
      .then(res => {
        setProject(res.data.project);
        setScanData(res.data.scan);
      })
      .catch(console.error);

    api.get(`/projects/${id}/tree`)
      .then(res => {
        const fileTree = res.data.tree || [];
        setTree(fileTree);
        // Expand root directories automatically
        const initialExpanded: Record<string, boolean> = {};
        fileTree.forEach((node: TreeNode) => {
          if (node.is_dir) initialExpanded[node.path] = true;
        });
        setExpandedDirs(initialExpanded);

        // Select first non-dir file automatically
        const findFirstFile = (nodes: TreeNode[]): string | null => {
          for (const n of nodes) {
            if (!n.is_dir) return n.path;
            if (n.children) {
              const f = findFirstFile(n.children);
              if (f) return f;
            }
          }
          return null;
        };
        const first = findFirstFile(fileTree);
        if (first) {
          setSelectedFilePath(first);
          loadFile(first);
        }
      })
      .catch(console.error);
  }, [id]);

  const loadFile = (path: string) => {
    setSelectedFilePath(path);
    setLoadingFile(true);
    api.get(`/projects/${id}/files?path=${encodeURIComponent(path)}`)
      .then(res => setFileContent(res.data.content))
      .catch(() => setFileContent('# Error reading file content'))
      .finally(() => setLoadingFile(false));
  };

  const toggleDir = (dirPath: string) => {
    setExpandedDirs(prev => ({ ...prev, [dirPath]: !prev[dirPath] }));
  };

  const renderTree = (nodes: TreeNode[], depth = 0) => {
    return nodes.map((node) => {
      const isExpanded = !!expandedDirs[node.path];
      const isSelected = selectedFilePath === node.path;

      if (node.is_dir) {
        return (
          <div key={node.path} className="select-none">
            <div
              onClick={() => toggleDir(node.path)}
              style={{ paddingLeft: `${depth * 14 + 10}px` }}
              className="flex items-center gap-1.5 py-1 px-2 text-[12px] font-medium text-[#182033] hover:bg-[#F7F8FC] rounded cursor-pointer transition-colors"
            >
              {isExpanded ? <ChevronDown size={14} className="text-[#68738A]" /> : <ChevronRight size={14} className="text-[#68738A]" />}
              <Folder size={14} className="text-[#5B5CE2] shrink-0" />
              <span className="truncate">{node.name}</span>
            </div>
            {isExpanded && node.children && (
              <div>{renderTree(node.children, depth + 1)}</div>
            )}
          </div>
        );
      }

      return (
        <div
          key={node.path}
          onClick={() => loadFile(node.path)}
          style={{ paddingLeft: `${depth * 14 + 24}px` }}
          className={`flex items-center gap-2 py-1 px-2 text-[12px] rounded cursor-pointer transition-colors ${
            isSelected
              ? 'bg-[#5B5CE2]/15 text-[#5B5CE2] font-semibold'
              : 'text-[#68738A] hover:text-[#182033] hover:bg-[#F7F8FC]'
          }`}
        >
          <FileCode size={13} className={isSelected ? 'text-[#5B5CE2]' : 'text-[#68738A]'} />
          <span className="truncate">{node.name}</span>
        </div>
      );
    });
  };

  // Symbols for the currently selected file
  const activeSymbols = scanData?.symbols?.[selectedFilePath || ''] || null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Details Bar */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/projects')}
            className="flex items-center gap-1.5 text-[12px] font-semibold text-[#68738A] hover:text-[#182033] mb-1.5 cursor-pointer"
          >
            <ArrowLeft size={14} /> Back to Projects
          </button>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-[#182033]">{project?.name || 'Loading Project...'}</h2>
            {project?.source_type === 'demo' && (
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#5B5CE2]/10 text-[#5B5CE2]">
                DEMO REPO
              </span>
            )}
          </div>
          <p className="text-[13px] text-[#68738A] mt-0.5">
            {project?.description || 'Scanned Python repository ready for autonomous bug fix pipeline'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {project?.has_verified_fix && (
            <button
              onClick={handleDownloadCorrected}
              disabled={downloading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#159A72] hover:bg-[#128361] text-white text-[13px] font-semibold shadow-xs cursor-pointer transition-colors disabled:opacity-50"
            >
              <Download size={15} />
              <span>{downloading ? 'Downloading...' : 'Download Corrected ZIP'}</span>
            </button>
          )}
          <button
            onClick={() => navigate(`/analysis/new?projectId=${id}`)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#5B5CE2] hover:bg-[#4F50D6] text-white text-[13px] font-semibold shadow-xs cursor-pointer transition-colors"
          >
            <PlayCircle size={15} />
            <span>Investigate Bug on this Repo</span>
          </button>
        </div>
      </div>

      {/* Intelligence Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-[#E6E9F2]">
          <span className="text-[11px] font-semibold text-[#68738A] uppercase">Total Files</span>
          <div className="text-xl font-bold text-[#182033] mt-1">{scanData?.total_files || project?.file_count || 0}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-[#E6E9F2]">
          <span className="text-[11px] font-semibold text-[#68738A] uppercase">Python Files</span>
          <div className="text-xl font-bold text-[#5B5CE2] mt-1">{scanData?.python_files || 0}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-[#E6E9F2]">
          <span className="text-[11px] font-semibold text-[#68738A] uppercase">Discovered Tests</span>
          <div className="text-xl font-bold text-[#159A72] mt-1">{scanData?.test_files || 0}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-[#E6E9F2]">
          <span className="text-[11px] font-semibold text-[#68738A] uppercase">Syntax Errors</span>
          <div className="text-xl font-bold text-[#D94F62] mt-1">{scanData?.syntax_errors_count || 0}</div>
        </div>
      </div>

      {/* Repository Manifest Metadata */}
      {scanData?.manifest && Object.keys(scanData.manifest).length > 0 && (
        <div className="bg-white p-4 rounded-xl border border-[#E6E9F2] flex flex-wrap items-center justify-between gap-3 text-[12px] shadow-2xs">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-[#68738A] uppercase text-[10px]">Repository Manifest:</span>
            <span className="px-2 py-0.5 rounded bg-[#5B5CE2]/10 text-[#5B5CE2] font-semibold">
              {scanData.manifest.languages?.join(', ') || 'Python'}
            </span>
            <span className="px-2 py-0.5 rounded bg-[#159A72]/10 text-[#159A72] font-semibold">
              Framework: {scanData.manifest.test_framework || 'pytest'}
            </span>
            <span className="px-2 py-0.5 rounded bg-[#3983E6]/10 text-[#3983E6] font-semibold">
              Package: {scanData.manifest.package_manager || 'pip'}
            </span>
          </div>
          <div className="text-[#68738A] text-[11px]">
            Entry Points: <span className="font-mono text-[#182033] font-semibold">{scanData.manifest.entry_points?.join(', ') || 'N/A'}</span>
          </div>
        </div>
      )}

      {/* Code Browser Shell: File Tree (Left) + Monaco Editor (Right) */}
      <div className="bg-white rounded-2xl border border-[#E6E9F2] shadow-xs grid grid-cols-1 md:grid-cols-12 overflow-hidden h-[620px]">
        {/* Left: File Tree */}
        <div className="md:col-span-4 border-r border-[#E6E9F2] flex flex-col h-full bg-[#F7F8FC]/30">
          <div className="p-3 border-b border-[#E6E9F2] bg-white flex items-center justify-between">
            <span className="text-[12px] font-bold text-[#182033] flex items-center gap-1.5">
              <Layers size={14} className="text-[#5B5CE2]" /> Workspace Explorer
            </span>
            <span className="text-[11px] text-[#68738A] font-mono">{tree.length} top-level</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {tree.length === 0 ? (
              <div className="text-center py-10 text-[12px] text-[#68738A]">No files discovered</div>
            ) : (
              renderTree(tree)
            )}
          </div>
        </div>

        {/* Right: Monaco Code Viewer & AST Symbols */}
        <div className="md:col-span-8 flex flex-col h-full">
          {/* File Tab Header */}
          <div className="p-3 border-b border-[#E6E9F2] bg-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Code2 size={15} className="text-[#5B5CE2]" />
              <span className="font-mono text-[12px] font-semibold text-[#182033]">
                {selectedFilePath || 'Select a file to inspect'}
              </span>
            </div>
            {selectedFilePath?.endsWith('.py') && (
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#159A72]/10 text-[#159A72]">
                AST INDEXED
              </span>
            )}
          </div>

          {/* Monaco Editor */}
          <div className="flex-1 relative bg-white">
            {loadingFile ? (
              <div className="h-full flex items-center justify-center text-[#68738A] text-[13px]">
                Loading source code...
              </div>
            ) : (
              <Editor
                height="100%"
                language={selectedFilePath?.endsWith('.py') ? 'python' : 'plaintext'}
                value={fileContent}
                theme="light"
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  fontSize: 13,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  wordWrap: 'on'
                }}
              />
            )}
          </div>

          {/* Bottom Symbol Tray if available */}
          {activeSymbols && (
            <div className="p-3 border-t border-[#E6E9F2] bg-[#F7F8FC] text-[11px] text-[#68738A] flex flex-wrap gap-4 items-center">
              <div>
                <strong className="text-[#182033]">Functions:</strong>{' '}
                {activeSymbols.functions?.length > 0
                  ? activeSymbols.functions.map((f: any) => f.name).join(', ')
                  : 'None'}
              </div>
              <div>
                <strong className="text-[#182033]">Classes:</strong>{' '}
                {activeSymbols.classes?.length > 0
                  ? activeSymbols.classes.map((c: any) => c.name).join(', ')
                  : 'None'}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

