"use client";

import { motion } from "framer-motion";
import type { AnimalAgent } from "@/types";

interface AnimalAvatarProps {
  animal?: AnimalAgent;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  fallback?: "user" | "animal";
}

const sizeClasses = {
  xs: "w-6 h-6",
  sm: "w-8 h-8",
  md: "w-12 h-12",
  lg: "w-16 h-16",
  xl: "w-24 h-24",
};

// SVG Avatars for each animal
const XueqiuAvatar = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 100" className={className}>
    {/* Snowball - Schnauzer Dog */}
    <circle cx="50" cy="50" r="45" fill="#F5F5F5" />
    {/* Ears */}
    <ellipse cx="25" cy="35" rx="10" ry="15" fill="#E0E0E0" />
    <ellipse cx="75" cy="35" rx="10" ry="15" fill="#E0E0E0" />
    {/* Eyes */}
    <circle cx="38" cy="45" r="6" fill="#333" />
    <circle cx="62" cy="45" r="6" fill="#333" />
    <circle cx="40" cy="43" r="2" fill="white" />
    <circle cx="64" cy="43" r="2" fill="white" />
    {/* Nose */}
    <ellipse cx="50" cy="55" rx="8" ry="6" fill="#333" />
    {/* Mouth */}
    <path d="M45 62 Q50 68 55 62" stroke="#333" strokeWidth="2" fill="none" />
    {/* Beard */}
    <path d="M30 55 L35 70 L40 60" stroke="#999" strokeWidth="2" fill="none" />
    <path d="M70 55 L65 70 L60 60" stroke="#999" strokeWidth="2" fill="none" />
  </svg>
);

const LiuliuAvatar = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 100" className={className}>
    {/* Liuliu - Blue Budgie */}
    <circle cx="50" cy="50" r="45" fill="#50C8E6" />
    {/* Head feathers */}
    <ellipse cx="35" cy="20" rx="8" ry="12" fill="#50C8E6" />
    <ellipse cx="50" cy="15" rx="8" ry="12" fill="#50C8E6" />
    <ellipse cx="65" cy="20" rx="8" ry="12" fill="#50C8E6" />
    {/* White face patch */}
    <ellipse cx="50" cy="45" rx="25" ry="20" fill="white" />
    {/* Eyes */}
    <circle cx="40" cy="42" r="5" fill="#333" />
    <circle cx="60" cy="42" r="5" fill="#333" />
    <circle cx="41" cy="41" r="2" fill="white" />
    <circle cx="61" cy="41" r="2" fill="white" />
    {/* Beak */}
    <path d="M50 50 L45 58 L50 55 L55 58 Z" fill="#FFB74D" />
    {/* Wing patterns */}
    <path d="M20 55 Q25 70 30 65" stroke="#3BA5C7" strokeWidth="3" fill="none" />
    <path d="M80 55 Q75 70 70 65" stroke="#3BA5C7" strokeWidth="3" fill="none" />
  </svg>
);

const XiaohuangAvatar = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 100" className={className}>
    {/* Xiaohuang - Yellow-Green Budgie */}
    <circle cx="50" cy="50" r="45" fill="#7ED321" />
    {/* Head feathers */}
    <ellipse cx="35" cy="20" rx="8" ry="12" fill="#9ED849" />
    <ellipse cx="50" cy="15" rx="8" ry="12" fill="#9ED849" />
    <ellipse cx="65" cy="20" rx="8" ry="12" fill="#9ED849" />
    {/* Yellow face patch */}
    <ellipse cx="50" cy="45" rx="25" ry="20" fill="#FFE66D" />
    {/* Eyes */}
    <circle cx="40" cy="42" r="5" fill="#333" />
    <circle cx="60" cy="42" r="5" fill="#333" />
    <circle cx="41" cy="41" r="2" fill="white" />
    <circle cx="61" cy="41" r="2" fill="white" />
    {/* Beak */}
    <path d="M50 50 L45 58 L50 55 L55 58 Z" fill="#FFB74D" />
    {/* Wing patterns */}
    <path d="M20 55 Q25 70 30 65" stroke="#6BC022" strokeWidth="3" fill="none" />
    <path d="M80 55 Q75 70 70 65" stroke="#6BC022" strokeWidth="3" fill="none" />
  </svg>
);

const UserAvatar = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 100" className={className}>
    {/* User placeholder */}
    <circle cx="50" cy="50" r="45" fill="#E8E8E8" />
    {/* Head */}
    <circle cx="50" cy="38" r="18" fill="#BDBDBD" />
    {/* Body */}
    <ellipse cx="50" cy="72" rx="22" ry="18" fill="#BDBDBD" />
  </svg>
);

export function AnimalAvatar({ animal, size = "md", fallback = "animal" }: AnimalAvatarProps) {
  const sizeClass = sizeClasses[size];
  
  if (!animal) {
    return (
      <div className={`${sizeClass} rounded-full overflow-hidden bg-gray-200`}>
        <UserAvatar className="w-full h-full" />
      </div>
    );
  }

  const renderAvatar = () => {
    switch (animal.id) {
      case "xueqiu":
        return <XueqiuAvatar className="w-full h-full" />;
      case "liuliu":
        return <LiuliuAvatar className="w-full h-full" />;
      case "xiaohuang":
        return <XiaohuangAvatar className="w-full h-full" />;
      default:
        return fallback === "user" ? <UserAvatar className="w-full h-full" /> : null;
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`${sizeClass} rounded-full overflow-hidden shadow-md`}
      style={{ backgroundColor: animal.color + "20" }}
    >
      {renderAvatar()}
    </motion.div>
  );
}
