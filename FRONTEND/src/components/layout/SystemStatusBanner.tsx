import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { AlertCircle, ShieldAlert } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export function SystemStatusBanner() {
  const { tenantId, isAuthenticated } = useAuth();
  const [status, setStatus] = useState<{
    ai_enabled: boolean;
    reason?: string;
  } | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !tenantId) return;

    async function checkStatus() {
      try {
        const data = await api.getAiStatus(tenantId);
        setStatus({
          ai_enabled: data.ai_enabled,
          reason: data.reason
        });
      } catch (e) {
        console.error("Failed to fetch tenant status:", e);
      }
    }

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [isAuthenticated, tenantId]);

  if (!status || status.ai_enabled) return null;

  return (
    <div className="bg-destructive/10 border-b border-destructive/20 p-2">
      <div className="container mx-auto">
        <Alert variant="destructive" className="border-none bg-transparent py-2">
          <ShieldAlert className="h-4 w-4" />
          <AlertTitle className="text-sm font-bold uppercase tracking-wider">
            EMERGENCY: AI Operations Disabled
          </AlertTitle>
          <AlertDescription className="text-xs">
            {status.reason || "The system is currently in a safety shutdown state. All autonomous tasks are halted."}
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
}
