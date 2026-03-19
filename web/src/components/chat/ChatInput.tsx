"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Send, Smile } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { EmojiPicker } from "./EmojiPicker";
import { MentionDropdown } from "./MentionDropdown";
import { useAnimalStore } from "@/stores/animalStore";
import { useConversationStore } from "@/stores/conversationStore";
import type { AnimalAgent } from "@/types";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder = "输入消息..." }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [mentionSearch, setMentionSearch] = useState<string | null>(null);
  const [mentionPosition, setMentionPosition] = useState({ top: 0, left: 0 });
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { animals: allAnimals } = useAnimalStore();
  const { getActiveConversation } = useConversationStore();
  const activeConversation = getActiveConversation();
  const availableAnimals = activeConversation?.participants ?? allAnimals;

  const handleSend = () => {
    if (!message.trim() || disabled) return;
    onSend(message.trim());
    setMessage("");
    setMentionSearch(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === "Escape") {
      setMentionSearch(null);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setMessage(value);
    
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
    
    const cursorPos = e.target.selectionStart;
    const textBeforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    
    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(" ") && !textAfterAt.includes("\n")) {
        setMentionSearch(textAfterAt);
        
        if (textareaRef.current) {
          const textareaRect = textareaRef.current.getBoundingClientRect();
          setMentionPosition({
            top: textareaRect.top - 280,
            left: textareaRect.left + 20,
          });
        }
      } else {
        setMentionSearch(null);
      }
    } else {
      setMentionSearch(null);
    }
  };

  const handleMentionSelect = (animal: AnimalAgent) => {
    if (!textareaRef.current) return;
    
    const cursorPos = textareaRef.current.selectionStart;
    const textBeforeCursor = message.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    
    const newText = 
      message.slice(0, lastAtIndex) + 
      `@${animal.name} ` + 
      message.slice(cursorPos);
    
    setMessage(newText);
    setMentionSearch(null);
    
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className={`
        flex items-end gap-2 p-4 bg-white border-t border-gray-100
        transition-all duration-300
        ${isFocused ? "shadow-lg" : ""}
      `}
    >
      {/* Emoji button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowEmojiPicker(true)}
        className="p-2.5 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <Smile className="w-6 h-6" />
      </motion.button>

      {/* Input area */}
      <motion.div
        animate={{
          boxShadow: isFocused 
            ? "0 0 0 3px rgba(255, 107, 157, 0.2)" 
            : "0 0 0 0px rgba(255, 107, 157, 0)",
        }}
        className="flex-1 relative"
      >
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={`
            w-full px-4 py-3 rounded-cartoon-lg 
            bg-gray-50 border-2 border-transparent
            focus:bg-white focus:border-cartoon-primary
            resize-none overflow-hidden
            text-sm text-gray-800 placeholder-gray-400
            transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            focus:outline-none
          `}
          style={{ minHeight: "48px", maxHeight: "120px" }}
        />
      </motion.div>

      {/* Send button */}
      <motion.div
        whileHover={{ scale: message.trim() ? 1.05 : 1 }}
        whileTap={{ scale: message.trim() ? 0.95 : 1 }}
      >
        <Button
          variant="primary"
          size="icon"
          onClick={handleSend}
          disabled={!message.trim() || disabled}
          className="rounded-full w-12 h-12"
        >
          <Send className="w-5 h-5" />
        </Button>
      </motion.div>

      {/* Emoji Picker */}
      <EmojiPicker
        isOpen={showEmojiPicker}
        onClose={() => setShowEmojiPicker(false)}
        onSelect={(emoji) => {
          setMessage((prev) => prev + emoji);
          setShowEmojiPicker(false);
        }}
      />

      {/* Mention Dropdown */}
      {mentionSearch !== null && (
        <MentionDropdown
          animals={availableAnimals}
          filter={mentionSearch}
          position={mentionPosition}
          onSelect={handleMentionSelect}
          onClose={() => setMentionSearch(null)}
        />
      )}
    </motion.div>
  );
}
