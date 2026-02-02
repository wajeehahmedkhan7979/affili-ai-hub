import { Badge } from "@/components/ui/badge";

interface TaskStatusBadgeProps {
  status: string;
}

const statusConfig: Record<string, { variant: string; className: string }> = {
  PENDING: { variant: "secondary", className: "bg-gray-500 hover:bg-gray-600" },
  CLAIMED: { variant: "default", className: "bg-blue-500 hover:bg-blue-600" },
  RUNNING: { variant: "default", className: "bg-yellow-500 hover:bg-yellow-600" },
  COMPLETED: { variant: "default", className: "bg-green-500 hover:bg-green-600" },
  FAILED: { variant: "destructive", className: "bg-red-500 hover:bg-red-600" },
};

export function TaskStatusBadge({ status }: TaskStatusBadgeProps) {
  const config = statusConfig[status] || { variant: "outline", className: "" };
  
  return (
    <Badge variant={config.variant as any} className={config.className}>
      {status}
    </Badge>
  );
}
