import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';

interface HealthMetrics {
    active_workers: number;
    queue_depth: number;
    tasks_processed_1h: number;
    error_rate_1h: number;
}

const WorkerStatusWidget: React.FC = () => {
    const { token } = useAuth();
    const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchMetrics = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/analytics/health`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch health metrics');
            }

            const data = await response.json();
            setMetrics(data);
            setError(null);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (token) {
            fetchMetrics();
            const interval = setInterval(fetchMetrics, 5000); // Poll every 5 seconds
            return () => clearInterval(interval);
        }
    }, [token]);

    if (loading && !metrics) {
        return <div className="p-4 bg-white rounded-lg shadow animate-pulse h-32">Loading Worker Status...</div>;
    }

    if (error) {
        return <div className="p-4 bg-red-50 text-red-600 rounded-lg shadow">Error: {error}</div>;
    }

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Worker Fleet Status</h3>
            <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-600 font-medium">Active Workers</p>
                    <p className="text-2xl font-bold text-blue-900">{metrics?.active_workers || 0}</p>
                </div>
                <div className="p-4 bg-green-50 rounded-md">
                    <p className="text-sm text-green-600 font-medium">Tasks (Last 1h)</p>
                    <p className="text-2xl font-bold text-green-900">{metrics?.tasks_processed_1h || 0}</p>
                </div>
                <div className="p-4 bg-yellow-50 rounded-md">
                    <p className="text-sm text-yellow-600 font-medium">Queue Depth</p>
                    <p className="text-2xl font-bold text-yellow-900">{metrics?.queue_depth || 0}</p>
                </div>
                 <div className="p-4 bg-red-50 rounded-md">
                    <p className="text-sm text-red-600 font-medium">Error Rate</p>
                    <p className="text-2xl font-bold text-red-900">{(metrics?.error_rate_1h || 0).toFixed(2)}%</p>
                </div>
            </div>
        </div>
    );
};

export default WorkerStatusWidget;
