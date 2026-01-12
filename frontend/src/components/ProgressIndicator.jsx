import { useEffect, useState } from 'react';
import { getOptimizationStatus } from '../api/client';

function ProgressIndicator({ taskId, onComplete, onError }) {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Initializing optimization...');

  useEffect(() => {
    if (!taskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const statusData = await getOptimizationStatus(taskId);
        
        setStatus(statusData.status);
        setProgress(statusData.progress || 0);
        setMessage(statusData.message || 'Processing...');

        if (statusData.status === 'completed') {
          clearInterval(pollInterval);
          if (onComplete) {
            onComplete(statusData.results);
          }
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval);
          if (onError) {
            onError(statusData.message || 'Optimization failed');
          }
        }
      } catch (error) {
        console.error('Error polling status:', error);
        clearInterval(pollInterval);
        if (onError) {
          onError('Failed to check optimization status');
        }
      }
    }, 1000); // Poll every second

    return () => clearInterval(pollInterval);
  }, [taskId, onComplete, onError]);

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return '#10b981'; // green
      case 'failed':
        return '#ef4444'; // red
      case 'processing':
        return '#3b82f6'; // blue
      default:
        return '#6b7280'; // gray
    }
  };

  return (
    <div className="progress-indicator">
      <div className="progress-header">
        <h3>Optimization Progress</h3>
        <span className="status-badge" style={{ backgroundColor: getStatusColor() }}>
          {status.toUpperCase()}
        </span>
      </div>

      <div className="progress-bar-container">
        <div
          className="progress-bar"
          style={{
            width: `${progress}%`,
            backgroundColor: getStatusColor(),
          }}
        />
      </div>

      <div className="progress-info">
        <span className="progress-percentage">{progress}%</span>
        <span className="progress-message">{message}</span>
      </div>

      {status === 'processing' && (
        <div className="progress-spinner">
          <div className="spinner"></div>
        </div>
      )}
    </div>
  );
}

export default ProgressIndicator;
