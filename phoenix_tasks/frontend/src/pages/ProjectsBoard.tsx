import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Plus, Trash2, CheckCircle2, Circle, MessageSquare, AlertCircle } from 'lucide-react';

interface ProjectsBoardProps {
  user: any;
}

export function ProjectsBoard({ user }: ProjectsBoardProps) {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showNewProj, setShowNewProj] = useState(false);
  const [newProjName, setNewProjName] = useState('');
  const [newProjDesc, setNewProjDesc] = useState('');

  const [showNewTask, setShowNewTask] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState('medium');

  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);
  const [newComment, setNewComment] = useState('');

  const canManageProjects = user?.role === 'admin' || user?.role === 'manager';

  const fetchProjects = async () => {
    try {
      const data = await api.projects.list();
      setProjects(data);
      if (data.length > 0 && !selectedProject) {
        setSelectedProject(data[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchTasks = async (projectId: number) => {
    try {
      const data = await api.tasks.list(projectId);
      setTasks(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      await fetchProjects();
      setLoading(false);
    }
    loadData();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchTasks(selectedProject.id);
    } else {
      setTasks([]);
    }
  }, [selectedProject]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjName.trim()) return;

    try {
      const res = await api.projects.create({ name: newProjName, description: newProjDesc });
      setProjects([...projects, res]);
      setSelectedProject(res);
      setNewProjName('');
      setNewProjDesc('');
      setShowNewProj(false);
    } catch (err) {
      alert('Error creating project. Check your role permissions.');
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !selectedProject) return;

    try {
      const res = await api.tasks.create(selectedProject.id, {
        title: newTaskTitle,
        description: newTaskDesc,
        priority: newTaskPriority,
      });
      setTasks([...tasks, res]);
      setNewTaskTitle('');
      setNewTaskDesc('');
      setNewTaskPriority('medium');
      setShowNewTask(false);
    } catch (err) {
      alert('Error creating task.');
    }
  };

  const handleDeleteProject = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this project and all its tasks?')) return;
    try {
      await api.projects.delete(id);
      const updated = projects.filter((p) => p.id !== id);
      setProjects(updated);
      setSelectedProject(updated[0] || null);
    } catch (err) {
      alert('Unauthorized or error deleting project.');
    }
  };

  const handleTaskClick = async (task: any) => {
    setSelectedTask(task);
    try {
      const c = await api.tasks.getComments(task.id);
      setComments(c);
    } catch (e) {
      setComments([]);
    }
  };

  const handleUpdateTaskStatus = async (task: any, newStatus: string) => {
    try {
      const res = await api.tasks.update(task.id, { status: newStatus });
      setTasks(tasks.map((t) => (t.id === task.id ? res : t)));
      if (selectedTask && selectedTask.id === task.id) {
        setSelectedTask(res);
      }
    } catch (err) {
      alert('Unauthorized to update this task.');
    }
  };

  const handleDeleteTask = async (task: any) => {
    if (!window.confirm('Delete this task?')) return;
    try {
      await api.tasks.delete(task.id);
      setTasks(tasks.filter((t) => t.id !== task.id));
      setSelectedTask(null);
    } catch (e) {
      alert('Unauthorized to delete this task.');
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !selectedTask) return;

    try {
      const res = await api.tasks.addComment(selectedTask.id, { content: newComment });
      setComments([...comments, res]);
      setNewComment('');
    } catch (e) {
      alert('Error adding comment.');
    }
  };

  const tasksByStatus = (status: string) => tasks.filter((t) => t.status === status);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950 text-slate-400">
        Loading board and tasks data...
      </div>
    );
  }

  return (
    <div className="flex-1 bg-slate-950 p-8 flex flex-col overflow-hidden text-slate-100 relative">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6 mb-8 shrink-0">
        <div className="flex items-center gap-4">
          <select
            value={selectedProject?.id || ''}
            onChange={(e) => {
              const proj = projects.find((p) => p.id === parseInt(e.target.value));
              setSelectedProject(proj || null);
            }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-lg font-bold text-white focus:outline-none focus:border-violet-500 max-w-[280px]"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
            {projects.length === 0 && <option value="">No Active Projects</option>}
          </select>

          {selectedProject && canManageProjects && (
            <button
              onClick={() => handleDeleteProject(selectedProject.id)}
              className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-red-950/20 hover:text-red-400 hover:border-red-900/30 transition-all text-slate-500"
              title="Delete Project"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          {canManageProjects && (
            <button
              onClick={() => setShowNewProj(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-sm font-semibold text-white transition-all"
            >
              <Plus className="w-4 h-4" />
              New Project
            </button>
          )}

          {selectedProject && (
            <button
              onClick={() => setShowNewTask(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 rounded-xl text-sm font-semibold text-white shadow-md shadow-violet-900/30 transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Task
            </button>
          )}
        </div>
      </div>

      {projects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
          <LayersPlaceholder />
          <h3 className="text-xl font-bold mt-4 text-slate-300">No Projects Found</h3>
          <p className="text-sm mt-1 text-slate-500">
            {canManageProjects
              ? 'Click "New Project" to create your first SaaS workspace.'
              : 'Contact your Manager/Admin to assign you to a project.'}
          </p>
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 overflow-hidden pr-2">
          <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5 flex flex-col h-full overflow-hidden">
            <h4 className="text-sm font-bold text-slate-400 mb-4 tracking-wider uppercase flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
              Todo ({tasksByStatus('todo').length})
            </h4>
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {tasksByStatus('todo').map((task) => (
                <TaskCard key={task.id} task={task} onClick={() => handleTaskClick(task)} />
              ))}
            </div>
          </div>

          <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5 flex flex-col h-full overflow-hidden">
            <h4 className="text-sm font-bold text-slate-400 mb-4 tracking-wider uppercase flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-violet-500" />
              In Progress ({tasksByStatus('in_progress').length})
            </h4>
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {tasksByStatus('in_progress').map((task) => (
                <TaskCard key={task.id} task={task} onClick={() => handleTaskClick(task)} />
              ))}
            </div>
          </div>

          <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5 flex flex-col h-full overflow-hidden">
            <h4 className="text-sm font-bold text-slate-400 mb-4 tracking-wider uppercase flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
              Done ({tasksByStatus('done').length})
            </h4>
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {tasksByStatus('done').map((task) => (
                <TaskCard key={task.id} task={task} onClick={() => handleTaskClick(task)} />
              ))}
            </div>
          </div>
        </div>
      )}

      {showNewProj && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-6">Create New Project</h3>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProjName}
                  onChange={(e) => setNewProjName(e.target.value)}
                  placeholder="e.g. Website Redesign"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Description</label>
                <textarea
                  value={newProjDesc}
                  onChange={(e) => setNewProjDesc(e.target.value)}
                  placeholder="Optional details..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors h-24 resize-none"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewProj(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-semibold transition-colors"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showNewTask && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-6">Create New Task</h3>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Task Title</label>
                <input
                  type="text"
                  required
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  placeholder="e.g. Implement JWT Auth"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Description</label>
                <textarea
                  value={newTaskDesc}
                  onChange={(e) => setNewTaskDesc(e.target.value)}
                  placeholder="Optional details..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors h-24 resize-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Priority</label>
                <select
                  value={newTaskPriority}
                  onChange={(e) => setNewTaskPriority(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewTask(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-semibold transition-colors"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedTask && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex justify-end z-50">
          <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center shrink-0">
              <div className="overflow-hidden">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider border ${
                  selectedTask.priority === 'high' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                  selectedTask.priority === 'medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                  'bg-blue-500/10 text-blue-400 border-blue-500/20'
                }`}>
                  {selectedTask.priority} priority
                </span>
                <h3 className="text-xl font-bold text-white mt-3 truncate">{selectedTask.title}</h3>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-slate-400 hover:text-white font-bold"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div>
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Description</h4>
                <p className="text-sm text-slate-300 bg-slate-950 border border-slate-800 rounded-xl p-4 min-h-16 whitespace-pre-wrap">
                  {selectedTask.description || 'No description provided.'}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Task Status</h4>
                <div className="flex gap-2">
                  {['todo', 'in_progress', 'done'].map((st) => (
                    <button
                      key={st}
                      onClick={() => handleUpdateTaskStatus(selectedTask, st)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase border transition-all ${
                        selectedTask.status === st
                          ? 'bg-violet-600 border-violet-500 text-white shadow-md'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {st.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-800 pt-6">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-violet-400" />
                  Comments ({comments.length})
                </h4>

                <form onSubmit={handleAddComment} className="flex gap-2 mb-6">
                  <input
                    type="text"
                    required
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Ask a question or post an update..."
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors"
                  />
                  <button
                    type="submit"
                    className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-semibold transition-colors shrink-0"
                  >
                    Post
                  </button>
                </form>

                <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                  {comments.map((c) => (
                    <div key={c.id} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-sm">
                      <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                        <span className="font-semibold text-violet-400">Author ID {c.author_id}</span>
                        <span>{new Date(c.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="text-slate-300">{c.content}</div>
                    </div>
                  ))}
                  {comments.length === 0 && (
                    <div className="text-center py-6 text-slate-500 text-sm">No comments yet.</div>
                  )}
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex justify-between items-center shrink-0">
              <button
                onClick={() => handleDeleteTask(selectedTask)}
                className="flex items-center gap-2 px-3 py-2 bg-red-950/20 hover:bg-red-900/20 text-red-400 rounded-lg text-sm font-medium border border-red-900/30 transition-all"
              >
                <Trash2 className="w-4 h-4" />
                Delete Task
              </button>
              <button
                onClick={() => setSelectedTask(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TaskCard({ task, onClick }: { task: any; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      className="bg-slate-900 hover:bg-slate-800/80 border border-slate-800/60 hover:border-violet-500/30 rounded-xl p-4 shadow-md transition-all cursor-pointer group flex flex-col gap-3.5"
    >
      <div className="flex justify-between items-start gap-3">
        <h5 className="font-semibold text-white group-hover:text-violet-400 transition-colors line-clamp-2 text-sm leading-snug">
          {task.title}
        </h5>
        {task.status === 'done' ? (
          <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
        ) : (
          <Circle className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
        )}
      </div>

      {task.description && (
        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed break-all">
          {task.description}
        </p>
      )}

      <div className="flex justify-between items-center pt-2 border-t border-slate-800/60">
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border tracking-wide ${
          task.priority === 'high' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
          task.priority === 'medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
          'bg-blue-500/10 text-blue-400 border-blue-500/20'
        }`}>
          {task.priority}
        </span>
        <div className="text-[10px] text-slate-500 flex items-center gap-1">
          <MessageSquare className="w-3 h-3 text-slate-600" />
          {task.comments?.length || 0}
        </div>
      </div>
    </div>
  );
}

function LayersPlaceholder() {
  return (
    <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 opacity-60">
      <AlertCircle className="w-8 h-8" />
    </div>
  );
}
