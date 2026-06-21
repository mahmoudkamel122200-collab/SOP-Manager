import React from 'react';
import { motion } from 'framer-motion';
import { 
  Pill, 
  Activity, 
  Syringe, 
  Stethoscope, 
  Microscope, 
  FlaskConical,
  Plus,
  HeartPulse
} from 'lucide-react';

const icons = [
  Pill, Activity, Syringe, Stethoscope, Microscope, FlaskConical, Plus, HeartPulse
];

export const MedicalBackground: React.FC = () => {
  // Generate a set of random floating elements
  // We use a fixed seed or hardcoded array to avoid hydration mismatches if SSR was used,
  // but since it's a Vite SPA, we can just generate them once.
  const elements = Array.from({ length: 20 }).map((_, i) => {
    const Icon = icons[i % icons.length];
    const size = Math.random() * 40 + 20; // 20px to 60px
    const startX = Math.random() * 100; // 0% to 100vw
    const startY = Math.random() * 100; // 0% to 100vh
    const duration = Math.random() * 20 + 20; // 20s to 40s
    const delay = Math.random() * 5; // 0s to 5s
    const opacity = Math.random() * 0.05 + 0.02; // very faint, 2% to 7%
    const rotation = Math.random() * 360;

    return {
      id: i,
      Icon,
      size,
      startX,
      startY,
      duration,
      delay,
      opacity,
      rotation,
    };
  });

  return (
    <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none bg-slate-50">
      {/* Optional: adding a subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-pharmacy-500/10 via-transparent to-teal-500/10" />
      
      {elements.map((el) => (
        <motion.div
          key={el.id}
          className="absolute text-pharmacy-600"
          style={{
            left: `${el.startX}vw`,
            top: `${el.startY}vh`,
            opacity: el.opacity,
          }}
          initial={{ 
            y: 0, 
            x: 0, 
            rotate: el.rotation 
          }}
          animate={{
            y: [0, -100, 0, 100, 0],
            x: [0, 50, 0, -50, 0],
            rotate: [el.rotation, el.rotation + 90, el.rotation + 180, el.rotation + 270, el.rotation + 360]
          }}
          transition={{
            duration: el.duration,
            repeat: Infinity,
            ease: "linear",
            delay: el.delay,
          }}
        >
          <el.Icon size={el.size} strokeWidth={1.5} />
        </motion.div>
      ))}
    </div>
  );
};
