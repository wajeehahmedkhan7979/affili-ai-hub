import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Mail, Trello, CreditCard, ExternalLink } from 'lucide-react';

const integrations = [
  {
    id: 'gmail',
    name: 'Gmail',
    description: 'Send automated emails and notifications',
    icon: Mail,
    status: 'available',
    category: 'Communication',
  },
  {
    id: 'trello',
    name: 'Trello',
    description: 'Sync tasks and manage workflow boards',
    icon: Trello,
    status: 'available',
    category: 'Productivity',
  },
  {
    id: 'stripe',
    name: 'Stripe',
    description: 'Process payments and track commissions',
    icon: CreditCard,
    status: 'coming_soon',
    category: 'Payments',
  },
];

export default function Integrations() {
  return (
    <AppLayout title="Integrations">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <p className="text-muted-foreground">
            Connect third-party services to enhance your workflow
          </p>
        </div>

        {/* Integrations Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {integrations.map((integration) => (
            <Card key={integration.id} className="relative overflow-hidden">
              {integration.status === 'coming_soon' && (
                <div className="absolute inset-0 bg-background/50 backdrop-blur-[1px] z-10 flex items-center justify-center">
                  <Badge variant="secondary" className="text-sm">Coming Soon</Badge>
                </div>
              )}
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                    <integration.icon className="h-6 w-6 text-primary" />
                  </div>
                  <Badge variant="outline">{integration.category}</Badge>
                </div>
                <CardTitle className="mt-4">{integration.name}</CardTitle>
                <CardDescription>{integration.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  className="w-full gap-2" 
                  variant={integration.status === 'available' ? 'default' : 'secondary'}
                  disabled={integration.status === 'coming_soon'}
                >
                  {integration.status === 'available' ? (
                    <>
                      Configure
                      <ExternalLink className="h-4 w-4" />
                    </>
                  ) : (
                    'Coming Soon'
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
