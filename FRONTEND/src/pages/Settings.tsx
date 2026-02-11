import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { User, Bell, Shield, Palette, Database } from 'lucide-react';
import { useConfig } from '@/context/ConfigContext';
import { useToast } from '@/hooks/use-toast';

export default function Settings() {
  const { darkMode, setDarkMode, demoMode, setDemoMode } = useConfig();
  const { toast } = useToast();
  
  const handleSave = () => {
    toast({
      title: "Settings saved",
      description: "Your preferences have been updated locally.",
    });
  };

  return (
    <AppLayout title="Settings">
      <div className="max-w-4xl">
        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile" className="gap-2">
              <User className="h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2">
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-2">
              <Shield className="h-4 w-4" />
              Security
            </TabsTrigger>
            <TabsTrigger value="appearance" className="gap-2">
              <Palette className="h-4 w-4" />
              Appearance
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>
                  Update your account details and company information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="company">Company Name</Label>
                    <Input id="company" defaultValue="Automated Online Profits, LLC" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" defaultValue="admin@automatedonlineprofits.com" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="website">Website URL</Label>
                    <Input id="website" defaultValue="https://automatedonlineprofits.com" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timezone">Timezone</Label>
                    <Input id="timezone" defaultValue="America/New_York" />
                  </div>
                </div>
                <Separator />
                <div className="flex justify-end">
                  <Button onClick={handleSave}>Save Changes</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>
                  Configure how you receive updates and alerts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  {[
                    { title: "Application Approvals", desc: "Get notified when applications are approved" },
                    { title: "New Programs Found", desc: "Alerts when new programs match your criteria" },
                    { title: "Captcha Required", desc: "Notify when manual input is needed" },
                    { title: "Agent Disconnected", desc: "Alert when agent loses connection" }
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-foreground">{item.title}</p>
                        <p className="text-sm text-muted-foreground">{item.desc}</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle>Security Settings</CardTitle>
                <CardDescription>
                  Manage your API keys and authentication settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <div className="flex gap-2">
                    <Input type="text" defaultValue={import.meta.env.VITE_AGENT_API_KEY || "agent-secret-key"} readOnly />
                    <Button variant="outline" onClick={() => {
                        const key = import.meta.env.VITE_AGENT_API_KEY || "agent-secret-key";
                        navigator.clipboard.writeText(key);
                        toast({ title: "Copied", description: "API Key copied to clipboard" });
                    }}>Copy</Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Use this key to authenticate your local agent
                  </p>
                </div>
                <Separator />
                <div className="space-y-2">
                  <Label>Two-Factor Authentication</Label>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Add an extra layer of security to your account
                    </p>
                    <Button variant="outline">Enable 2FA</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="appearance">
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>
                  Customize the look and feel of your dashboard
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-foreground">Dark Mode</p>
                    <p className="text-sm text-muted-foreground">Toggle dark mode on or off</p>
                  </div>
                  <Switch 
                    checked={darkMode} 
                    onCheckedChange={setDarkMode} 
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-foreground">Demo Mode</p>
                    <p className="text-sm text-muted-foreground">Use mock data instead of live API</p>
                  </div>
                  <Switch 
                    checked={demoMode} 
                    onCheckedChange={setDemoMode} 
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
