import React from 'react';
import { AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

export default function ConfirmDialog({ description, onConfirm, onCancel }) {
  return (
    <div className="flex justify-start w-full mt-2 mb-6">
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 max-w-[85%] sm:max-w-[75%] shadow-sm ml-11 relative overflow-hidden">
        {/* Top edge highlight */}
        <div className="absolute top-0 left-0 w-full h-1 bg-amber-400"></div>
        
        <div className="flex items-start gap-3 mb-4">
          <AlertCircle className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="text-amber-900 font-semibold text-[15px]">Action Required</h3>
            <p className="text-amber-800 text-sm mt-1 leading-relaxed">
              {description || "The assistant wants to perform an action on your behalf. Do you want to proceed?"}
            </p>
          </div>
        </div>
        
        <div className="flex gap-3 mt-4 ml-8">
          <button
            onClick={onConfirm}
            className="flex items-center gap-1.5 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-amber-500 shadow-sm"
          >
            <CheckCircle2 size={16} />
            Yes, proceed
          </button>
          
          <button
            onClick={onCancel}
            className="flex items-center gap-1.5 px-4 py-2 bg-white border border-amber-300 hover:bg-amber-100 text-amber-800 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-amber-500 shadow-sm"
          >
            <XCircle size={16} />
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
