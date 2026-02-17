import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';

const GovernanceControls: React.FC = () => {
    const { token } = useAuth();
    const [killSwitchActive, setKillSwitchActive] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(true);
    const [confirming, setConfirming] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/analytics/governance`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (!response.ok) throw new Error('Failed to fetch governance status');
            const data = await response.json();
            setKillSwitchActive(data.is_kill_switch_active);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const toggleKillSwitch = async () => {
        try {
            const newState = !killSwitchActive;
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/governance/kill-switch?active=${newState}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Failed to toggle kill switch');
            
            setKillSwitchActive(newState);
            setConfirming(false);
        } catch (err: any) {
            setError(err.message);
        }
    };

    useEffect(() => {
        if (token) fetchStatus();
    }, [token]);

    if (loading) return <div className="p-4 bg-white rounded-lg shadow h-32 animate-pulse">Loading Controls...</div>;

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Governance Controls</h3>
            
            {error && <div className="mb-4 text-red-600 text-sm">{error}</div>}

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                    <h4 className="font-medium text-gray-900">System Kill-Switch</h4>
                    <p className="text-sm text-gray-500">Emergency stop for all active workers.</p>
                </div>
                
                {confirming ? (
                    <div className="flex items-center gap-2">
                        <button 
                            onClick={() => setConfirming(false)}
                            className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={toggleKillSwitch}
                            className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 font-bold"
                        >
                            CONFIRM
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => setConfirming(true)}
                        className={`px-4 py-2 rounded-full font-bold transition-colors ${
                            killSwitchActive 
                                ? 'bg-red-100 text-red-700 border-2 border-red-500 hover:bg-red-200' 
                                : 'bg-green-100 text-green-700 border-2 border-green-500 hover:bg-green-200'
                        }`}
                    >
                        {killSwitchActive ? "STOPPED" : "ACTIVE"}
                    </button>
                )}
            </div>
        </div>
    );
};

export default GovernanceControls;
