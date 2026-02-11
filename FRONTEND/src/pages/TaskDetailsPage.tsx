import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Clock, User, AlertCircle } from "lucide-react";
import { TaskStatusBadge } from "@/components/tasks/TaskStatusBadge";
import { LogsViewer } from "@/components/tasks/LogsViewer";
import { ScreenshotGallery } from "@/components/tasks/ScreenshotGallery";
import { format } from "date-fns";

import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

async function fetchTask(taskId: string): Promise<Task> {
  return api.getTask(taskId);
}

export default function TaskDetailsPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { tenantId } = useAuth();
  const [isResuming, setIsResuming] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const { data: task, isLoading, error, refetch } = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => fetchTask(taskId!),
    enabled: !!taskId,
  });

  const { data: aiStatus } = useQuery({
    queryKey: ["ai-status", tenantId],
    queryFn: () => api.getAiStatus(tenantId!),
    enabled: !!tenantId,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">Loading task details...</p>
      </div>
    );
  }

  const handleResume = async () => {
    setIsResuming(true);
    try {
      await api.resumeTask(taskId!, "Operator manually resumed");
      toast({ title: "Task Resumed", description: "Automation will continue shortly." });
      refetch();
    } catch (err: any) {
      toast({ variant: "destructive", title: "Action Blocked", description: err.message });
    } finally {
      setIsResuming(false);
    }
  };

  const handleCancel = async () => {
    setIsCancelling(true);
    try {
      await api.cancelTask(taskId!, "Operator manually cancelled");
      toast({ title: "Task Cancelled", description: "Task has been marked as failed by operator." });
      refetch();
    } catch (err: any) {
      toast({ variant: "destructive", title: "Failed to cancel", description: err.message });
    } finally {
      setIsCancelling(false);
    }
  };

  const formatDate = (date: string | null) => {
    if (!date) return "N/A";
    return format(new Date(date), "PPpp");
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/tasks")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Task Details</h1>
          <p className="text-muted-foreground text-sm">{task.id}</p>
        </div>
      </div>

      {/* Metadata Card */}
      <Card>
        <CardHeader>
          <CardTitle>Task Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Type</p>
              <p className="font-medium">{task.task_type}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <TaskStatusBadge status={task.status} />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Program Name</p>
              <p className="font-medium">{task.payload?.program_name || "N/A"}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Agent ID</p>
              <p className="font-medium flex items-center gap-2">
                {task.agent_id ? (
                  <>
                    <User className="h-4 w-4" />
                    {task.agent_id}
                  </>
                ) : (
                  "Unclaimed"
                )}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Retries</p>
              <p className="font-medium">
                {task.retry_count} / {task.max_retries}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {formatDate(task.created_at)}
              </p>
            </div>
            {task.claimed_at && (
              <div>
                <p className="text-sm text-muted-foreground">Claimed</p>
                <p className="font-medium">{formatDate(task.claimed_at)}</p>
              </div>
            )}
            {task.started_at && (
              <div>
                <p className="text-sm text-muted-foreground">Started</p>
                <p className="font-medium">{formatDate(task.started_at)}</p>
              </div>
            )}
            {task.completed_at && (
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="font-medium">{formatDate(task.completed_at)}</p>
              </div>
            )}
            {task.last_heartbeat && (
              <div>
                <p className="text-sm text-muted-foreground">Last Heartbeat</p>
                <p className="font-medium">{formatDate(task.last_heartbeat)}</p>
              </div>
            )}
          </div>

          {/* Error Message */}
          {task.error_message && (
            <div className="mt-4 p-4 bg-destructive/10 border border-destructive rounded-lg">
              <p className="text-sm font-medium text-destructive">Error</p>
              <p className="text-sm text-destructive/80 mt-1">{task.error_message}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Automation Details */}
      {(task.status === "PAUSED_FOR_CAPTCHA" || task.status === "PAUSED_FOR_USER" || task.status === "PAUSED_LOW_CONFIDENCE") && (
        <Card className="border-amber-200 bg-amber-50 shadow-sm transition-all animate-in fade-in slide-in-from-top-2">
          <CardHeader>
            <CardTitle className="text-amber-800 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Human Intervention Required
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-amber-700">
              The automation has paused because: 
              <span className="font-bold ml-1">
                {task.status === "PAUSED_FOR_CAPTCHA" ? "CAPTCHA detected on page." : 
                 task.status === "PAUSED_LOW_CONFIDENCE" ? "Low confidence in AI predictions." : 
                 "Awaiting user approval for certain fields."}
              </span>
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              {task.payload?.signup_url && (
                <Button variant="outline" className="border-amber-200 hover:bg-amber-100" onClick={() => window.open(task.payload.signup_url, '_blank')}>
                  Open Browser to Solve
                </Button>
              )}
              
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="inline-block">
                      <Button 
                        disabled={isResuming || (aiStatus && !aiStatus.ai_enabled)}
                        onClick={handleResume}
                        className="bg-amber-600 hover:bg-amber-700 text-white"
                      >
                        {isResuming ? "Resuming..." : "Resume Automation"}
                      </Button>
                    </div>
                  </TooltipTrigger>
                  {aiStatus && !aiStatus.ai_enabled && (
                    <TooltipContent>
                      <p>Resume blocked: Kill-switch active for this tenant.</p>
                    </TooltipContent>
                  )}
                </Tooltip>
              </TooltipProvider>

              <Button 
                variant="ghost" 
                className="text-amber-700 hover:bg-amber-100 hover:text-amber-800"
                onClick={handleCancel}
                disabled={isCancelling}
              >
                {isCancelling ? "Cancelling..." : "Cancel Task"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {task.result?.predictions && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              AI Automation Decisions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative overflow-x-auto border rounded-lg">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-slate-50 border-b">
                  <tr>
                    <th className="px-4 py-3">Field Label</th>
                    <th className="px-4 py-3">Value</th>
                    <th className="px-4 py-3">Source</th>
                    <th className="px-4 py-3">Confidence</th>
                    <th className="px-4 py-3">Reasoning</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(task.result.predictions).map(([field, pred]: [string, any]) => (
                    <tr key={field} className="border-b hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium">{field}</td>
                      <td className="px-4 py-3">{pred.value || pred.answer || "N/A"}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-[10px] font-bold ${pred.source === 'RAG' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
                          {pred.source || "LLM"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${pred.confidence >= 0.8 ? 'text-green-600' : pred.confidence >= 0.6 ? 'text-amber-600' : 'text-red-500'}`}>
                            {Math.round(pred.confidence * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground italic">
                        {pred.reasoning || "Matched via historical similarity"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Screenshots */}
      <ScreenshotGallery 
        screenshots={task.result?.screenshots || null} 
        taskId={task.id} 
      />

      {/* Logs */}
      <LogsViewer logs={task.logs} />

      {/* Result Data */}
      {task.result && (
        <Card>
          <CardHeader>
            <CardTitle>Technical Context (JSON)</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-slate-50 p-4 rounded-lg overflow-auto max-h-64 text-sm font-mono border">
              {JSON.stringify(task.result, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
