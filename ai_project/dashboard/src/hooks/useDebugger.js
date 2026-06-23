import { useState } from 'react';
import * as api from '../services/api';

export function useDebugger(addToast) {
  const [workspaceFiles, setWorkspaceFiles] = useState([]);
  const [detectedIssues, setDetectedIssues] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [repairResults, setRepairResults] = useState({});
  const [isRepairing, setIsRepairing] = useState({});

  const handleScanWorkspace = async () => {
    setIsScanning(true);
    try {
      const data = await api.scanWorkspace();
      setWorkspaceFiles(data.files || []);
      setDetectedIssues(data.issues || []);
      if (addToast) {
        addToast(
          `Scanned ${(data.files || []).length} files, found ${(data.issues || []).length} issues.`,
          (data.issues || []).length > 0 ? 'error' : 'success'
        );
      }
    } catch (err) {
      if (addToast) {
        addToast('Scan failed: ' + err.message, 'error');
      }
    } finally {
      setIsScanning(false);
    }
  };

  const handleRepairFile = async (filePath, errorMsg) => {
    setIsRepairing(prev => ({ ...prev, [filePath]: true }));
    try {
      const data = await api.repairFile(filePath, errorMsg);
      setRepairResults(prev => ({ ...prev, [filePath]: data }));
      if (addToast) {
        if (data.status === 'success') {
          addToast(`Repaired: ${filePath}`, 'success');
        } else {
          addToast(`Repair failed: ${filePath}`, 'error');
        }
      }
      handleScanWorkspace();
    } catch (err) {
      if (addToast) {
        addToast('Repair error: ' + err.message, 'error');
      }
    } finally {
      setIsRepairing(prev => ({ ...prev, [filePath]: false }));
    }
  };

  return {
    workspaceFiles,
    detectedIssues,
    isScanning,
    repairResults,
    isRepairing,
    handleScanWorkspace,
    handleRepairFile
  };
}
