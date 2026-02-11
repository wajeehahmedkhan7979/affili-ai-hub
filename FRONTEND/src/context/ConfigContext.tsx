import React, { createContext, useContext, useEffect, useState } from 'react';

interface ConfigContextType {
  demoMode: boolean;
  setDemoMode: (enabled: boolean) => void;
  darkMode: boolean;
  setDarkMode: (enabled: boolean) => void;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [demoMode, setDemoModeState] = useState(() => {
    const saved = localStorage.getItem('demoMode');
    return saved !== null ? JSON.parse(saved) : true;
  });

  const [darkMode, setDarkModeState] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved !== null ? JSON.parse(saved) : false;
  });

  const setDemoMode = (enabled: boolean) => {
    setDemoModeState(enabled);
    localStorage.setItem('demoMode', JSON.stringify(enabled));
  };

  const setDarkMode = (enabled: boolean) => {
    setDarkModeState(enabled);
    localStorage.setItem('darkMode', JSON.stringify(enabled));
  };

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <ConfigContext.Provider value={{ demoMode, setDemoMode, darkMode, setDarkMode }}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
}
