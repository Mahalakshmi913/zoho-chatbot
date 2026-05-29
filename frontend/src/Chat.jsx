import React from 'react';
import { LogOut, Bot } from 'lucide-react';
import { logout } from './api';
import ChatWindow from './components/ChatWindow';

export default function Chat({ user, onLogout }) {
  const handleLogout = async () => {
    try {
      await logout();
      onLogout();
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-lg text-white">
                <Bot size={24} />
              </div>
              <h1 className="text-xl font-bold text-gray-900 hidden sm:block">Zoho Project Assistant</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 font-medium">{user.email}</span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-red-600 hover:bg-red-50 focus:outline-none transition-colors"
                title="Logout"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-hidden flex justify-center bg-gray-50">
        <div className="w-full max-w-5xl h-full flex flex-col shadow-sm border-x border-gray-200 bg-white">
          <ChatWindow />
        </div>
      </main>
    </div>
  );
}
