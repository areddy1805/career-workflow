import { useQuery } from '@tanstack/react-query';
import { fetchArtifacts } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { usePreferences } from '@/store/preferences';
import JsonView from 'react18-json-view';
import 'react18-json-view/src/style.css';
import { Database, FileJson } from 'lucide-react';
import { CopyButton } from '@/components/CopyButton';

export default function Artifacts() {
  const { data: artifacts = [], isLoading } = useQuery({
    queryKey: ['artifacts'],
    queryFn: fetchArtifacts,
  });

  const { theme } = usePreferences();
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const selectedArtifact = artifacts.find((a: any) => a.run_id === selectedRunId);

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="flex items-center px-4 py-2 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold tracking-tight">Artifact Explorer</h2>
      </div>

      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel defaultSize={25} minSize={20} maxSize={40} className="bg-card flex flex-col">
            <div className="h-10 border-b flex items-center px-4 bg-secondary/30 shrink-0">
              <Database className="w-3.5 h-3.5 text-muted-foreground mr-2" />
              <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider">Runs ({artifacts.length})</span>
            </div>
            <ScrollArea className="flex-1 custom-scrollbar">
              {isLoading ? (
                <div className="p-2 space-y-1">
                  {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-8 bg-muted animate-pulse rounded" />)}
                </div>
              ) : (
                <div className="flex flex-col">
                  {artifacts.map((a: any) => (
                    <button
                      key={a.run_id}
                      onClick={() => setSelectedRunId(a.run_id)}
                      className={`flex items-center px-4 py-2 text-xs font-mono border-b border-border/40 transition-colors text-left
                        ${selectedRunId === a.run_id ? 'bg-primary/10 text-primary border-l-2 border-l-primary' : 'hover:bg-muted/50 border-l-2 border-l-transparent'}`}
                    >
                      {a.run_id}
                    </button>
                  ))}
                  {!artifacts.length && <div className="p-4 text-xs text-muted-foreground text-center">No artifacts found.</div>}
                </div>
              )}
            </ScrollArea>
          </ResizablePanel>

          <ResizableHandle withHandle className="bg-border/50 hover:bg-primary/50 transition-colors w-1" />

          <ResizablePanel defaultSize={75} className="bg-card flex flex-col relative z-20">
            {selectedArtifact ? (
              <Tabs defaultValue="result" className="w-full h-full flex flex-col">
                <div className="px-2 border-b h-10 flex items-center justify-between bg-secondary/10 shrink-0">
                  <TabsList className="h-7 bg-transparent p-0 gap-1">
                    <TabsTrigger value="result" className="h-7 px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm rounded-sm border border-transparent data-[state=active]:border-border">
                      <FileJson className="w-3.5 h-3.5 mr-1.5" /> result.json
                    </TabsTrigger>
                    <TabsTrigger value="state" className="h-7 px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm rounded-sm border border-transparent data-[state=active]:border-border">
                      <FileJson className="w-3.5 h-3.5 mr-1.5" /> run.json (State)
                    </TabsTrigger>
                  </TabsList>
                  <div className="pr-2 flex items-center">
                     <span className="text-xs text-muted-foreground mr-2 font-mono">{selectedArtifact.run_id}</span>
                     <CopyButton value={JSON.stringify(selectedArtifact, null, 2)} className="h-7 w-7" />
                  </div>
                </div>
                <div className="flex-1 overflow-auto bg-background/50 relative">
                  <TabsContent value="result" className="absolute inset-0 m-0 outline-none">
                    <ScrollArea className="h-full w-full">
                      <div className="p-4">
                        <JsonView 
                          src={selectedArtifact.result} 
                          dark={theme === 'dark'}
                          theme="vscode"
                          enableClipboard={true}
                          collapsed={2}
                          style={{ backgroundColor: 'transparent', fontSize: '12px', fontFamily: 'var(--font-mono, monospace)' }}
                        />
                      </div>
                    </ScrollArea>
                  </TabsContent>
                  <TabsContent value="state" className="absolute inset-0 m-0 outline-none">
                    <ScrollArea className="h-full w-full">
                      <div className="p-4">
                        <JsonView 
                          src={selectedArtifact.state} 
                          dark={theme === 'dark'}
                          theme="vscode"
                          enableClipboard={true}
                          collapsed={2}
                          style={{ backgroundColor: 'transparent', fontSize: '12px', fontFamily: 'var(--font-mono, monospace)' }}
                        />
                      </div>
                    </ScrollArea>
                  </TabsContent>
                </div>
              </Tabs>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-4 bg-muted/10">
                <FileJson className="w-12 h-12 text-muted/30" />
                <p className="text-sm">Select a run from the sidebar to inspect its JSON payloads.</p>
              </div>
            )}
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  );
}
