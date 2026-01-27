import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Copy, Terminal, Apple, MonitorDot, HelpCircle, Wifi, WifiOff } from 'lucide-react';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

export default function AgentSetup() {
  const { toast } = useToast();
  const [agentConnected] = useState(true);
  
  const dockerCommand = `docker run -d \\
  -e API_BASE_URL=https://api.affili-ai.com \\
  -e AGENT_API_KEY=your-api-key-here \\
  --name affili-agent \\
  affili-ai/agent:latest`;

  const copyCommand = () => {
    navigator.clipboard.writeText(dockerCommand);
    toast({
      title: "Copied!",
      description: "Docker command copied to clipboard",
    });
  };

  return (
    <AppLayout title="Agent Setup">
      <div className="max-w-4xl space-y-8">
        {/* Status Card */}
        <Card className={cn(
          "border-2",
          agentConnected ? "border-green-500/50 bg-green-500/5" : "border-destructive/50 bg-destructive/5"
        )}>
          <CardContent className="flex items-center gap-4 py-6">
            <div className={cn(
              "flex h-12 w-12 items-center justify-center rounded-full",
              agentConnected ? "bg-green-500/10" : "bg-destructive/10"
            )}>
              {agentConnected ? (
                <Wifi className="h-6 w-6 text-green-500" />
              ) : (
                <WifiOff className="h-6 w-6 text-destructive" />
              )}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground">
                Agent Status: {agentConnected ? 'Connected' : 'Disconnected'}
              </h3>
              <p className="text-sm text-muted-foreground">
                {agentConnected 
                  ? 'Your local agent is running and connected successfully.' 
                  : 'Your local agent is not connected. Follow the steps below to set it up.'}
              </p>
            </div>
            <Badge variant={agentConnected ? 'default' : 'destructive'}>
              {agentConnected ? 'Online' : 'Offline'}
            </Badge>
          </CardContent>
        </Card>

        {/* Installation Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Installation</CardTitle>
            <CardDescription>
              Install the local agent on your machine to enable browser automation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Step 1 */}
            <div className="flex gap-4">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                1
              </div>
              <div className="flex-1 space-y-3">
                <h4 className="font-medium text-foreground">Install Docker</h4>
                <p className="text-sm text-muted-foreground">
                  Download and install Docker Desktop for your operating system.
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" asChild>
                    <a href="https://www.docker.com/products/docker-desktop" target="_blank" rel="noopener noreferrer" className="gap-2">
                      <Apple className="h-4 w-4" />
                      Mac
                    </a>
                  </Button>
                  <Button variant="outline" size="sm" asChild>
                    <a href="https://www.docker.com/products/docker-desktop" target="_blank" rel="noopener noreferrer" className="gap-2">
                      <MonitorDot className="h-4 w-4" />
                      Windows
                    </a>
                  </Button>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-4">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                2
              </div>
              <div className="flex-1 space-y-3">
                <h4 className="font-medium text-foreground">Run the Agent</h4>
                <p className="text-sm text-muted-foreground">
                  Open your terminal and run the following command:
                </p>
                <div className="relative">
                  <pre className="rounded-lg bg-secondary p-4 text-sm text-secondary-foreground overflow-x-auto font-mono">
                    {dockerCommand}
                  </pre>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="absolute right-2 top-2"
                    onClick={copyCommand}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-4">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                3
              </div>
              <div className="flex-1 space-y-3">
                <h4 className="font-medium text-foreground">Verify Connection</h4>
                <p className="text-sm text-muted-foreground">
                  Once the agent is running, it will automatically connect to AFFILI-AI. 
                  The status above will show "Connected" when successful.
                </p>
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  Agent connected successfully
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Troubleshooting */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HelpCircle className="h-5 w-5" />
              Troubleshooting
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-foreground">Docker not starting?</h4>
              <p className="text-sm text-muted-foreground">
                Make sure Docker Desktop is running and you've accepted the terms of service.
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-foreground">Connection issues?</h4>
              <p className="text-sm text-muted-foreground">
                Check that your API key is correct and that you have an active internet connection.
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-foreground">Need help?</h4>
              <p className="text-sm text-muted-foreground">
                Contact support at support@automatedonlineprofits.com for assistance.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
