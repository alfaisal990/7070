import { useState, useEffect } from 'react';
import * as api from '../services/api';

export function useHealth(addToast) {
  const [healthData, setHealthData] = useState(null);
  const [isOnline, setIsOnline] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);

  const fetchHealth = async () => {
    try {
      const data = await api.fetchHealth();
      setHealthData(data);
      setIsOnline(true);
    } catch (err) {
      setIsOnline(false);
    }
  };

  const handleTriggerBackup = async () => {
    setIsBackingUp(true);
    try {
      const data = await api.triggerBackup();
      if (addToast) {
        addToast(`Backup created: ${data.backup_file}`, 'success');
      }
    } catch (err) {
      if (addToast) {
        addToast('Backup failed: ' + err.message, 'error');
      }
    } finally {
      setIsBackingUp(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  return {
    healthData,
    isOnline,
    isBackingUp,
    handleTriggerBackup,
    fetchHealth
  };
}
