import React from 'react';
import WorkerStatusWidget from '../components/dashboard/WorkerStatusWidget';
import GovernanceControls from '../components/dashboard/GovernanceControls';
import TaskInspector from '../components/dashboard/TaskInspector';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const OperatorDashboard: React.FC = () => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();

    // Basic protection (though App.tsx should handle this too)
    if (!token) {
        return <div className="p-8 text-center">Redirecting to login...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Operator Dashboard</h1>
                    <p className="text-gray-500">Live System Monitoring & Control</p>
                </div>
                <div className="flex gap-4">
                    <button 
                         onClick={() => navigate('/')}
                         className="px-4 py-2 bg-white text-gray-700 rounded shadow-sm hover:bg-gray-50"
                    >
                        Back to Home
                    </button>
                    <button 
                        onClick={logout}
                        className="px-4 py-2 bg-white text-red-600 rounded shadow-sm hover:bg-red-50"
                    >
                        Logout
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {/* Top Row: Status & Controls */}
                <div className="col-span-1 md:col-span-1 lg:col-span-2">
                     <WorkerStatusWidget />
                </div>
                <div className="col-span-1">
                    <GovernanceControls />
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
                {/* Bottom Row: Detailed Inspection */}
                <TaskInspector />
            </div>
        </div>
    );
};

export default OperatorDashboard;
