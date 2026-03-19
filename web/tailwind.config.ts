import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // Cartoon color palette - Zootopia inspired
        cartoon: {
          // Primary colors
          primary: "#FF6B9D", // Playful pink
          secondary: "#4ECDC4", // Teal
          accent: "#FFE66D", // Sunny yellow
          
          // Animal colors
          xueqiu: "#4A90E2", // Snowball - blue
          liuliu: "#50C8E6", // Liuliu - light blue
          xiaohuang: "#7ED321", // Xiaohuang - green
          
          // Background colors
          bgLight: "#FFF9F0", // Cream
          bgDark: "#2D3436", // Dark gray
          
          // Message bubbles
          bubbleUser: "#FFE4E1", // Light pink
          bubbleAgent: "#E8F5E9", // Light green
          
          // Status colors
          available: "#00E676",
          busy: "#FFB74D",
          offline: "#9E9E9E",
          
          // Fun accents
          orange: "#FF8C42",
          purple: "#9B59B6",
          mint: "#98D8C8",
          coral: "#FF6B6B",
          sky: "#87CEEB",
        },
      },
      borderRadius: {
        // Extra rounded for cartoon feel
        cartoon: "1.5rem",
        "cartoon-lg": "2rem",
        "cartoon-xl": "2.5rem",
        "cartoon-full": "9999px",
      },
      fontFamily: {
        cartoon: ["var(--font-cartoon)", "system-ui", "sans-serif"],
      },
      animation: {
        // Cartoon animations
        "bounce-slow": "bounce 2s ease-in-out infinite",
        "wiggle": "wiggle 0.5s ease-in-out",
        "pop": "pop 0.3s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "float": "float 3s ease-in-out infinite",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        wiggle: {
          "0%, 100%": { transform: "rotate(-3deg)" },
          "50%": { transform: "rotate(3deg)" },
        },
        pop: {
          "0%": { transform: "scale(0.8)", opacity: "0" },
          "50%": { transform: "scale(1.1)" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
      boxShadow: {
        // Soft cartoon shadows
        cartoon: "0 8px 32px rgba(0, 0, 0, 0.1)",
        "cartoon-lg": "0 12px 48px rgba(0, 0, 0, 0.15)",
        "cartoon-colored": "0 8px 32px rgba(78, 205, 196, 0.2)",
      },
    },
  },
  plugins: [],
};
export default config;
