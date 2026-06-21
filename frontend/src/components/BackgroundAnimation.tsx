import React from 'react';
import { motion } from 'framer-motion';

export const BackgroundAnimation: React.FC = () => {
  return (
    <div className="fixed inset-0 z-[-1] overflow-hidden bg-gradient-to-br from-pharmacy-50 via-white to-blue-50">
      {/* Molecule/DNA inspired animated blobs */}
      <motion.div
        className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-pharmacy-200/30 blur-[100px]"
        animate={{
          scale: [1, 1.2, 1],
          x: [0, 50, 0],
          y: [0, 30, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div
        className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-200/20 blur-[120px]"
        animate={{
          scale: [1, 1.5, 1],
          x: [0, -70, 0],
          y: [0, -50, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      {/* Hexagon Pattern Grid */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 0l25.98 15v30L30 60 4.02 45V15z' fill-rule='evenodd' stroke='%230f766e' stroke-width='1' fill='none'/%3E%3C/svg%3E")`,
          backgroundSize: '60px 60px'
        }}
      />
    </div>
  );
};
