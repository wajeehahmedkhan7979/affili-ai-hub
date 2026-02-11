import { useState, useEffect } from 'react';
import { Program } from '@/lib/mock-data';
import { api } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Checkbox } from '@/components/ui/checkbox';

interface BulkApplyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function BulkApplyModal({ open, onOpenChange, onSuccess }: BulkApplyModalProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [selectedPrograms, setSelectedPrograms] = useState<Set<string>>(new Set());
  const [strategy, setStrategy] = useState('');

  useEffect(() => {
    if (open) {
      loadDiscoveredPrograms();
    } else {
      // Reset on close
      setSelectedPrograms(new Set());
      setStrategy('');
    }
  }, [open]);

  async function loadDiscoveredPrograms() {
    setLoading(true);
    try {
      const allPrograms = await api.getPrograms({ status: 'Discovered' });
      setPrograms(allPrograms.filter(p => p.status === 'Discovered'));
      // Select all by default
      setSelectedPrograms(new Set(allPrograms.filter(p => p.status === 'Discovered').map(p => p.id)));
    } catch (error) {
      console.error('Failed to load programs:', error);
      toast({
        title: "Error",
        description: "Failed to load programs. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }

  const toggleProgram = (programId: string) => {
    const newSelected = new Set(selectedPrograms);
    if (newSelected.has(programId)) {
      newSelected.delete(programId);
    } else {
      newSelected.add(programId);
    }
    setSelectedPrograms(newSelected);
  };

  const toggleAll = () => {
    if (selectedPrograms.size === programs.length) {
      setSelectedPrograms(new Set());
    } else {
      setSelectedPrograms(new Set(programs.map(p => p.id)));
    }
  };

  async function handleSubmit() {
    if (selectedPrograms.size === 0) {
      toast({
        title: "No Programs Selected",
        description: "Please select at least one program to apply to.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      // Create a bulk application task
      await api.createTask({
        task_type: 'BULK_APPLY',
        payload: {
          program_ids: Array.from(selectedPrograms),
          strategy: strategy || 'default',
          count: selectedPrograms.size
        }
      });

      toast({
        title: "Bulk Application Started",
        description: `Created application task for ${selectedPrograms.size} programs. Check the Tasks page for progress.`,
      });

      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Failed to start bulk application:', error);
      toast({
        title: "Failed to Start",
        description: "Failed to start bulk application. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Bulk Apply to Programs</DialogTitle>
          <DialogDescription>
            The agent will automatically apply to all "Discovered" programs that match your criteria.
            {programs.length > 0 && ` Reviewing ${programs.length} programs.`}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="py-12 flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Loading discovered programs...</p>
          </div>
        ) : programs.length === 0 ? (
          <div className="py-12 text-center">
            <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Programs Found</h3>
            <p className="text-muted-foreground">
              No discovered programs available for bulk application.
              Try discovering new programs first.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {/* Application Strategy */}
              <div className="space-y-2">
                <Label htmlFor="strategy">Application Strategy (Optional)</Label>
                <Textarea
                  id="strategy"
                  placeholder="e.g., high commission saas products first"
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  rows={2}
                  className="resize-none"
                />
                <p className="text-xs text-muted-foreground">
                  Provide guidance on how the AI should prioritize applications.
                </p>
              </div>

              {/* Program Selection */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Select Programs ({selectedPrograms.size} selected)</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleAll}
                  >
                    {selectedPrograms.size === programs.length ? 'Deselect All' : 'Select All'}
                  </Button>
                </div>
                <div className="rounded-lg border border-border max-h-64 overflow-y-auto">
                  {programs.map((program) => (
                    <div
                      key={program.id}
                      className="flex items-center gap-3 p-3 border-b border-border last:border-b-0 hover:bg-muted/50 cursor-pointer"
                      onClick={() => toggleProgram(program.id)}
                    >
                      <Checkbox
                        checked={selectedPrograms.has(program.id)}
                        onCheckedChange={() => toggleProgram(program.id)}
                      />
                      <div className="flex-1">
                        <p className="font-medium text-sm">{program.name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">{program.network}</Badge>
                          {program.commission && (
                            <span className="text-xs text-green-600 font-medium">
                              {program.commission}
                            </span>
                          )}
                        </div>
                      </div>
                      {program.confidence_score && (
                        <div className="text-xs text-muted-foreground">
                          {(program.confidence_score * 100).toFixed(0)}% confidence
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={submitting || selectedPrograms.size === 0}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Start Bulk Application
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
