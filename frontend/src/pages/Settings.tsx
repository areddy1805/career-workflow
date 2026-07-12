import { useQuery } from '@tanstack/react-query';
import { fetchSettings } from '@/lib/api';
import { Settings2, SlidersHorizontal, Monitor, Moon, Sun } from 'lucide-react';
import { usePreferences } from '@/store/preferences';

export default function Settings() {
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  });

  const { theme, setTheme } = usePreferences();

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      <div className="flex items-center px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold text-lg tracking-tight flex items-center gap-2">
          <Settings2 className="w-5 h-5 text-primary" />
          Settings
        </h2>
      </div>

      <div className="flex-1 overflow-auto p-6 max-w-4xl space-y-8">
        
        {/* Frontend Preferences */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 border-b pb-2">
            <SlidersHorizontal className="w-4 h-4 text-muted-foreground" />
            <h3 className="font-semibold text-sm">Interface Preferences</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="border border-border/50 rounded-md p-4 bg-card/30 flex items-center justify-between">
              <div>
                <p className="font-medium">Theme</p>
                <p className="text-xs text-muted-foreground">Select your interface color scheme.</p>
              </div>
              <div className="flex bg-muted rounded-md p-1 border">
                <button 
                  onClick={() => setTheme('light')}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-sm text-xs transition-colors ${theme === 'light' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                >
                  <Sun className="w-3.5 h-3.5" /> Light
                </button>
                <button 
                  onClick={() => setTheme('dark')}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-sm text-xs transition-colors ${theme === 'dark' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                >
                  <Moon className="w-3.5 h-3.5" /> Dark
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Backend Environment */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 border-b pb-2 mt-8">
            <Monitor className="w-4 h-4 text-muted-foreground" />
            <h3 className="font-semibold text-sm">Environment Configuration</h3>
            <span className="ml-2 text-[10px] uppercase font-mono bg-secondary px-1.5 py-0.5 rounded text-muted-foreground tracking-wider">Read-Only</span>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map(i => <div key={i} className="h-14 bg-muted animate-pulse rounded" />)}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(settings || {}).map(([key, value]) => (
                <div key={key} className="border border-border/50 rounded-md p-3 bg-card/30 flex flex-col justify-center">
                  <p className="text-[10px] font-mono text-muted-foreground truncate mb-1" title={key}>{key}</p>
                  <p className="font-mono text-xs font-medium truncate" title={String(value)}>{value != null && value !== '' ? String(value) : 'Not Set'}</p>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
