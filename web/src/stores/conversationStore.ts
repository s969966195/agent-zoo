import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Message, Conversation, AnimalAgent, AnimalType } from "@/types";

interface ConversationState {
  conversations: Conversation[];
  activeConversationId: string | null;
  isTyping: Record<string, boolean>; // conversationId -> isTyping
}

interface ConversationActions {
  // Conversation CRUD
  createConversation: (title: string, participants: AnimalAgent[]) => Conversation;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, newTitle: string) => void;
  toggleFavorite: (id: string) => void;
  
  // Messages
  addMessage: (conversationId: string, message: Message) => void;
  setTyping: (conversationId: string, isTyping: boolean) => void;
  
  // Session management
  setActiveConversation: (id: string | null) => void;
  endConversation: (id: string, saveToHistory?: boolean) => void;
  getConversationById: (id: string) => Conversation | undefined;
  getActiveConversation: () => Conversation | undefined;
  
  // Queries
  getConversationsByAnimal: (animalId: AnimalType) => Conversation[];
  getFavoriteConversations: () => Conversation[];
  searchConversations: (query: string) => Conversation[];
  getSortedConversations: () => Conversation[];
}

const generateId = () => Math.random().toString(36).substring(2, 15);

export const useConversationStore = create<ConversationState & ConversationActions>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeConversationId: null,
      isTyping: {},

      createConversation: (title, participants) => {
        const newConversation: Conversation = {
          id: generateId(),
          title,
          participants,
          messages: [],
          status: "active",
          createdAt: new Date(),
          updatedAt: new Date(),
          isFavorite: false,
          unreadCount: 0,
        };
        
        set((state) => ({
          conversations: [newConversation, ...state.conversations],
          activeConversationId: newConversation.id,
        }));
        
        return newConversation;
      },

      updateConversation: (id, updates) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === id ? { ...conv, ...updates, updatedAt: new Date() } : conv
          ),
        }));
      },

      deleteConversation: (id) => {
        set((state) => ({
          conversations: state.conversations.filter((conv) => conv.id !== id),
          activeConversationId: state.activeConversationId === id ? null : state.activeConversationId,
        }));
      },

      renameConversation: (id, newTitle) => {
        get().updateConversation(id, { title: newTitle });
      },

      toggleFavorite: (id) => {
        const conv = get().getConversationById(id);
        if (conv) {
          get().updateConversation(id, { isFavorite: !conv.isFavorite });
        }
      },

      addMessage: (conversationId, message) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: [...conv.messages, message],
                  updatedAt: new Date(),
                }
              : conv
          ),
        }));
      },

      setTyping: (conversationId, isTyping) => {
        set((state) => ({
          isTyping: { ...state.isTyping, [conversationId]: isTyping },
        }));
      },

      setActiveConversation: (id) => {
        set({ activeConversationId: id });
        if (id) {
          set((state) => ({
            conversations: state.conversations.map((conv) =>
              conv.id === id ? { ...conv, unreadCount: 0 } : conv
            ),
          }));
        }
      },

      endConversation: (id, saveToHistory = true) => {
        if (saveToHistory) {
          get().updateConversation(id, { status: "ended" });
        } else {
          get().deleteConversation(id);
        }
        if (get().activeConversationId === id) {
          set({ activeConversationId: null });
        }
      },

      getConversationById: (id) => {
        return get().conversations.find((conv) => conv.id === id);
      },

      getActiveConversation: () => {
        const id = get().activeConversationId;
        return id ? get().getConversationById(id) : undefined;
      },

      getConversationsByAnimal: (animalId) => {
        return get().conversations.filter((conv) =>
          conv.participants.some((p) => p.id === animalId)
        );
      },

      getFavoriteConversations: () => {
        return get().conversations.filter((conv) => conv.isFavorite);
      },

      searchConversations: (query) => {
        const lowerQuery = query.toLowerCase();
        return get().conversations.filter(
          (conv) =>
            conv.title.toLowerCase().includes(lowerQuery) ||
            conv.messages.some((m) =>
              m.content.toLowerCase().includes(lowerQuery)
            )
        );
      },

      getSortedConversations: () => {
        return [...get().conversations].sort((a, b) => {
          // Favorites first
          if (a.isFavorite !== b.isFavorite) {
            return a.isFavorite ? -1 : 1;
          }
          // Then by updated time (newest first)
          return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
        });
      },
    }),
    {
      name: "conversation-store",
    }
  )
);
