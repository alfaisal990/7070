import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatPage } from './pages/ChatPage';
import { SandboxPage } from './pages/SandboxPage';
import { MemoryPage } from './pages/MemoryPage';
import { DebuggerPage } from './pages/DebuggerPage';
import { RefactorPage } from './pages/RefactorPage';
import { AIExplorerPage } from './pages/AIExplorerPage';

import { useToast } from './hooks/useToast';
import { useHealth } from './hooks/useHealth';
import { useDebugger } from './hooks/useDebugger';
import { useRefactor } from './hooks/useRefactor';
import { useSandbox } from './hooks/useSandbox';
import { useMemory } from './hooks/useMemory';
import { useChat } from './hooks/useChat';

function App() {
  const [activeTab, setActiveTab] = useState('chat');

  // Custom State Orchestration Hooks
  const { toasts, addToast } = useToast();
  const { healthData, isOnline, isBackingUp, handleTriggerBackup } = useHealth(addToast);
  const {
    workspaceFiles,
    detectedIssues,
    isScanning,
    repairResults,
    isRepairing,
    handleScanWorkspace,
    handleRepairFile
  } = useDebugger(addToast);

  const {
    refactorCode,
    setRefactorCode,
    refactoredResult,
    refactorType,
    setRefactorType,
    isRefactoring,
    handleRefactorCode
  } = useRefactor(addToast);

  const {
    sandboxCode,
    setSandboxCode,
    sandboxOutput,
    isRunning,
    sandboxTimeout,
    setSandboxTimeout,
    handleRunSandbox
  } = useSandbox(addToast);

  const {
    memories,
    newMemoryText,
    setNewMemoryText,
    newMemoryMeta,
    setNewMemoryMeta,
    isSavingMemory,
    memorySearch,
    setMemorySearch,
    searchResults,
    setSearchResults,
    isSearching,
    fetchMemories,
    handleMemorySearch,
    handleClearMemory,
    handleSaveMemory
  } = useMemory(addToast);

  const {
    messages,
    inputText,
    setInputText,
    isTyping,
    streamMode,
    setStreamMode,
    messagesEndRef,
    handleSendMessage
  } = useChat(fetchMemories);

  return (
    <div className="layout">
      {/* Sidebar Panel */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        healthData={healthData}
        isOnline={isOnline}
        onScanWorkspace={handleScanWorkspace}
        onTriggerBackup={handleTriggerBackup}
        isBackingUp={isBackingUp}
      />

      {/* Main Content Area */}
      <main className="main-panel">
        <header className="panel-header">
          <h2>
            {activeTab === 'chat' && '💬 AI Assistant Chat'}
            {activeTab === 'sandbox' && '💻 Secure Code Execution Sandbox'}
            {activeTab === 'memory' && '🧠 Long-Term Semantic Memory Store'}
            {activeTab === 'debug' && '🔧 Proactive Workspace Debugger'}
            {activeTab === 'refactor' && '⚡ Automated Code Refactorer'}
            {activeTab === 'ai_explorer' && '🚀 AI Types Explorer'}
          </h2>
        </header>

        {/* Tab 1: Chat Assistant */}
        {activeTab === 'chat' && (
          <ChatPage
            messages={messages}
            isTyping={isTyping}
            inputText={inputText}
            setInputText={setInputText}
            streamMode={streamMode}
            setStreamMode={setStreamMode}
            isOnline={isOnline}
            onSubmit={handleSendMessage}
            messagesEndRef={messagesEndRef}
          />
        )}

        {/* Tab 2: Code Sandbox */}
        {activeTab === 'sandbox' && (
          <SandboxPage
            sandboxCode={sandboxCode}
            setSandboxCode={setSandboxCode}
            sandboxTimeout={sandboxTimeout}
            setSandboxTimeout={setSandboxTimeout}
            isRunning={isRunning}
            isOnline={isOnline}
            sandboxOutput={sandboxOutput}
            onRun={handleRunSandbox}
          />
        )}

        {/* Tab 3: Vector Memory */}
        {activeTab === 'memory' && (
          <MemoryPage
            newMemoryText={newMemoryText}
            setNewMemoryText={setNewMemoryText}
            newMemoryMeta={newMemoryMeta}
            setNewMemoryMeta={setNewMemoryMeta}
            isSavingMemory={isSavingMemory}
            onSaveMemory={handleSaveMemory}
            memorySearch={memorySearch}
            setMemorySearch={setMemorySearch}
            isSearching={isSearching}
            onMemorySearch={handleMemorySearch}
            searchResults={searchResults}
            setSearchResults={setSearchResults}
            memories={memories}
            onClearMemory={handleClearMemory}
            isOnline={isOnline}
            addToast={addToast}
          />
        )}

        {/* Tab 4: Auto Debugger */}
        {activeTab === 'debug' && (
          <DebuggerPage
            workspaceFiles={workspaceFiles}
            detectedIssues={detectedIssues}
            isScanning={isScanning}
            isOnline={isOnline}
            repairResults={repairResults}
            isRepairing={isRepairing}
            onScan={handleScanWorkspace}
            onRepair={handleRepairFile}
          />
        )}

        {/* Tab 5: Code Refactorer */}
        {activeTab === 'refactor' && (
          <RefactorPage
            refactorCode={refactorCode}
            setRefactorCode={setRefactorCode}
            refactorType={refactorType}
            setRefactorType={setRefactorType}
            isRefactoring={isRefactoring}
            isOnline={isOnline}
            refactoredResult={refactoredResult}
            onRefactor={handleRefactorCode}
            addToast={addToast}
          />
        )}

        {/* Tab 6: AI Explorer */}
        {activeTab === 'ai_explorer' && (
          <AIExplorerPage
            isOnline={isOnline}
            addToast={addToast}
          />
        )}
      </main>

      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
