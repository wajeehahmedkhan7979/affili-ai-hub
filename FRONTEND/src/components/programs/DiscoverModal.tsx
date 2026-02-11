import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface DiscoverModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function DiscoverModal({ open, onOpenChange, onSuccess }: DiscoverModalProps) {
  const [loading, setLoading] = useState(false);
  const [seedUrl, setSeedUrl] = useState('');
  const [error, setError] = useState('');

  const handleDiscover = async () => {
    if (!seedUrl) return;
    
    setLoading(true);
    setError('');

    try {
      await api.createTask({
        task_type: 'DISCOVER_PROGRAM', // Matches backend enum
        payload: { seed_url: seedUrl }
      });
      
      setSeedUrl('');
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (err: any) {
      console.error('Failed to create discovery task:', err);
      const errorMsg = err?.message || 'Failed to start discovery. Please try again.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Discover New Programs</DialogTitle>
          <DialogDescription>
            Enter a website URL or keyword to search for affiliate programs.
            Our AI agent will verify if they have an active program.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="seed-url">Website URL or Keyword</Label>
            <Input
              id="seed-url"
              placeholder="e.g., techradar.com or best gaming laptops"
              value={seedUrl}
              onChange={(e) => setSeedUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleDiscover()}
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
          <Button onClick={handleDiscover} disabled={!seedUrl || loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Start Discovery
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
