import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy } from "lucide-react";
import { toast } from "sonner";

interface LogsViewerProps {
  logs: string | null;
}

export function LogsViewer({ logs }: LogsViewerProps) {
  const handleCopy = () => {
    if (logs) {
      navigator.clipboard.writeText(logs);
      toast.success("Logs copied to clipboard");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Execution Logs</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          disabled={!logs}
        >
          <Copy className="h-4 w-4 mr-2" />
          Copy
        </Button>
      </CardHeader>
      <CardContent>
        {logs ? (
          <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg overflow-auto max-h-96 text-sm font-mono whitespace-pre-wrap">
            {logs}
          </pre>
        ) : (
          <p className="text-muted-foreground text-center py-8">
            No logs available
          </p>
        )}
      </CardContent>
    </Card>
  );
}
