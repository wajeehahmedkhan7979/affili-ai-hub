import { useState, useEffect } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { api } from '@/lib/api';
import { ResponsePoolItem } from '@/lib/mock-data';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, Plus, Edit, Trash2 } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { formatDistanceToNow } from 'date-fns';
import { AddResponseModal } from '@/components/response-pool/AddResponseModal';
import { useToast } from '@/hooks/use-toast';

export default function ResponsePool() {
  const { toast } = useToast();
  const [responses, setResponses] = useState<ResponsePoolItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadResponses();
  }, [search]);

  async function loadResponses() {
    setLoading(true);
    try {
      const data = await api.getResponsePool(search || undefined);
      setResponses(data);
    } catch (error) {
      console.error('Failed to load responses:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppLayout title="Response Pool">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-muted-foreground">
              Manage your AI-powered Q&A responses for applications
            </p>
          </div>
          <Button className="gap-2" onClick={() => setShowAddModal(true)}>
            <Plus className="h-4 w-4" />
            Add Response
          </Button>
        </div>

        {/* Search */}
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search responses..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Table */}
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-[30%]">Question</TableHead>
                <TableHead className="w-[35%]">Answer</TableHead>
                <TableHead>Context</TableHead>
                <TableHead>Approval Rate</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={6}>
                      <Skeleton className="h-16 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              ) : responses.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    No responses found. Add your first Q&A response to get started.
                  </TableCell>
                </TableRow>
              ) : (
                responses.map((response) => (
                  <TableRow key={response.id} className="group">
                    <TableCell>
                      <p className="font-medium text-card-foreground line-clamp-2">
                        {response.question_text}
                      </p>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {response.answer_text}
                      </p>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {response.context.map((ctx) => (
                          <Badge key={ctx} variant="outline" className="text-xs">
                            {ctx}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Progress value={response.approval_rate * 100} className="w-16 h-2" />
                          <span className="text-sm font-medium text-green-600">
                            {Math.round(response.approval_rate * 100)}%
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(response.last_used_date), { addSuffix: true })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button size="icon" variant="ghost">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="icon" variant="ghost" className="text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        <AddResponseModal
          open={showAddModal}
          onOpenChange={setShowAddModal}
          onSuccess={loadResponses}
        />
      </div>
    </AppLayout>
  );
}
