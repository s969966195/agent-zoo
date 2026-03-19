"use client";

import { useAnimalStore } from "@/stores/animalStore";
import { AnimalCard } from "@/components/animals/AnimalCard";
import { Sparkles } from "lucide-react";

export function AnimalsView() {
  const { animals, getFavoriteAnimals } = useAnimalStore();
  const favoriteAnimals = getFavoriteAnimals();
  const otherAnimals = animals.filter((a) => !a.isFavorite);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 bg-white border-b border-gray-100">
        <h2 className="text-lg font-bold text-gray-800">动物伙伴</h2>
        <p className="text-sm text-gray-500">认识你的动物协作伙伴</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Favorites */}
        {favoriteAnimals.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-500 mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              收藏的动物
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {favoriteAnimals.map((animal) => (
                <AnimalCard key={animal.id} animal={animal} showFavorite />
              ))}
            </div>
          </div>
        )}

        {/* All animals */}
        <div>
          <h3 className="text-sm font-semibold text-gray-500 mb-3">所有动物</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {otherAnimals.map((animal) => (
              <AnimalCard key={animal.id} animal={animal} showFavorite />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
