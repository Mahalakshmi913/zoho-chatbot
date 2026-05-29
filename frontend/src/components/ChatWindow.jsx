import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Send } from 'lucide-react';
import { sendMessage as apiSendMessage } from '../api';
import MessageBubble from './MessageBubble';
import ConfirmDialog from './ConfirmDialog';

export default function ChatWindow() {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Pending action state to handle HIL flow
  const [pendingConfirmation, setPendingConfirmation] = useState(false);
  const [actionDescription, setActionDescription] = useState('');

  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Generate unique session ID on mount
    setSessionId(uuidv4());
    
    // Initial greeting
    setMessages([
      {
        id: 'init-1',
        role: 'assistant',
        content: "Hi there! I'm your Zoho Projects Assistant. I can help you list projects, view tasks, create new tasks, and check team utilization. What would you like to do?"
      }
    ]);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    // Add user message to UI immediately
    const userMsg = { id: uuidv4(), role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setPendingConfirmation(false);
    setActionDescription('');

    try {
      const result = await apiSendMessage(text, sessionId);
      
      // Add assistant response
      const botMsg = { id: uuidv4(), role: 'assistant', content: result.response };
      setMessages(prev => [...prev, botMsg]);
      
      // If it requires human confirmation for an action
      if (result.pending_confirmation) {
        setPendingConfirmation(true);
        setActionDescription(result.action_description);
      }
      
    } catch (err) {
      console.error("Failed to send message", err);
      setMessages(prev => [...prev, { 
        id: uuidv4(), 
        role: 'assistant', 
        content: "Sorry, I encountered an error communicating with the server. Please check if your Zoho session expired." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!loading && !pendingConfirmation) {
      sendMessage(input);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              </div>
              <span className="text-gray-500 text-sm ml-2 font-medium">Thinking...</span>
            </div>
          </div>
        )}
        
        {/* HIL Confirmation Dialog */}
        {pendingConfirmation && !loading && (
          <ConfirmDialog 
            description={actionDescription} 
            onConfirm={() => sendMessage('yes')} 
            onCancel={() => sendMessage('no')} 
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-100">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading || pendingConfirmation}
            placeholder={pendingConfirmation ? "Please confirm or cancel the action above..." : "Ask me about your projects or tasks..."}
            className="w-full pl-5 pr-14 py-4 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white transition-all disabled:opacity-60 disabled:cursor-not-allowed text-gray-800 placeholder-gray-400"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading || pendingConfirmation}
            className="absolute right-2 p-2.5 rounded-full text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 focus:outline-none transition-colors"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
}
