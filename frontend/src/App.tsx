import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LayoutDashboard, Briefcase, Activity, BarChart2, Settings, FileJson, PlaySquare, PanelLeftClose, PanelLeftOpen, Search, Play, ListTodo } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePreferences } from '@/store/preferences';
import { CommandMenu } from '@/components/CommandMenu';
import { GlobalErrorBoundary } from '@/components/ErrorBoundary';

// Pages placeholders
import Dashboard from '@/pages/Dashboard';
import Jobs from '@/pages/Jobs';
import Runs from '@/pages/Runs';
import Runtime from '@/pages/Runtime';
import Artifacts from '@/pages/Artifacts';
import Analytics from '@/pages/Analytics';
import AppSettings from '@/pages/Settings';
import Pipeline from '@/pages/Pipeline';
import Queues from '@/pages/Queues';

const queryClient = new QueryClient();

function Sidebar() {
  const location = useLocation();
  const { sidebarOpen, toggleSidebar } = usePreferences();
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Jobs', path: '/jobs', icon: Briefcase },
    { name: 'Runs', path: '/runs', icon: PlaySquare },
    { name: 'Runtime', path: '/runtime', icon: Activity },
    { name: 'Artifacts', path: '/artifacts', icon: FileJson },
    { name: 'Analytics', path: '/analytics', icon: BarChart2 },
    { name: 'Pipeline', path: '/pipeline', icon: Play },
    { name: 'Queues', path: '/queues', icon: ListTodo },
  ];

  return (
    <div className={cn(
      "border-r bg-card h-screen flex flex-col transition-all duration-200 ease-in-out shrink-0",
      sidebarOpen ? "w-56" : "w-[60px]"
    )}>
      <div className="h-12 border-b flex items-center justify-between px-3">
        {sidebarOpen && (
          <h1 className="font-semibold text-sm flex items-center gap-2 overflow-hidden whitespace-nowrap">
            <div className="w-5 h-5 bg-foreground rounded flex items-center justify-center shrink-0">
              <span className="text-background text-[10px] font-bold">CW</span>
            </div>
            Operations
          </h1>
        )}
        {!sidebarOpen && (
          <div className="w-5 h-5 bg-foreground rounded flex items-center justify-center shrink-0 mx-auto">
            <span className="text-background text-[10px] font-bold">CW</span>
          </div>
        )}
      </div>
      <div className="p-2 flex-1 flex flex-col gap-1 overflow-hidden">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            title={!sidebarOpen ? item.name : undefined}
            className={cn(
              "flex items-center gap-3 px-3 py-1.5 rounded text-sm transition-colors whitespace-nowrap",
              location.pathname === item.path
                ? "bg-secondary text-foreground font-medium"
                : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
            )}
          >
            <item.icon className="w-4 h-4 shrink-0" />
            {sidebarOpen && <span>{item.name}</span>}
          </Link>
        ))}
      </div>
      <div className="p-2 border-t flex flex-col gap-1">
        <Link
          to="/settings"
          title={!sidebarOpen ? "Settings" : undefined}
          className={cn(
            "flex items-center gap-3 px-3 py-1.5 rounded text-sm transition-colors whitespace-nowrap",
            location.pathname === "/settings"
              ? "bg-secondary text-foreground font-medium"
              : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
          )}
        >
          <Settings className="w-4 h-4 shrink-0" />
          {sidebarOpen && <span>Settings</span>}
        </Link>
        <button
          onClick={toggleSidebar}
          className="flex items-center gap-3 px-3 py-1.5 rounded text-sm text-muted-foreground hover:bg-secondary/50 hover:text-foreground transition-colors"
        >
          {sidebarOpen ? <PanelLeftClose className="w-4 h-4 shrink-0" /> : <PanelLeftOpen className="w-4 h-4 shrink-0" />}
          {sidebarOpen && <span>Collapse Sidebar</span>}
        </button>
      </div>
    </div>
  );
}

function Topbar() {
  return (
    <header className="h-12 border-b bg-background flex items-center px-4 justify-between shrink-0">
      <div className="flex-1" />
      <div className="flex items-center gap-4">
        <button className="flex items-center gap-2 text-xs text-muted-foreground bg-secondary/50 hover:bg-secondary border px-2 py-1 rounded-md transition-colors" onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}>
          <Search className="w-3 h-3" />
          <span>Search...</span>
          <kbd className="font-mono text-[10px] bg-background px-1 rounded border">⌘K</kbd>
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
                <Route path="/" element={<Dashboard />} />
                <Route path="/jobs" element={<Jobs />} />
                <Route path="/runs" element={<Runs />} />
                <Route path="/runtime" element={<Runtime />} />
                <Route path="/artifacts" element={<Artifacts />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<AppSettings />} />
                <Route path="/pipeline" element={<Pipeline />} />
                <Route path="/queues" element={<Queues />} />
              </Routes>
            </Layout>
          </Router>
        </ThemeProvider>
      </QueryClientProvider>
    </GlobalErrorBoundary>
  );
}

export default App;
