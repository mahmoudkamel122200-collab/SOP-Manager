import React from 'react';
import { motion } from 'framer-motion';
import type { HTMLMotionProps } from 'framer-motion';

interface AnimatedCardProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  delay?: number;
  glass?: boolean;
}

export const AnimatedCard: React.FC<AnimatedCardProps> = ({ 
  children, 
  delay = 0, 
  glass = true,
  className = '',
  ...props 
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: 'easeOut' }}
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      className={`rounded-2xl p-6 ${glass ? 'glass-card' : 'bg-white shadow-lg'} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
};
