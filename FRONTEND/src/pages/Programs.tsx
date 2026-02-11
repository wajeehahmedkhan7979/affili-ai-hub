import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { api } from '@/lib/api';
import { Program } from '@/lib/mock-data';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Search, 
  Filter, 
  ExternalLink, 
  MoreHorizontal,
  Plus,
  RefreshCw
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { ApplicationModal } from '@/components/programs/ApplicationModal';
import { DiscoverModal } from '@/components/programs/DiscoverModal';
import { ProgramDetailsModal } from '@/components/programs/ProgramDetailsModal';
import { BulkApplyModal } from '@/components/programs/BulkApplyModal';
import { formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';

const statusColors: Record<string, string> = {
  Discovered: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  Applied: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  Approved: 'bg-green-500/10 text-green-600 border-green-500/20',
  Rejected: 'bg-destructive/10 text-destructive border-destructive/20',
};

const networks = ['All Networks', 'ClickBank', 'ShareASale', 'CJ Affiliate', 'Impact'];
const statuses = ['All Statuses', 'Discovered', 'Applied', 'Approved', 'Rejected'];

export default function Programs() {
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [network, setNetwork] = useState('All Networks');
  const [status, setStatus] = useState('All Statuses');
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [showDiscoverModal, setShowDiscoverModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showBulkApplyModal, setShowBulkApplyModal] = useState(false);
  const [programToDelete, setProgramToDelete] = useState<Program | null>(null);

  useEffect(() => {
    // Check for action=discover in URL
    if (searchParams.get('action') === 'discover') {
      setShowDiscoverModal(true);
    }
  }, [searchParams]);

  useEffect(() => {
    loadPrograms();
  }, [search, network, status]);

  async function loadPrograms() {
    setLoading(true);
    try {
      const filters: any = {};
      if (search) filters.search = search;
      if (network !== 'All Networks') filters.network = network;
      if (status !== 'All Statuses') filters.status = status;
      
      const data = await api.getPrograms(filters);
      setPrograms(data);
    } catch (error) {
      console.error('Failed to load programs:', error);
    } finally {
      setLoading(false);
    }
  }

  const handleApply = (program: Program) => {
    setSelectedProgram(program);
    setShowApplicationModal(true);
  };

  const handleViewDetails = (program: Program) => {
    setSelectedProgram(program);
    setShowDetailsModal(true);
  };

  const handleAddToChannel = (program: Program) => {
    toast({
      title: "Added to Channel",
      description: `${program.name} has been added to your channel.`,
    });
  };

  const handleRemove = (program: Program) => {
    setProgramToDelete(program);
  };

  const confirmDelete = async () => {
    if (!programToDelete) return;
    
    try {
      // Call API to delete program
      await api.deleteProgram(programToDelete.id);
      
      // Remove from local state on success
      setPrograms(programs.filter(p => p.id !== programToDelete.id));
      
      toast({
        title: "Program Removed",
        description: `${programToDelete.name} has been removed.`,
      });
    } catch (error: any) {
      console.error('Delete error:', error);
      const errorMsg = error?.message || 'Failed to remove program. Please try again.';
      toast({
        title: "Error",
        description: errorMsg,
        variant: "destructive",
      });
    } finally {
      setProgramToDelete(null);
    }
  };

  return (
    <AppLayout title="Programs">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-muted-foreground">
              Manage discovered affiliate programs and track applications
            </p>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              className="gap-2" 
              onClick={() => setShowBulkApplyModal(true)}
              disabled={programs.filter(p => p.status === 'Discovered').length === 0}
            >
              Bulk Apply
            </Button>
            <Button className="gap-2" onClick={() => setShowDiscoverModal(true)}>
              <Plus className="h-4 w-4" />
              Discover New
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search programs..."
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={network} onValueChange={setNetwork}>
            <SelectTrigger className="w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {networks.map((n) => (
                <SelectItem key={n} value={n}>{n}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {statuses.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => loadPrograms()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {/* Table */}
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead>Program</TableHead>
                <TableHead>Network</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Commission</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Action</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={8}> {/* Corrected colSpan */}
                      <Skeleton className="h-12 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              ) : programs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                    No programs found. Try adjusting your filters or discover new programs.
                  </TableCell>
                </TableRow>
              ) : (
                programs.map((program) => (
                  <TableRow key={program.id} className="group">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary font-semibold text-sm">
                          {program.name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium text-card-foreground">{program.name}</p>
                          <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                            {program.description}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{program.network}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant="secondary"
                        className={program.source === 'discovered' ? 'bg-blue-500/10 text-blue-600' : ''}
                      >
                        {program.source || 'manual'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {program.source === 'discovered' && program.confidence_score ? (
                        <span className="text-sm font-medium">
                          {(program.confidence_score * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-sm">N/A</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="font-medium text-green-600">{program.commission || 'N/A'}</span>
                    </TableCell>
                    <TableCell>
                      <Badge className={cn("border", statusColors[program.status])}>
                        {program.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDistanceToNow(new Date(program.created_at), { addSuffix: true })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button 
                          size="sm" 
                          onClick={() => handleApply(program)}
                          disabled={program.status !== 'Discovered'}
                        >
                          Apply
                        </Button>
                        <Button size="sm" variant="outline" asChild>
                          <a href={program.url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button size="sm" variant="ghost">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleViewDetails(program)}>
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleAddToChannel(program)}>
                              Add to Channel
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="text-destructive"
                              onClick={() => handleRemove(program)}
                            >
                              Remove
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Application Modal */}
        <ApplicationModal
          program={selectedProgram}
          open={showApplicationModal}
          onOpenChange={setShowApplicationModal}
        />
        
        {/* Discover Modal */}
        <DiscoverModal
          open={showDiscoverModal}
          onOpenChange={setShowDiscoverModal}
          onSuccess={() => loadPrograms()}
        />

        {/* Bulk Apply Modal */}
        <BulkApplyModal
          open={showBulkApplyModal}
          onOpenChange={setShowBulkApplyModal}
          onSuccess={() => loadPrograms()}
        />

        {/* Details Modal */}
        <ProgramDetailsModal
          program={selectedProgram}
          open={showDetailsModal}
          onOpenChange={setShowDetailsModal}
          onApply={handleApply}
          onRemove={handleRemove}
        />

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={!!programToDelete} onOpenChange={(open) => !open && setProgramToDelete(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Remove Program?</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to remove "{programToDelete?.name}"? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                Remove
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppLayout>
  );
}
