import { useQuery } from '@tanstack/react-query';
import { fetchArtifacts } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function Artifacts() {
  const { data: artifacts = [], isLoading } = useQuery({
    queryKey: ['artifacts'],
    queryFn: fetchArtifacts,
  });

  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const selectedArtifact = artifacts.find((a: any) => a.run_id === selectedRunId);

  return (
    <div className="p-8 h-full flex flex-col space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Artifact Explorer</h2>
        <p className="text-muted-foreground">Inspect JSON payloads for completed runs.</p>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 overflow-hidden">
        <Card className="col-span-1 flex flex-col overflow-hidden">
          <CardHeader>
            <CardTitle>Runs</CardTitle>
          </CardHeader>
          <ScrollArea className="flex-1 p-4 pt-0">
            {isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => <Skeleton key={i} className="h-10 w-full" />)}
              </div>
            ) : (
              <div className="space-y-2">
                {artifacts.map((a: any) => (
                  <Button
                    key={a.run_id}
                    variant={selectedRunId === a.run_id ? 'default' : 'outline'}
                    className="w-full justify-start font-mono text-sm"
                    onClick={() => setSelectedRunId(a.run_id)}
                  >
                    {a.run_id}
                  </Button>
                ))}
              </div>
            )}
          </ScrollArea>
        </Card>

        <Card className="col-span-2 flex flex-col overflow-hidden">
          <CardHeader>
            <CardTitle>JSON Viewer</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto p-0">
            {selectedArtifact ? (
              <Tabs defaultValue="result" className="w-full h-full flex flex-col">
                <div className="px-4 border-b">
                  <TabsList>
                    <TabsTrigger value="result">result.json</TabsTrigger>
                    <TabsTrigger value="state">run.json (State)</TabsTrigger>
                  </TabsList>
                </div>
                <ScrollArea className="flex-1">
                  <TabsContent value="result" className="p-4 m-0">
                    <pre className="text-xs bg-muted p-4 rounded-md overflow-x-auto">
                      {JSON.stringify(selectedArtifact.result, null, 2)}
                    </pre>
                  </TabsContent>
                  <TabsContent value="state" className="p-4 m-0">
                    <pre className="text-xs bg-muted p-4 rounded-md overflow-x-auto">
                      {JSON.stringify(selectedArtifact.state, null, 2)}
                    </pre>
                  </TabsContent>
                </ScrollArea>
              </Tabs>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Select a run to view artifacts.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
