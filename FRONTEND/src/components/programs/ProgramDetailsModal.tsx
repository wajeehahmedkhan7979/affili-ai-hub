import { Program } from '@/lib/mock-data';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, TrendingUp, Calendar, Network } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ProgramDetailsModalProps {
  program: Program | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApply?: (program: Program) => void;
  onRemove?: (program: Program) => void;
}

export function ProgramDetailsModal({ 
  program, 
  open, 
  onOpenChange,
  onApply,
  onRemove 
}: ProgramDetailsModalProps) {
  if (!program) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary font-semibold text-lg">
              {program.name.charAt(0)}
            </div>
            <div>
              <span className="text-xl">{program.name}</span>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline">{program.network}</Badge>
                <Badge 
                  variant="secondary"
                  className={program.source === 'discovered' ? 'bg-blue-500/10 text-blue-600' : ''}
                >
                  {program.source || 'manual'}
                </Badge>
              </div>
            </div>
          </DialogTitle>
          <DialogDescription>
            {program.description || 'No description available'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Commission Info */}
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <h4 className="font-semibold text-sm">Commission Details</h4>
            </div>
            <p className="text-2xl font-bold text-green-600">
              {program.commission || 'N/A'}
            </p>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-border bg-muted/50 p-3">
              <div className="flex items-center gap-2 mb-1">
                <Network className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Network</span>
              </div>
              <p className="font-medium">{program.network}</p>
            </div>

            <div className="rounded-lg border border-border bg-muted/50 p-3">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Discovered</span>
              </div>
              <p className="font-medium">
                {formatDistanceToNow(new Date(program.created_at), { addSuffix: true })}
              </p>
            </div>
          </div>

          {/* Confidence Score (if discovered) */}
          {program.source === 'discovered' && program.confidence_score && (
            <div className="rounded-lg border border-border bg-blue-500/5 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">AI Confidence Score</span>
                <span className="text-lg font-bold text-blue-600">
                  {(program.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-600 transition-all"
                  style={{ width: `${program.confidence_score * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* URL */}
          {program.url && (
            <div className="rounded-lg border border-border bg-muted/50 p-3">
              <span className="text-xs text-muted-foreground block mb-1">Program URL</span>
              <a 
                href={program.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline flex items-center gap-1 break-all"
              >
                {program.url}
                <ExternalLink className="h-3 w-3 flex-shrink-0" />
              </a>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          {onRemove && (
            <Button 
              variant="outline" 
              className="text-destructive hover:text-destructive"
              onClick={() => {
                onRemove(program);
                onOpenChange(false);
              }}
            >
              Remove Program
            </Button>
          )}
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {onApply && program.status === 'Discovered' && (
            <Button onClick={() => {
              onApply(program);
              onOpenChange(false);
            }}>
              Apply Now
            </Button>
          )}
          {program.url && (
            <Button asChild>
              <a href={program.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                Visit Site
              </a>
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
