"""AstrBot Smart Translator plugin."""

from __future__ import annotations

import re
import time
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Tuple

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.message import components

# 语言别名映射 (基于 Google Translate 支持的语言)
LANG_ALIASES: Dict[str, str] = {
    # 中文
    "zh": "zh", "zh-cn": "zh", "zh-hans": "zh", "cn": "zh",
    "中": "zh", "中文": "zh", "汉语": "zh", "简体": "zh", "简中": "zh", "国语": "zh", "普通话": "zh",
    # 繁体中文
    "zh-tw": "zh-TW", "zh-hant": "zh-TW", "繁体": "zh-TW", "繁中": "zh-TW", "繁体中文": "zh-TW",
    # 英语
    "en": "en", "eng": "en", "english": "en", "英文": "en", "英": "en", "英语": "en",
    "en-gb": "en-GB", "英语（英国）": "en-GB", "英式英语": "en-GB",
    "en-us": "en", "英语（美国）": "en", "美式英语": "en",
    # 日语
    "ja": "ja", "jp": "ja", "japanese": "ja", "日文": "ja", "日语": "ja", "日": "ja",
    # 韩语
    "ko": "ko", "kr": "ko", "korean": "ko", "韩文": "ko", "韩语": "ko", "韩": "ko", "朝鲜语": "ko",
    # 俄语
    "ru": "ru", "rus": "ru", "russian": "ru", "俄文": "ru", "俄语": "ru", "俄": "ru",
    # 法语
    "fr": "fr", "fra": "fr", "french": "fr", "法语": "fr", "法文": "fr", "法": "fr",
    # 德语
    "de": "de", "ger": "de", "german": "de", "德语": "de", "德文": "de", "德": "de",
    # 西班牙语
    "es": "es", "spa": "es", "spanish": "es", "西语": "es", "西班牙语": "es", "西班牙文": "es",
    # 意大利语
    "it": "it", "ita": "it", "italian": "it", "意语": "it", "意大利语": "it", "意大利文": "it",
    # 葡萄牙语
    "pt": "pt", "por": "pt", "portuguese": "pt", "葡语": "pt", "葡萄牙语": "pt", "葡萄牙文": "pt",
    "pt-br": "pt-BR", "葡萄牙语（巴西）": "pt-BR", "巴西葡萄牙语": "pt-BR",
    "pt-pt": "pt-PT", "葡萄牙语（葡萄牙）": "pt-PT",
    # 阿拉伯语
    "ar": "ar", "ara": "ar", "arabic": "ar", "阿语": "ar", "阿拉伯语": "ar", "阿拉伯文": "ar",
    # 泰语
    "th": "th", "tha": "th", "thai": "th", "泰语": "th", "泰文": "th", "泰": "th",
    # 越南语
    "vi": "vi", "vie": "vi", "vietnamese": "vi", "越语": "vi", "越南语": "vi", "越南文": "vi",
    # 荷兰语
    "nl": "nl", "dut": "nl", "dutch": "nl", "荷语": "nl", "荷兰语": "nl", "荷兰文": "nl",
    # 波兰语
    "pl": "pl", "pol": "pl", "polish": "pl", "波兰语": "pl", "波兰文": "pl",
    # 土耳其语
    "tr": "tr", "tur": "tr", "turkish": "tr", "土耳其语": "tr", "土耳其文": "tr",
    # 瑞典语
    "sv": "sv", "swe": "sv", "swedish": "sv", "瑞典语": "sv", "瑞典文": "sv",
    # 希腊语
    "el": "el", "gre": "el", "greek": "el", "希腊语": "el", "希腊文": "el",
    # 希伯来语
    "he": "he", "iw": "he", "heb": "he", "hebrew": "he", "希伯来语": "he", "希伯来文": "he",
    # 印地语
    "hi": "hi", "hin": "hi", "hindi": "hi", "印地语": "hi", "印度语": "hi",
    # 印尼语
    "id": "id", "ind": "id", "indonesian": "id", "印尼语": "id", "印尼文": "id", "印度尼西亚语": "id",
    # 马来语
    "ms": "ms", "may": "ms", "malay": "ms", "马来语": "ms", "马来文": "ms",
    # 拉丁语
    "la": "la", "lat": "la", "latin": "la", "拉丁语": "la", "拉丁文": "la",
    # 乌克兰语
    "uk": "uk", "ukr": "uk", "ukrainian": "uk", "乌克兰语": "uk", "乌克兰文": "uk",
    # 捷克语
    "cs": "cs", "cze": "cs", "czech": "cs", "捷克语": "cs", "捷克文": "cs",
    # 罗马尼亚语
    "ro": "ro", "rum": "ro", "romanian": "ro", "罗马尼亚语": "ro", "罗马尼亚文": "ro",
    # 匈牙利语
    "hu": "hu", "hun": "hu", "hungarian": "hu", "匈牙利语": "hu", "匈牙利文": "hu",
    # 芬兰语
    "fi": "fi", "fin": "fi", "finnish": "fi", "芬兰语": "fi", "芬兰文": "fi",
    # 丹麦语
    "da": "da", "dan": "da", "danish": "da", "丹麦语": "da", "丹麦文": "da",
    # 挪威语
    "no": "no", "nor": "no", "norwegian": "no", "挪威语": "no", "挪威文": "no",
    # 阿姆哈拉语
    "am": "am", "amh": "am", "amharic": "am", "阿姆哈拉语": "am",
    # 巴斯克语
    "eu": "eu", "eus": "eu", "basque": "eu", "巴斯克语": "eu",
    # 孟加拉语
    "bn": "bn", "ben": "bn", "bengali": "bn", "孟加拉语": "bn", "孟加拉文": "bn",
    # 保加利亚语
    "bg": "bg", "bul": "bg", "bulgarian": "bg", "保加利亚语": "bg", "保加利亚文": "bg",
    # 加泰罗尼亚语
    "ca": "ca", "cat": "ca", "catalan": "ca", "加泰罗尼亚语": "ca",
    # 切罗基语
    "chr": "chr", "cherokee": "chr", "切罗基语": "chr",
    # 克罗地亚语
    "hr": "hr", "hrv": "hr", "croatian": "hr", "克罗地亚语": "hr", "克罗地亚文": "hr",
    # 爱沙尼亚语
    "et": "et", "est": "et", "estonian": "et", "爱沙尼亚语": "et", "爱沙尼亚文": "et",
    # 菲律宾语
    "fil": "fil", "tl": "fil", "filipino": "fil", "tagalog": "fil", "菲律宾语": "fil",
    # 古吉拉特语
    "gu": "gu", "guj": "gu", "gujarati": "gu", "古吉拉特语": "gu",
    # 冰岛语
    "is": "is", "isl": "is", "icelandic": "is", "冰岛语": "is", "冰岛文": "is",
    # 卡纳达语
    "kn": "kn", "kan": "kn", "kannada": "kn", "卡纳达语": "kn",
    # 拉脱维亚语
    "lv": "lv", "lav": "lv", "latvian": "lv", "拉脱维亚语": "lv", "拉脱维亚文": "lv",
    # 立陶宛语
    "lt": "lt", "lit": "lt", "lithuanian": "lt", "立陶宛语": "lt", "立陶宛文": "lt",
    # 马拉雅拉姆语
    "ml": "ml", "mal": "ml", "malayalam": "ml", "马拉雅拉姆语": "ml",
    # 马拉地语
    "mr": "mr", "mar": "mr", "marathi": "mr", "马拉地语": "mr",
    # 塞尔维亚语
    "sr": "sr", "srp": "sr", "serbian": "sr", "塞尔维亚语": "sr", "塞尔维亚文": "sr",
    # 斯洛伐克语
    "sk": "sk", "slk": "sk", "slovak": "sk", "斯洛伐克语": "sk", "斯洛伐克文": "sk",
    # 斯洛文尼亚语
    "sl": "sl", "slv": "sl", "slovenian": "sl", "斯洛文尼亚语": "sl", "斯洛文尼亚文": "sl",
    # 斯瓦希里语
    "sw": "sw", "swa": "sw", "swahili": "sw", "斯瓦希里语": "sw",
    # 泰米尔语
    "ta": "ta", "tam": "ta", "tamil": "ta", "泰米尔语": "ta",
    # 泰卢固语
    "te": "te", "tel": "te", "telugu": "te", "泰卢固语": "te",
    # 乌尔都语
    "ur": "ur", "urd": "ur", "urdu": "ur", "乌尔都语": "ur",
    # 威尔士语
    "cy": "cy", "cym": "cy", "welsh": "cy", "威尔士语": "cy", "威尔士文": "cy",
    # 自动检测
    "auto": "auto",
}

# 匹配: "翻译成日语: xxx", "译成英文: xxx"
TRANSLATE_TO_LANG_RE = re.compile(
    r"^(?:把|将|请|帮我|帮忙)?(?:翻译|译)(?:成|为|到)(?P<lang>[A-Za-z]{2,}|[\u4e00-\u9fff]{1,4})(?:文|语)?[:：\s]+(?P<text>.+)$",
    flags=re.DOTALL,
)
# 匹配: "日语: xxx", "英文：xxx" (语言前缀格式)
LANG_PREFIX_RE = re.compile(
    r"^(?P<lang>[A-Za-z]{2,}|[\u4e00-\u9fff]{1,4})(?:文|语)[:：]\s*(?P<text>.+)$",
    flags=re.DOTALL,
)
# 匹配: "xxx 翻译成日语", "xxx译成英文"
TEXT_THEN_TRANSLATE_RE = re.compile(
    r"^(?P<text>.+?)\s*(?:翻译|译)(?:成|为|到)(?P<lang>[A-Za-z]{2,}|[\u4e00-\u9fff]{1,4})(?:文|语)?[。？?!！]?$",
    flags=re.DOTALL,
)
# 回复消息触发（用于引用消息的二次翻译）
REPLY_TRIGGER_RE = re.compile(r"(再翻译|翻译|翻成|译一下|译成|translate)", flags=re.IGNORECASE)

DEFAULT_SYSTEM_PROMPT = (
    "You are a translation engine. "
    "Translate the user text into the target language. "
    "Output ONLY the translated text. "
    "No explanations, no notes, no links, no formatting."
)

CONFIG_DEFAULTS: Dict[str, Any] = {
    "api_settings": {
        "provider_id": "",
        "provider_is_local": False,
    },
    "interaction_settings": {
        "default_target_lang": "zh",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
    },
    "formatter_settings": {
        "output_mode": "tagged",
    },
    "logging_settings": {
        "show_api_exchange": False,
    },
}

# 缓存配置常量
CACHE_MAX_SIZE = 100  # 最大缓存条目数（LRU 淘汰）


class LRUCache:
    """简单的 LRU 缓存实现，带 TTL 支持."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 900):
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl_seconds:
            del self._cache[key]
            return None
        # 移动到末尾（最近使用）
        self._cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            del self._cache[key]
        self._cache[key] = (value, time.time())
        # 超出容量时移除最旧的
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def set_ttl(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds

    def cleanup_expired(self) -> int:
        """清理所有过期条目，返回清理数量."""
        now = time.time()
        expired_keys = [
            k for k, (_, ts) in self._cache.items()
            if now - ts > self._ttl_seconds
        ]
        for k in expired_keys:
            del self._cache[k]
        return len(expired_keys)


def _preview(text: str, limit: int = 80) -> str:
    sanitized = text.replace("\n", " ").strip()
    return sanitized[:limit] + ("…" if len(sanitized) > limit else "")


def _clean_str(value: Any) -> str:
    return str(value).strip() if value else ""


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value) if isinstance(value, (int, float)) else False


def _normalize_lang(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return LANG_ALIASES.get(token.lower())


def _detect_language(text: str) -> str:
    """基于字符集统计检测文本主要语言（单次遍历）."""
    if not text:
        return "auto"

    counts = {"zh": 0, "ja": 0, "ko": 0, "ru": 0, "en": 0}
    for char in text:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF:
            counts["zh"] += 1
        elif 0x3040 <= code <= 0x30FF:
            counts["ja"] += 1
        elif 0xAC00 <= code <= 0xD7AF:
            counts["ko"] += 1
        elif 0x0400 <= code <= 0x04FF:
            counts["ru"] += 1
        elif (0x0041 <= code <= 0x005A) or (0x0061 <= code <= 0x007A):
            counts["en"] += 1

    lang, count = max(counts.items(), key=lambda x: x[1])
    return lang if count > 0 else "auto"


# 预编译清理译文用的正则表达式
_CLEAN_PATTERNS = [
    re.compile(r"^(?:翻译[：:]\s*)", re.IGNORECASE),
    re.compile(r"^(?:译文[：:]\s*)", re.IGNORECASE),
    re.compile(r"^(?:Translation[：:]?\s*)", re.IGNORECASE),
    re.compile(r"^(?:Here(?:'s| is) the translation[：:]?\s*)", re.IGNORECASE),
]
_URL_PATTERN = re.compile(r"https?://[^\s\]\)]+")
_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_CITATION_PATTERN = re.compile(r"\[\d+\]")
_MULTI_NEWLINE_PATTERN = re.compile(r"\n{2,}")


def _clean_translation(text: str) -> str:
    """清理 LLM 返回的译文."""
    if not text:
        return ""
    result = text.strip()

    for pattern in _CLEAN_PATTERNS:
        result = pattern.sub("", result).strip()

    result = _URL_PATTERN.sub("", result).strip()
    result = _MARKDOWN_LINK_PATTERN.sub(r"\1", result)
    result = _CITATION_PATTERN.sub("", result).strip()
    result = _MULTI_NEWLINE_PATTERN.sub("\n", result)

    return result.strip()


@dataclass
class TranslationRequest:
    source_text: Optional[str] = None
    target_lang: Optional[str] = None
    source_lang: Optional[str] = None


class TranslationBackendError(RuntimeError):
    pass


class SmartTranslator(Star):
    """基于 LLM 的自然语言翻译插件."""

    def __init__(self, context: Context, config: Optional[Dict[str, Any]] = None):
        super().__init__(context)
        self.config: Dict[str, Any] = config or {}
        self.provider_id: str = ""
        self.fallback_provider_id: str = ""
        self.provider_is_local: bool = False
        self.default_target_lang: str = "zh"
        self.system_prompt: str = DEFAULT_SYSTEM_PROMPT
        self.output_mode: Literal["plain", "tagged", "bilingual"] = "tagged"
        self.show_api_exchange: bool = False
        self.cache_ttl_minutes: int = 15
        # LRU 缓存，带容量限制和 TTL
        self._translation_cache = LRUCache(max_size=CACHE_MAX_SIZE, ttl_seconds=15 * 60)

    async def initialize(self):
        self._load_config()
        logger.info("SmartTranslator 已加载")

    async def terminate(self):
        logger.info("SmartTranslator 已卸载")

    def _load_config(self) -> None:
        merged = deepcopy(CONFIG_DEFAULTS)
        if self.config:
            for section, values in self.config.items():
                if isinstance(values, dict) and section in merged:
                    merged[section].update(values)
                else:
                    merged[section] = values

        api = merged.get("api_settings", {})
        self.provider_id = _clean_str(api.get("provider_id"))
        self.fallback_provider_id = _clean_str(api.get("fallback_provider_id"))
        self.provider_is_local = _to_bool(api.get("provider_is_local"))

        interaction = merged.get("interaction_settings", {})
        self.default_target_lang = _clean_str(interaction.get("default_target_lang")) or "zh"
        self.system_prompt = _clean_str(interaction.get("system_prompt")) or DEFAULT_SYSTEM_PROMPT
        try:
            self.cache_ttl_minutes = int(_clean_str(interaction.get("cache_ttl_minutes")) or "15")
        except ValueError:
            self.cache_ttl_minutes = 15

        # 更新缓存 TTL
        self._translation_cache.set_ttl(self.cache_ttl_minutes * 60)

        formatter = merged.get("formatter_settings", {})
        mode = _clean_str(formatter.get("output_mode"))
        self.output_mode = mode if mode in ("plain", "tagged", "bilingual") else "tagged"

        log_settings = merged.get("logging_settings", {})
        self.show_api_exchange = _to_bool(log_settings.get("show_api_exchange"))

        logger.info(
            "SmartTranslator 配置: provider_id=%s output_mode=%s default_target=%s cache_ttl=%dm",
            self.provider_id or "<default>",
            self.output_mode,
            self.default_target_lang,
            self.cache_ttl_minutes,
        )

        # 检查 fallback 配置
        if self.provider_id and not self.fallback_provider_id:
            logger.warning(
                "未配置 fallback_provider_id，当主 provider (%s) 不可用时将无法自动切换",
                self.provider_id,
            )

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """消息处理入口 - 在消息阶段拦截翻译请求."""
        request = self._parse_request(event)
        if not request:
            return  # 不触发翻译，让消息继续传递

        # 检查是否是二次翻译失败的情况
        if not request.source_text:
            event.stop_event()
            yield event.plain_result("⚠️ 翻译失败：未获取到原文")
            return

        # 匹配到翻译请求，拦截消息
        event.stop_event()

        source_lang = request.source_lang or "auto"
        target_lang = request.target_lang or self.default_target_lang

        logger.info(
            "翻译请求: %s -> %s, 文本: %s",
            source_lang, target_lang, _preview(request.source_text)
        )

        try:
            translation, status_note = await self._do_translate(
                text=request.source_text,
                target_lang=target_lang,
                source_lang=source_lang,
            )
        except TranslationBackendError as exc:
            yield event.plain_result(f"翻译失败: {exc}")
            return
        except Exception as exc:
            logger.exception("翻译异常: %s", exc)
            yield event.plain_result("翻译失败，请稍后重试。")
            return

        # 缓存原文，用于后续二次翻译
        cache_key = self._get_cache_key(event)
        if cache_key:
            self._translation_cache.set(cache_key, request.source_text)
            logger.debug("缓存原文: %s", _preview(request.source_text, 50))

        # 格式化输出，status_note 在最前面
        output = self._format_output(translation, source_lang, target_lang, request.source_text)
        if status_note:
            output = f"{status_note}\n{output}"
        yield event.plain_result(output)

    def _get_cache_key(self, event: AstrMessageEvent) -> Optional[str]:
        """获取缓存键."""
        try:
            message_id = event.message_obj.message_id
            if message_id:
                return str(message_id)
            #
            # # 尝试从 event 获取唯一标识
            # unified_id = getattr(event, "unified_msg_origin", None)
            # if unified_id:
            #     return str(unified_id)
            #
            # session_id = getattr(event, "session_id", None)
            # if session_id:
            #     return str(session_id)
            #
            # # 从 message_obj 获取 user_id
            # msg_obj = getattr(event, "message_obj", None)
            # if msg_obj:
            #     sender = getattr(msg_obj, "sender", None)
            #     if sender:
            #         user_id = getattr(sender, "user_id", None) or getattr(sender, "id", None)
            #         if user_id:
            #             return f"user:{user_id}"
        except Exception:
            pass
        return None

    def _get_cached_source(self, event: AstrMessageEvent) -> Optional[str]:
        """获取缓存的原文（用于二次翻译）."""
        cache_key = self._get_cache_key(event)
        if not cache_key:
            return None

        source_text = self._translation_cache.get(cache_key)
        if source_text:
            logger.debug("使用缓存原文进行二次翻译: %s", _preview(source_text, 50))
        return source_text

    def _parse_request(self, event: AstrMessageEvent) -> Optional[TranslationRequest]:
        """解析翻译请求."""
        raw = (event.message_str or "").strip()
        if not raw:
            return None

        quote_message = self._get_reply_message(event)

        # 1. 引用消息 + 翻译触发词 -> 翻译引文
        if quote_message:
            # 从消息段中提取纯文本（排除引用部分）
            trailing_text = self._get_text_from_message_chain(event) or self._get_trailing_text(raw)
            logger.debug("引用消息后续文本: %s", trailing_text)

            if trailing_text:
                trigger_match = REPLY_TRIGGER_RE.search(trailing_text)
                if trigger_match:
                    target = self._extract_target_from_trigger(trailing_text)
                    logger.debug("引文翻译触发: 目标语言=%s", target)

                    if not target:
                        # 没有指定目标语言，使用默认目标语言
                        target = self.default_target_lang
                        logger.debug("[引用消息] 使用默认目标语言: %s", target)

                    # 从缓存获取首次翻译的原文
                    quote_message_id = self._get_reply_message_id(quote_message)
                    if quote_message_id:
                        cached_source = self._translation_cache.get(str(quote_message_id))
                        if cached_source:
                            return TranslationRequest(
                                source_text=cached_source,
                                target_lang=target,
                                source_lang=_detect_language(cached_source),
                            )

                    # 缓存过期或不存在，直接翻译引文
                    logger.debug("[引用消息] 缓存未命中或已过期")
                    quote_message_str = self._get_reply_message_str(quote_message)
                    if quote_message_str:
                        return TranslationRequest(
                            source_text=quote_message_str,
                            target_lang=target,
                            source_lang=_detect_language(quote_message_str)
                        )

            # 引用消息但没有翻译触发词，不处理
            logger.debug("[引用消息] 无翻译触发词，跳过")
            return None

        # 以下正则只处理非引用消息
        # 2. "翻译成日语: xxx" 格式
        match = TRANSLATE_TO_LANG_RE.match(raw)
        if match:
            target = _normalize_lang(match.group("lang"))
            if target:  # 必须识别出有效语言
                source = match.group("text").strip()
                return TranslationRequest(
                    source_text=source,
                    target_lang=target,
                    source_lang=_detect_language(source),
                )

        # 3. "日语: xxx" 格式 (语言前缀)
        match = LANG_PREFIX_RE.match(raw)
        if match:
            target = _normalize_lang(match.group("lang"))
            if target:
                source = match.group("text").strip()
                return TranslationRequest(
                    source_text=source,
                    target_lang=target,
                    source_lang=_detect_language(source),
                )

        # 4. "xxx 翻译成日语" 格式
        match = TEXT_THEN_TRANSLATE_RE.match(raw)
        if match:
            target = _normalize_lang(match.group("lang"))
            if target:
                source = match.group("text").strip()
                return TranslationRequest(
                    source_text=source,
                    target_lang=target,
                    source_lang=_detect_language(source),
                )

        return None

    def _extract_target_from_trigger(self, text: str) -> Optional[str]:
        """从触发文本中提取目标语言.
        
        支持格式：
        - "翻译成日语" / "译成英文"
        - "再翻译成德语"
        - "翻成法语"
        """
        # 匹配 "再翻译成X" / "翻译成X" / "译成X" / "翻成X"
        match = re.search(
            r"(?:再)?(?:翻译|翻|译)(?:成|为|到)([A-Za-z]{2,}|[\u4e00-\u9fff]{1,4})(?:文|语)?",
            text,
        )
        if match:
            lang = _normalize_lang(match.group(1))
            logger.debug("提取目标语言: '%s' -> %s", match.group(1), lang)
            return lang
        return None

    def _get_reply_message(self, event: AstrMessageEvent) -> components.BaseMessageComponent | None:
        """
        获取引用的消息
        """
        msgs = event.message_obj.message
        if msgs[0] and msgs[0].type == components.ComponentType.Reply:
            return msgs[0]
        return None

    def _get_reply_message_id(self, msg_comp: components.BaseMessageComponent) -> int | None:
        if msg_comp:
            return getattr(msg_comp, "id", None)
        return None

    def _get_reply_message_str(self, msg_comp: components.BaseMessageComponent) -> str | None:
        if msg_comp:
            return getattr(msg_comp, "message_str", None)
        return None

    def _get_trailing_text(self, msg_str: str) -> Optional[str]:
        """提取引用消息后的后续文本.
        
        支持格式：
        - "[引用消息(昵称: 内容)] 后续文本" -> "后续文本"
        - "[CQ:reply,id=xxx]后续文本" -> "后续文本"
        """
        # 1. 尝试 AstrBot 标准格式: "[引用消息(...)] 后续文本"
        last_bracket_space = msg_str.rfind(")] ")
        if last_bracket_space != -1:
            trailing = msg_str[last_bracket_space + 3:].strip()
            if trailing:
                return trailing

        # 2. 尝试 CQHTTP 格式: "[CQ:reply,id=xxx]后续文本"
        cq_match = re.search(r"\[CQ:reply,[^\]]*\](.+)$", msg_str)
        if cq_match:
            trailing = cq_match.group(1).strip()
            if trailing:
                return trailing

        return None

    def _get_text_from_message_chain(self, event: AstrMessageEvent) -> Optional[str]:
        """从消息链中提取纯文本内容（排除引用/回复段）.
        
        这是更可靠的方法，直接从消息段中读取 text/Plain 类型的内容。
        """
        try:
            msg_obj = getattr(event, "message_obj", None)
            if not msg_obj:
                return None

            message_chain = getattr(msg_obj, "message", None) or getattr(msg_obj, "message_chain", None)
            if not message_chain:
                return None

            text_parts = []
            for seg in message_chain:
                # 获取段类型 - 可能是字符串、枚举或其他类型
                if isinstance(seg, dict):
                    seg_type = seg.get("type", "")
                    seg_data = seg.get("data", {})
                else:
                    seg_type = getattr(seg, "type", "")
                    seg_data = getattr(seg, "data", {}) or {}

                # 将类型转换为字符串进行比较（处理枚举类型）
                seg_type_str = str(seg_type).lower()

                # 匹配 text/plain 类型的消息段
                is_text_type = any(t in seg_type_str for t in ("text", "plain"))

                if is_text_type:
                    # 尝试多种方式获取文本内容
                    text_content = None

                    # 方式1: 从 data 字典获取
                    if isinstance(seg_data, dict):
                        text_content = seg_data.get("text", "")

                    # 方式2: 从 seg.text 属性获取
                    if not text_content and hasattr(seg, "text"):
                        text_content = getattr(seg, "text", "")

                    # 方式3: 从 seg.data.text 获取（如果 data 是对象）
                    if not text_content and hasattr(seg_data, "text"):
                        text_content = getattr(seg_data, "text", "")

                    if text_content:
                        text_parts.append(str(text_content))
                        logger.debug("[消息链] 从 %s 段提取文本: %s", seg_type_str, text_content[:50])

            if text_parts:
                result = "".join(text_parts).strip()
                logger.debug("从消息链提取纯文本: %s", result)
                return result if result else None
        except Exception as e:
            logger.debug("消息链提取失败: %s", e)

        return None

    async def _do_translate(
            self,
            text: str,
            target_lang: str,
            source_lang: str,
    ) -> Tuple[str, Optional[str]]:
        """执行翻译."""
        prompt = self._build_prompt(text, target_lang, source_lang)
        status_note = None

        if self.show_api_exchange:
            logger.info("翻译请求 => provider=%s, prompt=%s", self.provider_id or "<default>", _preview(prompt))

        try:
            kwargs: Dict[str, Any] = {
                "prompt": prompt,
                "system_prompt": self.system_prompt,
            }
            if self.provider_id:
                kwargs["chat_provider_id"] = self.provider_id

            resp = await self.context.llm_generate(**kwargs)
            translation = self._extract_llm_translation_output(resp)

            if self.show_api_exchange:
                logger.info("翻译响应 <= %s", _preview(translation or "<empty>"))

            if not translation:
                raise TranslationBackendError("LLM 返回为空")

            translation = _clean_translation(translation)

            if self.provider_is_local:
                status_note = "[本地LLM翻译]"

            return translation, status_note

        except Exception as exc:
            if self.provider_id and not self.provider_is_local:
                logger.warning("Provider %s 失败: %s, 尝试回退", self.provider_id, exc)
                # 尝试获取默认 provider 进行回退
                fallback_provider = self._get_fallback_provider()
                if fallback_provider:
                    try:
                        resp = await self.context.llm_generate(
                            prompt=prompt,
                            system_prompt=self.system_prompt,
                            chat_provider_id=fallback_provider,
                        )
                        translation = self._extract_llm_translation_output(resp)
                        if translation:
                            translation = _clean_translation(translation)
                            return translation, f"[主翻译失败，采用备用: {fallback_provider}]"
                    except Exception as fallback_exc:
                        logger.error("回退翻译也失败: %s", fallback_exc)
                else:
                    logger.error(
                        "主 provider (%s) 请求失败，且未配置 fallback_provider_id，无法切换备用",
                        self.provider_id,
                    )
                    raise TranslationBackendError(
                        f"主翻译失败且未配置备用 provider，请在插件设置中配置 fallback_provider_id"
                    ) from exc
            raise TranslationBackendError(str(exc)) from exc

    def _get_fallback_provider(self) -> Optional[str]:
        """获取回退用的 provider ID，由用户在配置中指定。"""
        if self.fallback_provider_id:
            logger.info("使用配置的回退 provider: %s", self.fallback_provider_id)
            return self.fallback_provider_id
        return None

    def _build_prompt(self, text: str, target_lang: str, source_lang: str) -> str:
        if source_lang and source_lang != "auto":
            instruction = f"Translate from {source_lang} to {target_lang}:"
        else:
            instruction = f"Translate to {target_lang}:"
        return f"{instruction}\n\n{text.strip()}"

    def _extract_llm_translation_output(self, resp: Any) -> str:
        if resp is None:
            return ""
        if isinstance(resp, str):
            return resp.strip()

        # 先尝试从 raw_completion 中提取（更可靠）
        raw = getattr(resp, "raw_completion", None)
        if raw:
            choices = getattr(raw, "choices", None) or (raw.get("choices") if isinstance(raw, dict) else None)
            if choices and len(choices) > 0:
                first = choices[0]
                msg = getattr(first, "message", None) or (first.get("message") if isinstance(first, dict) else None)
                if msg:
                    content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
                    if content:
                        return str(content).strip()

        # 尝试从 result_chain 提取
        chain = getattr(resp, "result_chain", None)
        if chain:
            parts = []
            chain_list = getattr(chain, "chain", chain)
            if isinstance(chain_list, (list, tuple)):
                for comp in chain_list:
                    text = getattr(comp, "text", None)
                    if text:
                        parts.append(str(text))
            if parts:
                return " ".join(parts).strip()

        # 尝试其他属性
        for attr in ("output_text", "text", "content", "response"):
            value = getattr(resp, attr, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        # 最后尝试 - 不要返回整个对象的字符串表示
        return ""

    def _format_output(
            self, translation: str, source_lang: str, target_lang: str, source_text: str = ""
    ) -> str:
        if self.output_mode == "plain":
            return translation
        if self.output_mode == "bilingual":
            # 原文/译文对照格式
            return f"原文：{source_text}\n译文：{translation}"
        if source_lang and source_lang != "auto":
            return f"[{source_lang}->{target_lang}] {translation}"
        return f"[->{target_lang}] {translation}"
