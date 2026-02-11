import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ConfigProvider } from "./context/ConfigContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Programs from "./pages/Programs";
import Applications from "./pages/Applications";
import Tasks from "./pages/Tasks";
import TaskDetailsPage from "./pages/TaskDetailsPage";
import ResponsePool from "./pages/ResponsePool";
import AgentSetup from "./pages/AgentSetup";
import Integrations from "./pages/Integrations";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import { Navigate, useLocation } from "react-router-dom";

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading session...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <ConfigProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/programs" element={<ProtectedRoute><Programs /></ProtectedRoute>} />
              <Route path="/applications" element={<ProtectedRoute><Applications /></ProtectedRoute>} />
              <Route path="/tasks" element={<ProtectedRoute><Tasks /></ProtectedRoute>} />
              <Route path="/tasks/:taskId" element={<ProtectedRoute><TaskDetailsPage /></ProtectedRoute>} />
              <Route path="/response-pool" element={<ProtectedRoute><ResponsePool /></ProtectedRoute>} />
              <Route path="/agent" element={<ProtectedRoute><AgentSetup /></ProtectedRoute>} />
              <Route path="/integrations" element={<ProtectedRoute><Integrations /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </ConfigProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
