#!/usr/bin/env python3
"""
who_is_spy.py - 谁是卧底游戏

四个 Zoo Agent 互相对话玩谁是卧底。

运行方式：
    cd ~/Projects/self/zoo
    source venv/bin/activate
    python games/who_is_spy.py
"""

import os
import sys
import json
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# 配置
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
)
MODEL = os.getenv("MODEL_ID", "glm-4-flash")

# ============================================================
# 游戏配置
# ============================================================

class GamePhase(str, Enum):
    SETUP = "setup"           # 设置阶段
    DESCRIBE = "describe"     # 描述阶段
    VOTE = "vote"             # 投票阶段
    REVEAL = "reveal"         # 揭晓阶段
    END = "end"               # 结束


@dataclass
class Player:
    agent_id: str
    name: str
    role: str  # "civilian" 或 "spy"
    word: str
    description: str = ""
    votes: int = 0
    voted_for: str = ""


@dataclass
class GameRecord:
    game_id: str
    players: Dict[str, Player]
    phases: List[dict]
    winner: str = ""
    created_at: str = ""
    
    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "players": {k: asdict(v) for k, v in self.players.items()},
            "phases": self.phases,
            "winner": self.winner,
            "created_at": self.created_at,
        }


# 词库
WORD_PAIRS = [
    ("苹果", "橘子"),       # 水果
    ("猫", "狗"),           # 宠物
    ("咖啡", "奶茶"),       # 饮品
    ("微信", "QQ"),         # 社交软件
    ("篮球", "足球"),       # 运动
    ("夏天", "冬天"),       # 季节
    ("火锅", "烧烤"),       # 美食
    ("电影", "电视剧"),     # 娱乐
    ("地铁", "公交"),       # 交通
    ("手机", "电脑"),       # 电子设备
]


# Agent 人设
AGENT_PERSONALITIES = {
    "xueqiu": {
        "name": "雪球",
        "personality": "稳重务实，说话简洁直接，喜欢用具体例子说明",
        "style": "务实派",
    },
    "liuliu": {
        "name": "六六",
        "personality": "活泼机灵，喜欢开玩笑，思维跳跃",
        "style": "活泼派",
    },
    "xiaohuang": {
        "name": "小黄",
        "personality": "温和细心，善于观察，说话委婉",
        "style": "观察派",
    },
    "openai": {
        "name": "OpenAI Agent",
        "personality": "逻辑强，喜欢分析推理，说话有条理",
        "style": "分析派",
    },
}


# ============================================================
# 游戏控制器
# ============================================================

class WhoIsSpyGame:
    """谁是卧底游戏控制器"""
    
    def __init__(self):
        self.game_id = f"game-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.phase = GamePhase.SETUP
        self.players: Dict[str, Player] = {}
        self.current_round = 0
        self.descriptions: List[dict] = []
        self.votes: Dict[str, str] = {}
        self.record = GameRecord(
            game_id=self.game_id,
            players={},
            phases=[],
            created_at=datetime.now().isoformat(),
        )
    
    def setup(self, agent_ids: List[str]):
        """设置游戏"""
        # 选择词对
        civilian_word, spy_word = random.choice(WORD_PAIRS)
        
        # 随机选择卧底
        spy_id = random.choice(agent_ids)
        
        # 分配角色
        for agent_id in agent_ids:
            info = AGENT_PERSONALITIES.get(agent_id, {"name": agent_id, "personality": ""})
            is_spy = agent_id == spy_id
            self.players[agent_id] = Player(
                agent_id=agent_id,
                name=info["name"],
                role="spy" if is_spy else "civilian",
                word=spy_word if is_spy else civilian_word,
            )
        
        self.record.players = self.players
        
        # 记录设置阶段
        self.record.phases.append({
            "phase": "setup",
            "civilian_word": civilian_word,
            "spy_word": spy_word,
            "spy_id": spy_id,
        })
        
        print(f"\n🎮 游戏开始！ID: {self.game_id}")
        print(f"📝 平民词：{civilian_word}，卧底词：{spy_word}")
        print(f"🕵️ 卧底是：{self.players[spy_id].name}（玩家不可见）")
        print("-" * 50)
        
        return civilian_word, spy_word
    
    def get_player_prompt(self, agent_id: str) -> str:
        """生成玩家的系统提示"""
        player = self.players[agent_id]
        info = AGENT_PERSONALITIES.get(agent_id, {})
        
        return f"""你是"{player.name}"，正在玩"谁是卧底"游戏。

你的性格：{info.get('personality', '正常')}
你的风格：{info.get('style', '正常')}

游戏规则：
- 每个人拿到一个词语
- 平民拿到的词相同，卧底拿到的词相似但不同
- 轮流描述自己的词（不能直接说出词语）
- 最后投票选出卧底

你的词语是：「{player.word}」
你的角色是：{'卧底（要隐藏身份）' if player.role == 'spy' else '平民（要找出卧底）'}

现在轮到你描述，用1-2句话描述你的词语，不要直接说出来。
保持你的性格特点！"""
    
    def agent_describe(self, agent_id: str) -> str:
        """让 agent 进行描述"""
        player = self.players[agent_id]
        prompt = self.get_player_prompt(agent_id)
        
        # 如果有之前的描述，加入上下文
        context = ""
        if self.descriptions:
            context = "\n\n之前的描述：\n"
            for d in self.descriptions:
                context += f"- {self.players[d['agent_id']].name}：{d['content']}\n"
        
        messages = [
            {"role": "system", "content": prompt + context},
            {"role": "user", "content": "请用1-2句话描述你的词语："},
        ]
        
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=200,
            )
            description = response.choices[0].message.content.strip()
        except Exception as e:
            description = f"[描述失败: {e}]"
        
        player.description = description
        self.descriptions.append({
            "agent_id": agent_id,
            "content": description,
        })
        
        return description
    
    def get_vote_prompt(self, agent_id: str) -> str:
        """生成投票提示"""
        player = self.players[agent_id]
        info = AGENT_PERSONALITIES.get(agent_id, {})
        
        # 列出所有描述
        desc_list = "\n".join([
            f"{i+1}. {self.players[d['agent_id']].name}：{d['content']}"
            for i, d in enumerate(self.descriptions)
        ])
        
        # 列出其他玩家
        others = [p.name for aid, p in self.players.items() if aid != agent_id]
        
        return f"""你是"{player.name}"，正在投票选出卧底。

你的词语：{player.word}
你的性格：{info.get('personality', '正常')}

所有描述：
{desc_list}

请根据描述，选出你最怀疑是卧底的人。
可选：{', '.join(others)}

只回答一个人名，不要解释。"""
    
    def agent_vote(self, agent_id: str) -> str:
        """让 agent 投票"""
        prompt = self.get_vote_prompt(agent_id)
        
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
            )
            vote = response.choices[0].message.content.strip()
        except Exception as e:
            # 随机投票
            others = [aid for aid in self.players if aid != agent_id]
            vote = self.players[random.choice(others)].name
        
        # 解析投票结果
        voted_for = None
        for aid, p in self.players.items():
            if p.name in vote or aid in vote:
                voted_for = aid
                break
        
        if not voted_for:
            # 随机投一个
            others = [aid for aid in self.players if aid != agent_id]
            voted_for = random.choice(others)
        
        self.votes[agent_id] = voted_for
        self.players[voted_for].votes += 1
        
        return self.players[voted_for].name
    
    def reveal(self):
        """揭晓结果"""
        # 找出票数最多的
        max_votes = max(p.votes for p in self.players.values())
        eliminated = [p for p in self.players.values() if p.votes == max_votes]
        
        # 如果平票，随机选一个
        if len(eliminated) > 1:
            eliminated = [random.choice(eliminated)]
        
        eliminated_player = eliminated[0]
        
        # 判定胜负
        if eliminated_player.role == "spy":
            winner = "平民"
        else:
            winner = "卧底"
        
        self.record.winner = winner
        self.record.phases.append({
            "phase": "reveal",
            "eliminated": eliminated_player.name,
            "role": eliminated_player.role,
            "votes": {self.players[aid].name: p.votes for aid, p in self.players.items()},
        })
        
        print("\n" + "=" * 50)
        print("🎭 投票结果")
        print("=" * 50)
        for aid, p in self.players.items():
            print(f"  {p.name}: {p.votes} 票")
        
        print(f"\n💀 {eliminated_player.name} 被淘汰！")
        print(f"   身份：{'卧底 🕵️' if eliminated_player.role == 'spy' else '平民 👥'}")
        
        print(f"\n🏆 {winner}胜利！")
        
        # 显示所有身份
        print("\n📋 身份揭晓：")
        for aid, p in self.players.items():
            emoji = "🕵️" if p.role == "spy" else "👥"
            print(f"  {emoji} {p.name}（{p.word}）")
    
    def save_record(self):
        """保存游戏记录"""
        record_dir = Path(__file__).parent / "game_records"
        record_dir.mkdir(exist_ok=True)
        
        record_file = record_dir / f"{self.game_id}.json"
        record_file.write_text(json.dumps(self.record.to_dict(), ensure_ascii=False, indent=2))
        
        print(f"\n📝 游戏记录已保存：{record_file}")


# ============================================================
# 主流程
# ============================================================

def play_game():
    """玩一局谁是卧底"""
    game = WhoIsSpyGame()
    
    # 1. 设置
    agent_ids = ["xueqiu", "liuliu", "xiaohuang", "openai"]
    game.setup(agent_ids)
    
    # 2. 描述阶段
    print("\n📢 描述阶段")
    print("-" * 50)
    
    # 随机顺序
    order = agent_ids.copy()
    random.shuffle(order)
    
    for agent_id in order:
        player = game.players[agent_id]
        print(f"\n🎤 {player.name} 的回合")
        print(f"   你的词：{player.word}")
        
        description = game.agent_describe(agent_id)
        print(f"   描述：{description}")
    
    # 3. 投票阶段
    print("\n\n📢 投票阶段")
    print("-" * 50)
    
    for agent_id in order:
        player = game.players[agent_id]
        voted = game.agent_vote(agent_id)
        print(f"🗳️ {player.name} 投票给：{voted}")
    
    # 4. 揭晓
    game.reveal()
    
    # 5. 保存记录
    game.save_record()
    
    return game


if __name__ == "__main__":
    print("=" * 50)
    print("🎭 谁是卧底 - Zoo Agent 对战")
    print("=" * 50)
    
    game = play_game()
    
    print("\n" + "=" * 50)
    print("游戏结束！感谢参与！")
    print("=" * 50)