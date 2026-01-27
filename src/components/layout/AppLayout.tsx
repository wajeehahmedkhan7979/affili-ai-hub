import { ReactNode, useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';

interface AppLayoutProps {
  children: ReactNode;
  title?: string;
}

export function AppLayout({ children, title }: AppLayoutProps) {
  const [demoMode, setDemoMode] = useState(true);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar agentConnected={demoMode} />
      <div className="pl-64 transition-all duration-300">
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
