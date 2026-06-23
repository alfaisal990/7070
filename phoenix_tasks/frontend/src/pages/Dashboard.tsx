import { useEffect, useState } from 'react';
import { api } from '../api';
import { LayoutDashboard, ClipboardList, CheckCircle2, AlertTriangle, Layers, Clock } from 'lucide-react';

export function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const s = await api.dashboard.getStats();
        setStats(s);
        
        try {
          const a = await api.activities.list();
          setActivities(a.slice(0, 10));
        } catch (e) {
          setActivities([]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950 text-slate-400">
        Loading dashboard metrics...
      </div>
    );
  }

  return (
    <div className="flex-1 bg-slate-950 p-8 overflow-y-auto text-slate-100">
      <header className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <LayoutDashboard className="w-8 h-8 text-violet-500" />
          Dashboard Overview
        </h2>
        <p className="text-slate-400 mt-2">Real-time metrics, status distribution, and activity logging.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center justify-between shadow-lg">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Projects</div>
            <div className="text-3xl font-bold mt-2 text-white">{stats?.total_projects || 0}</div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 border border-blue-500/20">
            <Layers className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center justify-between shadow-lg">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Tasks</div>
            <div className="text-3xl font-bold mt-2 text-white">{stats?.total_tasks || 0}</div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-violet-500/10 flex items-center justify-center text-violet-400 border border-violet-500/20">
            <ClipboardList className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center justify-between shadow-lg">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Done Tasks</div>
            <div className="text-3xl font-bold mt-2 text-white">{stats?.done_tasks || 0}</div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center text-green-400 border border-green-500/20">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center justify-between shadow-lg">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">High Priority</div>
            <div className="text-3xl font-bold mt-2 text-white">{stats?.high_priority_tasks || 0}</div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-red-500/10 flex items-center justify-center text-red-400 border border-red-500/20">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-white mb-6">Task Status Distribution</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Todo</span>
                <span className="font-semibold text-white">{stats?.todo_tasks || 0}</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{
                    width: `${
                      stats?.total_tasks ? ((stats.todo_tasks || 0) / stats.total_tasks) * 100 : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>In Progress</span>
                <span className="font-semibold text-white">{stats?.in_progress_tasks || 0}</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2">
                <div
                  className="bg-violet-500 h-2 rounded-full"
                  style={{
                    width: `${
                      stats?.total_tasks ? ((stats.in_progress_tasks || 0) / stats.total_tasks) * 100 : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Done</span>
                <span className="font-semibold text-white">{stats?.done_tasks || 0}</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{
                    width: `${
                      stats?.total_tasks ? ((stats.done_tasks || 0) / stats.total_tasks) * 100 : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-white mb-6">Recent Activities</h3>
          {activities.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-slate-500 text-sm">
              <Clock className="w-8 h-8 mb-2 opacity-50" />
              {stats?.total_projects === 0 ? 'No activity logs found yet.' : 'Only Managers/Admins can view audit logs.'}
            </div>
          ) : (
            <div className="space-y-4 max-h-[220px] overflow-y-auto pr-2">
              {activities.map((act) => (
                <div key={act.id} className="flex gap-4 p-3 bg-slate-950 border border-slate-800 rounded-lg text-sm">
                  <div className="text-violet-400 font-semibold shrink-0 uppercase text-xs tracking-wider self-start bg-violet-600/10 px-2 py-0.5 rounded border border-violet-500/20">
                    {act.action}
                  </div>
                  <div className="text-slate-300 break-all">{act.details}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
