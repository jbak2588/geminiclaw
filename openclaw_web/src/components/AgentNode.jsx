import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { User, Cpu, CheckCircle, AlertCircle, Clock } from 'lucide-react';

const AgentNode = ({ data }) => {
  const isAgent = data.role !== 'pm' && data.role !== 'reviewer';
  
  const getStatusIcon = () => {
    switch (data.status) {
      case 'working': return <Cpu className="w-4 h-4 text-secondary animate-pulse" />;
      case 'approved': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-accent" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className={`
      group relative flex flex-col w-52 glass rounded-xl border-t-2 overflow-hidden
      ${data.status === 'working' ? 'neon-glow border-primary animate-node-glow' : 'border-gray-700'}
      transition-all duration-500 hover:scale-105 select-none
    `}>
      {/* Header with Title (Requested: Todo label) */}
      <div className="bg-white/10 px-3 py-2 flex items-center justify-between border-b border-white/10">
        <span className="text-[10px] font-bold uppercase tracking-wider text-secondary">
          {data.title || data.role}
        </span>
        {getStatusIcon()}
      </div>

      <div className="p-3 flex items-center gap-3">
        <div className={`p-2 rounded-lg ${data.status === 'working' ? 'bg-primary/20' : 'bg-white/5'}`}>
          <User className={`w-5 h-5 ${data.status === 'working' ? 'text-primary' : 'text-gray-400'}`} />
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-white/90">{data.label}</span>
          <span className="text-[10px] text-gray-400 capitalize">{data.role}</span>
        </div>
      </div>

      {/* Progress bar for 'working' status */}
      {data.status === 'working' && (
        <div className="h-1 w-full bg-white/5 relative overflow-hidden">
          <div className="absolute inset-0 bg-primary/40 animate-shimmer" 
               style={{ width: '100%' }} 
          />
        </div>
      )}

      <Handle type="target" position={Position.Left} className="!bg-secondary !w-2 !h-2 border-none" />
      <Handle type="source" position={Position.Right} className="!bg-primary !w-2 !h-2 border-none" />

      {/* Glow effect for active nodes */}
      {data.status === 'working' && (
        <div className="absolute -inset-1 bg-primary/20 blur-xl -z-10 rounded-full" />
      )}
    </div>
  );
};

export default memo(AgentNode);
