import { useQuery } from '@tanstack/react-query';
import { fetchRuns } from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

export default function Runs() {
  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
  });

  return (
    <div className="p-8 h-full flex flex-col space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Runs Explorer</h2>
      </div>

      <div className="rounded-md border flex-1 overflow-auto bg-card">
        <Table>
          <TableHeader className="sticky top-0 bg-secondary/80 backdrop-blur">
            <TableRow>
              <TableHead>Run ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Acquired</TableHead>
              <TableHead>Classified</TableHead>
              <TableHead>Submitted</TableHead>
              <TableHead>Failed</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={7}><Skeleton className="h-6 w-full" /></TableCell>
                </TableRow>
              ))
            ) : runs.length ? (
              runs.map((run: any) => (
                <TableRow key={run.run_id} className="cursor-pointer hover:bg-muted/50">
                  <TableCell className="font-medium">{run.run_id}</TableCell>
                  <TableCell>
                    <Badge variant={run.status === 'SUCCESS' ? 'default' : run.status === 'FAILED' ? 'destructive' : 'secondary'}>
                      {run.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{new Date(run.started_at).toLocaleString()}</TableCell>
                  <TableCell>{run.acquired}</TableCell>
                  <TableCell>{run.classified}</TableCell>
                  <TableCell>{run.submitted}</TableCell>
                  <TableCell className="text-destructive font-medium">{run.failed}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center">No runs found.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
