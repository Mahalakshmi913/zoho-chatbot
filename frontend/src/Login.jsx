import React from 'react';
import { Bot } from 'lucide-react';

export default function Login() {
  const handleLogin = () => {
    window.location.href = "http://localhost:8000/auth/login";
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full text-center space-y-8 bg-white p-10 rounded-2xl shadow-xl border border-gray-100">
        <div className="flex justify-center">
          <div className="bg-blue-100 p-4 rounded-full text-blue-600">
            <Bot size={48} />
          </div>
        </div>
        <div>
          <h2 className="mt-2 text-3xl font-extrabold text-gray-900 tracking-tight">
            Zoho Project Assistant
          </h2>
          <p className="mt-4 text-gray-500 text-lg">
            Chat with your Zoho projects, manage tasks, and get insights using natural language.
          </p>
        </div>
        
        <div className="pt-4">
          <button
            onClick={handleLogin}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-lg font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Login with Zoho
          </button>
        </div>
      </div>
    </div>
  );
}
