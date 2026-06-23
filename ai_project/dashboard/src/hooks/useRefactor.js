import { useState } from 'react';
import * as api from '../services/api';

export function useRefactor(addToast) {
  const [refactorCode, setRefactorCode] = useState(
    `# Write or paste your Python code here\nimport os\nimport sys\nimport os # Duplicate import\n\ndef my_function(x):\n    for i in range(x):\n        print(i)\n`
  );
  const [refactoredResult, setRefactoredResult] = useState(null);
  const [refactorType, setRefactorType] = useState('optimize_imports');
  const [isRefactoring, setIsRefactoring] = useState(false);

  const handleRefactorCode = async () => {
    setIsRefactoring(true);
    setRefactoredResult(null);
    try {
      const data = await api.refactorCode(refactorCode, refactorType);
      setRefactoredResult(data);
      if (addToast) {
        addToast(
          data.status === 'success' ? 'Refactoring complete!' : 'Refactoring failed.',
          data.status === 'success' ? 'success' : 'error'
        );
      }
    } catch (err) {
      if (addToast) {
        addToast('Refactoring error: ' + err.message, 'error');
      }
    } finally {
      setIsRefactoring(false);
    }
  };

  return {
    refactorCode,
    setRefactorCode,
    refactoredResult,
    setRefactoredResult,
    refactorType,
    setRefactorType,
    isRefactoring,
    handleRefactorCode
  };
}
