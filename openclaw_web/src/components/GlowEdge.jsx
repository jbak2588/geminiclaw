import React from 'react';
import { getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

const GlowEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  animated,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      {/* Base Path with Glow Filter */}
      <path
        id={id}
        style={{
          ...style,
          strokeWidth: 3,
          stroke: 'rgba(139, 92, 246, 0.2)', // Dim primary
          filter: 'blur(2px)',
        }}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />
      
      {/* Target Path (Visible Line) */}
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={{ stroke: 'rgba(139, 92, 246, 0.4)', strokeWidth: 1.5 }} />

      {/* Animated Particle (Glowing Dot) */}
      {animated && (
        <circle r="4" fill="#22D3EE" filter="drop-shadow(0 0 5px #22D3EE)">
          <animateMotion
            dur="2s"
            repeatCount="indefinite"
            path={edgePath}
          />
          {/* Secondary smaller particle with delay */}
          <animate
            attributeName="opacity"
            values="0;1;1;0"
            dur="2s"
            repeatCount="indefinite"
          />
        </circle>
      )}

      {/* Trailing Particle (Bliking effect) */}
      {animated && (
        <circle r="2" fill="#8B5CF6" filter="drop-shadow(0 0 3px #8B5CF6)">
          <animateMotion
            dur="2s"
            begin="0.5s"
            repeatCount="indefinite"
            path={edgePath}
          />
          <animate
            attributeName="r"
            values="1;4;1"
            dur="1s"
            repeatCount="indefinite"
          />
        </circle>
      )}
    </>
  );
};

export default GlowEdge;
