import { useState } from 'react';
import * as api from '../services/api';

export function useSandbox(addToast) {
  const [sandboxCode, setSandboxCode] = useState(
    `# Write your Python code here\ndef greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("Phoenix AI"))\n`
  );
  const [sandboxOutput, setSandboxOutput] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [sandboxTimeout, setSandboxTimeout] = useState(5.0);

  const handleRunSandbox = async () => {
    setIsRunning(true);
    setSandboxOutput(null);
    try {
      const data = await api.runCodeInSandbox(sandboxCode, sandboxTimeout);
      setSandboxOutput(data);
      if (addToast) {
        addToast(
          data.status === 'success' && data.exit_code === 0 ? 'Code executed successfully!' : 'Execution completed with issues.',
          data.exit_code === 0 ? 'success' : 'error'
        );
      }
    } catch (err) {
      setSandboxOutput({ status: 'error', stderr: err.message, stdout: '', exit_code: -1 });
    } finally {
      setIsRunning(false);
    }
  };

  return {
    sandboxCode,
    setSandboxCode,
    sandboxOutput,
    setSandboxOutput,
    isRunning,
    sandboxTimeout,
    setSandboxTimeout,
    handleRunSandbox
  };
}
