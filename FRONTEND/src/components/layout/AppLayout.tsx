import { ReactNode, useEffect, useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { SystemStatusBanner } from './SystemStatusBanner';
import { useConfig } from '@/context/ConfigContext';
import { api } from '@/lib/api';

interface AppLayoutProps {
  children: ReactNode;
  title?: string;
}

export function AppLayout({ children, title }: AppLayoutProps) {
  const { demoMode, setDemoMode } = useConfig();
  const [agentConnected, setAgentConnected] = useState(false);

  useEffect(() => {
    async function checkAgent() {
      try {
        const status = await api.getAgentStatus();
        setAgentConnected(status.connected);
      } catch (e) {
        setAgentConnected(false);
      }
    }
    
    checkAgent();
    const interval = setInterval(checkAgent, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar 
        agentConnected={demoMode ? true : agentConnected} 
        isDemo={demoMode} 
      />
      <div className="pl-64 transition-all duration-300">
        <SystemStatusBanner />
        <Header 
          title={title} 
          demoMode={demoMode} 
          onToggleDemoMode={() => setDemoMode(!demoMode)} 
        />
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
