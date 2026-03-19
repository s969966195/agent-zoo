"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { MessageSquare, Sparkles } from "lucide-react";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";
import { AnimalSelector } from "@/components/animals/AnimalSelector";
import { Button } from "@/components/ui/Button";
import { useConversationStore } from "@/stores/conversationStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { Message } from "@/types";

export function ChatArea() {
  const [isSelectorOpen, setIsSelectorOpen] = useState(false);
  const { getActiveConversation, addMessage, isTyping } = useConversationStore();
  const { sendMessage, isConnected } = useWebSocket();

  const conversation = getActiveConversation();

  const handleSendMessage = useCallback(
    (content: string) => {
      if (!conversation) return;

      // Add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        type: "message",
        content,
        sender: {
          id: "user",
          name: "我",
          isAnimal: false,
        },
        timestamp: new Date(),
        threadId: conversation.id,
      };

      addMessage(conversation.id, userMessage);

      // Send via WebSocket
      const animalIds = conversation.participants.map((p) => p.id);
      sendMessage(content, animalIds, conversation.id);
    },
    [conversation, addMessage, sendMessage]
  );

  // Empty state
  if (!conversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-br from-cartoon-bgLight to-white p-8">
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
          className="text-center"
        >
          <div className="w-24 h-24 mx-auto mb-6 rounded-cartoon-xl bg-gradient-to-br from-cartoon-xueqiu via-cartoon-liuliu to-cartoon-xiaohuang flex items-center justify-center shadow-cartoon-lg">
            <Sparkles className="w-12 h-12 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            欢迎来到Agent动物园
          </h2>
          <p className="text-gray-500 mb-6 max-w-md">
            与可爱的动物伙伴们一起聊天、协作，让工作变得更有趣！
          </p>
          <Button
            variant="primary"
            size="lg"
            onClick={() => setIsSelectorOpen(true)}
            className="shadow-cartoon-lg"
          >
            <MessageSquare className="w-5 h-5 mr-2" />
            开始新对话
          </Button>
        </motion.div>

        <AnimalSelector isOpen={isSelectorOpen} onClose={() => setIsSelectorOpen(false)} />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <ChatHeader
        title={conversation.title}
        participants={conversation.participants}
      />

      {/* Messages */}
      <MessageList
        messages={conversation.messages}
        isTyping={isTyping[conversation.id] || false}
        typingAnimals={conversation.participants.filter((p) => p.status === "available")}
      />

      {/* Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={!isConnected}
        placeholder={isConnected ? "输入消息..." : "连接中..."}
      />

      <AnimalSelector isOpen={isSelectorOpen} onClose={() => setIsSelectorOpen(false)} />
    </div>
  );
}
