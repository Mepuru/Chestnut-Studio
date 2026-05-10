"""卡片组件模块"""

from chestnut_studio.ui.cards.base_card import BaseCard

# 导入所有卡片模块以触发 @register_card 装饰器注册
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.cards.registry import (
    create_card,
    get_card_class,
    get_ordered_cards,
    get_registry,
    register_card,
)
from chestnut_studio.ui.cards.timeline_card import TimelineCard
from chestnut_studio.ui.cards.translate_card import TranslateCard
from chestnut_studio.ui.cards.waveform_card import WaveformCard

__all__ = [
    # 基类
    "BaseCard",
    # 注册表函数
    "register_card",
    "get_registry",
    "get_ordered_cards",
    "get_card_class",
    "create_card",
    # 卡片类
    "PlayerCard",
    "WaveformCard",
    "TimelineCard",
    "TranslateCard",
]
