import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LayoutDashboard, Briefcase, Activity, BarChart2, Settings, FileJson, PlaySquare } from 'lucide-react';
import { cn } from '@/lib/utils';

// Pages placeholders
import Dashboard from '@/pages/Dashboard';
import Jobs from '@/pages/Jobs';
import Runs from '@/pages/Runs';
import Runtime from '@/pages/Runtime';
import Artifacts from '@/pages/Artifacts';
import Analytics from '@/pages/Analytics';
import AppSettings from '@/pages/Settings';

const queryClient = new QueryClient();

function Sidebar() {
  const location = useLocation();
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Jobs', path: '/jobs', icon: Briefcase },
    { name: 'Runs', path: '/runs', icon: PlaySquare },
    { name: 'Runtime', path: '/runtime', icon: Activity },
    { name: 'Artifacts', path: '/artifacts', icon: FileJson },
    { name: 'Analytics', path: '/analytics', icon: BarChart2 },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="w-64 border-r bg-card h-screen flex flex-col">
      <div className="p-4 border-b h-14 flex items-center">
        <h1 className="font-semibold text-lg flex items-center gap-2">
          <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
            <span className="text-primary-foreground text-xs font-bold">CW</span>
          </div>
          Career Workflow
        </h1>
      </div>
      <div className="p-4 flex-1 flex flex-col gap-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
              location.pathname === item.path
                ? "bg-primary text-primary-foreground font-medium"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.name}
          </Link>
        ))}
      </div>
    </div>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/runs" element={<Runs />} />
            <Route path="/runtime" element={<Runtime />} />
            <Route path="/artifacts" element={<Artifacts />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<AppSettings />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
