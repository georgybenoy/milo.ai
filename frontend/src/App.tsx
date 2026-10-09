import { useState, useEffect, useCallback } from 'react';
import { AppShell } from './components/AppShell';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { ChatWindow } from './components/ChatWindow';
import { MessageComposer } from './components/MessageComposer';
import { fetchHealth, fetchDatasetInfo, postChatMessage } from './api/client';
import type { ChatMessage, HealthStatus, DatasetInfo } from './types';

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Health and dataset state driven by real backend endpoints
  const [healthStatus, setHealthStatus] = useState<HealthStatus>('connecting');
  const [dataLoaded, setDataLoaded] = useState(false);

  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null);
  const [datasetLoading, setDatasetLoading] = useState(true);
  const [datasetError, setDatasetError] = useState<string | null>(null);

  // Responsive mobile drawer state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Poll health endpoint
  const pollHealth = useCallback(async () => {
    try {
      const res = await fetchHealth();
      setDataLoaded(Boolean(res.data_loaded));
      if (res.data_loaded) {
        setHealthStatus('ready');
      } else {
        setHealthStatus('connecting');
      }
    } catch {
      setHealthStatus('unavailable');
      setDataLoaded(false);
    }
  }, []);

  // Fetch dataset info
  const loadDatasetMetadata = useCallback(async () => {
    setDatasetLoading(true);
    setDatasetError(null);
    try {
      const data = await fetchDatasetInfo();
      setDatasetInfo(data);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : 'Failed to load dataset info');
    } finally {
      setDatasetLoading(false);
    }
  }, []);

  // Initial load and periodic health checks
  useEffect(() => {
    pollHealth();
    loadDatasetMetadata();

    const intervalId = window.setInterval(pollHealth, 10000);
    return () => window.clearInterval(intervalId);
  }, [pollHealth, loadDatasetMetadata]);

  // Handle escape key to close mobile drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMobileMenuOpen]);

  // Handle sending a message
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    setError(null);
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await postChatMessage(text.trim());
      if (res.error) {
        setError(res.error);
      } else if (res.reply) {
        const assistantMsg: ChatMessage = {
          id: `msg-${Date.now()}-assistant`,
          role: 'assistant',
          content: res.reply,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  // Start a fresh conversation
  const handleNewChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <AppShell>
      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar
          datasetInfo={datasetInfo}
          datasetLoading={datasetLoading}
          datasetError={datasetError}
          onNewChat={handleNewChat}
          isOpenMobile={isMobileMenuOpen}
          onCloseMobile={() => setIsMobileMenuOpen(false)}
        />

        {/* Main Application Surface */}
        <main className="flex-1 flex flex-col bg-[#21172D]/95 overflow-hidden">
          <Header
            healthStatus={healthStatus}
            dataLoaded={dataLoaded}
            onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
          />

          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            error={error}
            onSelectQuery={handleSendMessage}
            onRetry={() => {
              if (messages.length > 0 && messages[messages.length - 1].role === 'user') {
                handleSendMessage(messages[messages.length - 1].content);
              }
            }}
          />

          <MessageComposer
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </main>
      </div>
    </AppShell>
  );
}
