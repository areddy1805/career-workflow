import { useQuery } from '@tanstack/react-query';
import { fetchSettings } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';

export default function Settings() {
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  });

  return (
    <div className="p-8 space-y-8 h-full flex flex-col">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Read-only view of current environment configuration.</p>
      </div>

      <Card className="flex-1 overflow-hidden flex flex-col">
        <CardHeader>
          <CardTitle>Safe Configuration Variables</CardTitle>
        </CardHeader>
        <CardContent className="overflow-auto flex-1 p-6">
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(settings || {}).map(([key, value]) => (
                <div key={key} className="space-y-1">
                  <Label htmlFor={key} className="text-xs font-semibold text-muted-foreground tracking-wider">
                    {key}
                  </Label>
                  <Input
                    id={key}
                    value={value as string || 'Not Set'}
                    readOnly
                    className="bg-muted/50 font-mono text-sm"
                  />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
