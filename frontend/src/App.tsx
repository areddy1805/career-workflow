import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  LayoutDashboard, Briefcase, Activity, BarChart2, Settings,
  FileJson, PlaySquare, PanelLeftClose, PanelLeftOpen,
  Search, Play, ListTodo, Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePreferences } from '@/store/preferences';
import { CommandMenu } from '@/components/CommandMenu';
import { GlobalErrorBoundary } from '@/components/ErrorBoundary';

import Dashboard from '@/pages/Dashboard';
import Jobs from '@/pages/Jobs';
import Runs from '@/pages/Runs';
import Runtime from '@/pages/Runtime';
import Artifacts from '@/pages/Artifacts';
import Analytics from '@/pages/Analytics';
import AppSettings from '@/pages/Settings';
import Pipeline from '@/pages/Pipeline';
import Queues from '@/pages/Queues';
import SearchPage from '@/pages/Search';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
});

const NAV_ITEMS = [
  { name: 'Dashboard',  path: '/',          icon: LayoutDashboard, group: 'main' },
  { name: 'Search',     path: '/search',    icon: Search,           group: 'main' },
  { name: 'Queues',     path: '/queues',    icon: ListTodo,         group: 'main', badge: true },
  { name: 'Jobs',       path: '/jobs',      icon: Briefcase,        group: 'main' },
  { name: 'Pipeline',   path: '/pipeline',  icon: Play,             group: 'ops' },
  { name: 'Runs',       path: '/runs',      icon: PlaySquare,       group: 'ops' },
  { name: 'Runtime',    path: '/runtime',   icon: Activity,         group: 'ops' },
  { name: 'Artifacts',  path: '/artifacts', icon: FileJson,         group: 'ops' },
  { name: 'Analytics',  path: '/analytics', icon: BarChart2,        group: 'ops' },
];

function Sidebar() {
  const { sidebarOpen, toggleSidebar } = usePreferences();
  const mainItems = NAV_ITEMS.filter(i => i.group === 'main');
  const opsItems  = NAV_ITEMS.filter(i => i.group === 'ops');

  return (
    <div className={cn(
      'border-r border-border/60 bg-card h-screen flex flex-col transition-all duration-200 ease-in-out shrink-0 relative z-40',
      sidebarOpen ? 'w-[220px]' : 'w-[58px]'
    )}>
      {/* Logo */}
      <div className="h-14 border-b border-border/60 flex items-center px-3 shrink-0">
        {sidebarOpen ? (
          <div className="flex items-center gap-2.5 overflow-hidden whitespace-nowrap">
            <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center shrink-0 glow-amber">
              <Zap className="w-4 h-4 text-primary-foreground" />
            </div>
            <div>
              <p className="text-sm font-bold tracking-tight leading-none text-gradient-amber">CareerFlow</p>
              <p className="text-[9px] text-muted-foreground font-mono tracking-widest mt-0.5">OPERATIONS</p>
            </div>
          </div>
        ) : (
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center shrink-0 mx-auto glow-amber">
            <Zap className="w-4 h-4 text-primary-foreground" />
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 flex flex-col gap-0.5 overflow-y-auto overflow-x-hidden">
        {sidebarOpen && (
          <p className="text-[9px] font-semibold text-muted-foreground/60 uppercase tracking-widest px-2 mb-1">Workspace</p>
        )}
        {mainItems.map(item => <NavItem key={item.path} item={item} collapsed={!sidebarOpen} />)}

        <div className="my-2 border-t border-border/40" />

        {sidebarOpen && (
          <p className="text-[9px] font-semibold text-muted-foreground/60 uppercase tracking-widest px-2 mb-1">Operations</p>
        )}
        {opsItems.map(item => <NavItem key={item.path} item={item} collapsed={!sidebarOpen} />)}
      </nav>

      {/* Footer */}
      <div className="px-2 py-2 border-t border-border/60 flex flex-col gap-0.5">
        <NavLink
          to="/settings"
          title={!sidebarOpen ? 'Settings' : undefined}
          className={({ isActive }) => cn(
            'flex items-center gap-3 px-2.5 py-2 rounded-md text-xs font-medium transition-all duration-150 whitespace-nowrap group',
            isActive
              ? 'bg-primary/15 text-primary'
              : 'text-muted-foreground hover:bg-secondary/80 hover:text-foreground'
          )}
        >
          <Settings className="w-4 h-4 shrink-0" />
          {sidebarOpen && <span>Settings</span>}
        </NavLink>
        <button
          onClick={toggleSidebar}
          className="flex items-center gap-3 px-2.5 py-2 rounded-md text-xs text-muted-foreground hover:bg-secondary/80 hover:text-foreground transition-all duration-150 whitespace-nowrap"
        >
          {sidebarOpen
            ? <PanelLeftClose className="w-4 h-4 shrink-0" />
            : <PanelLeftOpen className="w-4 h-4 shrink-0" />}
          {sidebarOpen && <span className="text-xs">Collapse</span>}
        </button>
      </div>
    </div>
  );
}

function NavItem({ item, collapsed }: { item: typeof NAV_ITEMS[0]; collapsed: boolean }) {
  return (
    <NavLink
      to={item.path}
      end={item.path === '/'}
      title={collapsed ? item.name : undefined}
      className={({ isActive }) => cn(
        'flex items-center gap-3 px-2.5 py-2 rounded-md text-xs font-medium transition-all duration-150 whitespace-nowrap group relative',
        isActive
          ? 'bg-primary/15 text-primary shadow-sm'
          : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground'
      )}
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-primary rounded-r-full" />
          )}
          <item.icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-primary' : 'group-hover:text-foreground')} />
          {!collapsed && <span>{item.name}</span>}
        </>
      )}
    </NavLink>
  );
}

function Topbar() {
  const location = useLocation();
  const pageLabel = [...NAV_ITEMS, { path: '/settings', name: 'Settings', icon: Settings, group: '' }]
    .find(i => i.path === location.pathname || (i.path === '/' && location.pathname === '/'))?.name ?? '';

  return (
    <header className="h-12 border-b border-border/60 bg-background/80 backdrop-blur-sm flex items-center px-5 justify-between shrink-0 z-30 sticky top-0">
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground/60">/</span>
        <span className="text-xs font-semibold text-foreground">{pageLabel}</span>
      </div>
      <div className="flex items-center gap-3">
        {/* Live indicator */}
        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-green" />
          <span className="font-mono">LIVE</span>
        </div>
        <button
          className="flex items-center gap-2 text-xs text-muted-foreground bg-secondary/40 hover:bg-secondary border border-border/60 px-3 py-1.5 rounded-lg transition-all duration-150 hover:border-border"
          onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
        >
          <Search className="w-3 h-3" />
          <span>Search…</span>
          <kbd className="font-mono text-[9px] bg-background px-1.5 py-0.5 rounded border border-border/60 ml-1">⌘K</kbd>
        </button>
      </div>
    </header>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <Topbar />
        <main className="flex-1 overflow-auto relative">
          {children}
        </main>
      </div>
    </div>
  );
}

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme } = usePreferences();
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);
  return <>{children}</>;
}

function App() {
  return (
    <GlobalErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <Router>
            <CommandMenu />
            <Layout>
              <Routes>
                <Route path="/"          element={<Dashboard />} />
                <Route path="/jobs"      element={<Jobs />} />
                <Route path="/runs"      element={<Runs />} />
                <Route path="/runtime"   element={<Runtime />} />
                <Route path="/artifacts" element={<Artifacts />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/queues"    element={<Queues />} />
                <Route path="/search"    element={<SearchPage />} />
                <Route path="/settings"  element={<AppSettings />} />
                <Route path="/pipeline"  element={<Pipeline />} />
              </Routes>
            </Layout>
          </Router>
        </ThemeProvider>
      </QueryClientProvider>
    </GlobalErrorBoundary>
  );
}

export default App;
