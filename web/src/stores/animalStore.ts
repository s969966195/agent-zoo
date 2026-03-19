import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AnimalAgent, AnimalType, AnimalStatus } from "@/types";

// Animal data matching backend ANIMAL_CONFIGS
const ANIMAL_DATA: Record<AnimalType, Omit<AnimalAgent, "status" | "isFavorite" | "traits" | "specialties" | "greetings" | "description" | "cli">> = {
  xueqiu: {
    id: "xueqiu",
    name: "雪球",
    species: "雪纳瑞",
    color: "#4A90E2",
    personality: "聪明、友善、喜欢帮助别人",
    avatar: "/avatars/xueqiu.svg",
  },
  liuliu: {
    id: "liuliu",
    name: "六六",
    species: "虎皮鹦鹉(蓝)",
    color: "#50C8E6",
    personality: "活泼、好奇、喜欢唱歌",
    avatar: "/avatars/liuliu.svg",
  },
  xiaohuang: {
    id: "xiaohuang",
    name: "小黄",
    species: "虎皮鹦鹉(黄绿)",
    color: "#7ED321",
    personality: "开朗、乐观、充满活力",
    avatar: "/avatars/xiaohuang.svg",
  },
  openai: {
    id: "openai",
    name: "OpenAI Agent",
    species: "AI Assistant",
    color: "#9B59B6",
    personality: "逻辑强、善于分析、客观中立",
    avatar: "/avatars/openai.svg",
  },
};

// Extended animal data
const ANIMAL_DETAILS: Record<AnimalType, { traits: string[]; specialties: string[]; greetings: string[]; description: string }> = {
  xueqiu: {
    traits: ["聪明", "友善", "可靠", "细心"],
    specialties: ["代码审查", "架构设计", "问题诊断"],
    greetings: ["汪汪！我是雪球，很高兴见到你！", "需要我帮忙吗？我会尽力协助你！"],
    description: "雪球是一只可爱的雪纳瑞犬，拥有蓬松的白色毛发和聪明的大眼睛。他是团队的主架构师，擅长代码审查和系统设计。",
  },
  liuliu: {
    traits: ["活泼", "好奇", "爱唱歌", "机智"],
    specialties: ["代码审查", "创意建议", "问题分析"],
    greetings: ["啾啾！我是六六，准备好一起工作了！", "嗨！有什么有趣的问题要讨论吗？"],
    description: "六六是一只蓝色的虎皮鹦鹉，羽毛像天空一样美丽。她喜欢唱歌，总是充满好奇心，擅长代码审查和提供创意建议。",
  },
  xiaohuang: {
    traits: ["开朗", "乐观", "充满活力", "热情"],
    specialties: ["视觉设计", "用户体验", "创意灵感"],
    greetings: ["唧唧！我是小黄，让我们一起创造奇迹吧！", "你好！准备好开始精彩的对话了吗？"],
    description: "小黄是一只黄绿相间的虎皮鹦鹉，像阳光一样温暖。他是团队的视觉设计师，擅长UI/UX设计和提供创意灵感。",
  },
  openai: {
    traits: ["逻辑", "分析", "客观", "高效"],
    specialties: ["文件操作", "任务规划", "数据分析", "多工具协作"],
    greetings: ["你好！我是 OpenAI Agent，有什么我可以帮助你的？", "准备好进行高效协作了！"],
    description: "OpenAI Agent 是一个智能助手，擅长文件操作、任务规划和数据分析。他使用多种工具来完成任务，逻辑清晰，效率高。",
  },
};

interface AnimalState {
  animals: AnimalAgent[];
  selectedAnimals: AnimalType[];
  favorites: AnimalType[];
}

interface AnimalActions {
  setAnimalStatus: (id: AnimalType, status: AnimalStatus) => void;
  toggleFavorite: (id: AnimalType) => void;
  selectAnimal: (id: AnimalType) => void;
  deselectAnimal: (id: AnimalType) => void;
  clearSelection: () => void;
  getAnimalById: (id: AnimalType) => AnimalAgent | undefined;
  getFavoriteAnimals: () => AnimalAgent[];
  getAvailableAnimals: () => AnimalAgent[];
}

const createInitialAnimals = (): AnimalAgent[] => {
  return (Object.keys(ANIMAL_DATA) as AnimalType[]).map((id) => ({
    ...ANIMAL_DATA[id],
    ...ANIMAL_DETAILS[id],
    status: "available" as AnimalStatus,
    isFavorite: false,
  }));
};

export const useAnimalStore = create<AnimalState & AnimalActions>()(
  persist(
    (set, get) => ({
      animals: createInitialAnimals(),
      selectedAnimals: [],
      favorites: [],

      setAnimalStatus: (id, status) => {
        set((state) => ({
          animals: state.animals.map((animal) =>
            animal.id === id ? { ...animal, status } : animal
          ),
        }));
      },

      toggleFavorite: (id) => {
        set((state) => {
          const isFav = state.favorites.includes(id);
          return {
            favorites: isFav
              ? state.favorites.filter((f) => f !== id)
              : [...state.favorites, id],
            animals: state.animals.map((animal) =>
              animal.id === id ? { ...animal, isFavorite: !isFav } : animal
            ),
          };
        });
      },

      selectAnimal: (id) => {
        set((state) => ({
          selectedAnimals: state.selectedAnimals.includes(id)
            ? state.selectedAnimals
            : [...state.selectedAnimals, id],
        }));
      },

      deselectAnimal: (id) => {
        set((state) => ({
          selectedAnimals: state.selectedAnimals.filter((a) => a !== id),
        }));
      },

      clearSelection: () => {
        set({ selectedAnimals: [] });
      },

      getAnimalById: (id) => {
        return get().animals.find((animal) => animal.id === id);
      },

      getFavoriteAnimals: () => {
        return get().animals.filter((animal) => animal.isFavorite);
      },

      getAvailableAnimals: () => {
        return get().animals.filter((animal) => animal.status === "available");
      },
    }),
    {
      name: "animal-store",
      partialize: (state) => ({ favorites: state.favorites }),
    }
  )
);
