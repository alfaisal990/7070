import { LayoutDashboard, FolderKanban, LogOut, Flame } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  user: any;
  onLogout: () => void;
}

export function Sidebar({ activeTab, setActiveTab, user, onLogout }: SidebarProps) {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between text-slate-300">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8">
          <Flame className="w-8 h-8 text-violet-500 animate-pulse" />
          <span className="text-xl font-bold text-white tracking-wide">Phoenix Tasks</span>
        </div>

        <nav className="flex flex-col gap-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'dashboard'
                ? 'bg-violet-600/20 text-violet-400 border border-violet-600/30'
                : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard className="w-5 h-5" />
            Dashboard
          </button>

          <button
            onClick={() => setActiveTab('projects')}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'projects'
                ? 'bg-violet-600/20 text-violet-400 border border-violet-600/30'
                : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <FolderKanban className="w-5 h-5" />
            Projects Board
          </button>
        </nav>
      </div>

      <div className="p-6 border-t border-slate-800">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-violet-600/20 flex items-center justify-center border border-violet-600/30 text-violet-400 font-bold uppercase">
            {user?.email?.[0] || 'U'}
          </div>
          <div className="overflow-hidden">
            <div className="text-sm font-medium text-white truncate">{user?.email}</div>
            <div className="text-xs text-slate-400 capitalize">{user?.role}</div>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-red-900/20 text-slate-400 hover:text-red-400 rounded-lg text-sm font-medium border border-slate-700 hover:border-red-900/30 transition-all"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
