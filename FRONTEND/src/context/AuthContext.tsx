import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  role: 'OWNER' | 'ADMIN' | 'OPERATOR' | 'VIEWER';
  tenant_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  tenantId: string | null;
  isAuthenticated: boolean;
  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initialize auth state from localStorage
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');
    const storedTenantId = localStorage.getItem('auth_tenant_id');

    if (storedToken && storedUser && storedTenantId) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        setTenantId(storedTenantId);
      } catch (e) {
        console.error("Failed to restore auth state:", e);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('auth_tenant_id');
      }
    }
    setIsLoading(false);
  }, []);

  const login = (newToken: string, refreshToken: string, userData: User) => {
    setToken(newToken);
    setUser(userData);
    setTenantId(userData.tenant_id);
    
    localStorage.setItem('auth_token', newToken);
    localStorage.setItem('auth_refresh_token', refreshToken);
    localStorage.setItem('auth_user', JSON.stringify(userData));
    localStorage.setItem('auth_tenant_id', userData.tenant_id);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setTenantId(null);
    
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_refresh_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_tenant_id');
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      tenantId,
      isAuthenticated: !!token, 
      login, 
      logout,
      isLoading 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
