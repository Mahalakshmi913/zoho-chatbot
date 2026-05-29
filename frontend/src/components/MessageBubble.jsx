import React from 'react';
import { Bot, User } from 'lucide-react';

export default function MessageBubble({ role, content }) {
  const isBot = role === 'assistant';
  
  // Basic markdown-like link parsing could be added here if needed
  // For now, we'll just handle basic text formatting

  return (
    <div className={`flex w-full ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div className={`flex max-w-[85%] sm:max-w-[75%] ${isBot ? 'flex-row' : 'flex-row-reverse'} gap-3 items-end`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isBot ? 'bg-blue-100 text-blue-600' : 'bg-gray-800 text-white'
        }`}>
          {isBot ? <Bot size={18} /> : <User size={18} />}
        </div>
        
        {/* Bubble */}
        <div className={`px-5 py-4 text-[15px] leading-relaxed shadow-sm ${
          isBot 
            ? 'bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-bl-sm' 
            : 'bg-blue-600 text-white rounded-2xl rounded-br-sm'
        }`}>
          <div className="whitespace-pre-wrap break-words">{content}</div>
        </div>
        
      </div>
    </div>
  );
}
