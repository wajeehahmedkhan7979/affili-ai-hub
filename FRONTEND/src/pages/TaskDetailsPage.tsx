import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Clock, User, AlertCircle } from "lucide-react";
import { TaskStatusBadge } from "@/components/tasks/TaskStatusBadge";
import { LogsViewer } from "@/components/tasks/LogsViewer";
import { ScreenshotGallery } from "@/components/tasks/ScreenshotGallery";
import { format } from "date-fns";

interface Task {
  id: string;
  task_type: string;
  status: string;
  payload: any;
  result: any;
  agent_id: string | null;
  retry_count: number;
  max_retries: number;
  logs: string | null;
  screenshot_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  claimed_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  last_heartbeat: string | null;
}

async function fetchTask(taskId: string): Promise<Task> {
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const response = await fetch(`${baseUrl}/api/v1/tasks/${taskId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch task");
  }
  return response.json();
}

export default function TaskDetailsPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();

  const { data: task, isLoading, error } = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => fetchTask(taskId!),
    enabled: !!taskId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">Loading task details...</p>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-destructive">Failed to load task details</p>
        <Button variant="outline" onClick={() => navigate("/tasks")}>
          Back to Tasks
        </Button>
      </div>
    );
  }

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
            <CardTitle>Result Data</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-slate-50 p-4 rounded-lg overflow-auto max-h-64 text-sm">
              {JSON.stringify(task.result, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
