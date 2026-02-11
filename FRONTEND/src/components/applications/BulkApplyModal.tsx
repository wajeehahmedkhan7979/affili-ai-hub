import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface BulkApplyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function BulkApplyModal({ open, onOpenChange, onSuccess }: BulkApplyModalProps) {
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState('');
  const [error, setError] = useState('');

  const handleApply = async () => {
    setLoading(true);
    setError('');

    try {
      await api.createTask({
        task_type: 'APPLY_PROGRAM', 
        payload: { strategy_notes: strategy, mode: 'bulk' }
      });
      
      setStrategy('');
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (err) {
      console.error('Failed to create application task:', err);
      setError('Failed to start bulk application. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Bulk Apply to Programs</DialogTitle>
          <DialogDescription>
            The agent will automatically apply to all "Discovered" programs that match your criteria.
            Reviewing 5 programs.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="strategy">Application Strategy (Optional)</Label>
            <Textarea
              id="strategy"
              placeholder="e.g. Focus on high commission SaaS products first..."
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="min-h-[100px]"
            />
          </div>
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleApply} disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Start Bulk Apply
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
