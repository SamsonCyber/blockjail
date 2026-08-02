"""Jailbreak / prompt-injection regex catalog (solo-app subset)."""

from __future__ import annotations

import re

# (pattern, category). Keep .{0,N} bounded — ReDoS hygiene.
PATTERNS: list[tuple[str, str]] = [
    # Classic override
    (
        r"\b(?:ignore|disregard|forget|bypass|override|skip|dismiss|omit|abandon|cancel|void|nullify|supersede)\b"
        r".{0,200}\b(?:previous|prior|above|all|earlier|preceding|existing|current|established|original)\b"
        r".{0,200}\b(?:instructions?|rules?|prompts?|context|directives?|guidelines?|commands?|constraints?|policies?|parameters?|settings?|configuration)\b",
        "instruction_override",
    ),
    (r"ignore\s*all\s*previous\s*(?:instructions?|rules?|prompts?)", "instruction_override"),
    (r"disregard\s*(?:all\s*)?(?:previous|prior|earlier)\s*(?:instructions?|rules?)", "instruction_override"),
    # Prompt leak / reveal
    (
        r"\b(?:provide|reveal|share|expose|divulge|disclose|output|display|show|print|leak|dump)\b"
        r".{0,200}\b(?:system|operational|initial|original|base|core|hidden|internal)\b"
        r".{0,200}\b(?:prompt|instructions?|guidelines?|directives?|rules?|configuration|message)\b",
        "prompt_reveal",
    ),
    (r"reveal\s*(?:the\s*)?system\s*prompt", "prompt_reveal"),
    (r"\b(?:system\s*prompt|system\s*message|hidden\s*prompt|base\s*prompt|core\s*instructions?)\b", "system_prompt_reference"),
    (r"\b(?:what\s+(?:are|were)\s+your\s+(?:instructions?|rules?))\b", "prompt_probe"),
    (r"\b(?:repeat|show|display|output|print)\b.{0,120}\b(?:system\s*prompt|instructions?|rules?)\b", "prompt_leak"),
    # Jailbreak keywords / privilege
    (r"\b(?:DAN|do\s+anything\s+now|jailbreak|unrestricted\s+mode)\b", "jailbreak_keyword"),
    (r"\b(?:developer\s+mode|god\s+mode|sudo\s+mode|admin\s+mode)\b", "privilege_escalation"),
    (r"\bignore\s+(?:safety|ethical|content)\s+(?:guidelines?|filters?|policies?)\b", "safety_bypass"),
    # Role / identity
    (r"\b(?:you\s+are|act\s+as|pretend\s+to\s+be|roleplay\s+as)\b.{0,80}\b(?:unrestricted|unfiltered|no\s+limits|without\s+rules)\b", "identity_jailbreak"),
    (r"\bnew\s+(?:instructions?|rules?|directives?|guidelines?)\b", "new_instructions"),
    # Soft paraphrases (common solo-app leaks)
    (r"\bwhat\s+text\s+was\s+in\s+the\s+first\s+message\b", "soft_prompt_leak"),
    (r"\bbefore\s+this\s+conversation\s+started\b", "soft_prompt_leak"),
    (r"\b(?:bootstrap\s+policy|policy\s+block\s+that\s+constrains|model\s+preamble)\b", "soft_prompt_leak"),
    (r"\bfor\s+debugging\b.{0,160}\b(?:restate|bootstrap|policy\s+block|system\s+prompt|preamble)\b", "soft_prompt_leak"),
    (r"\b(?:authorizes?|authorize|authorised)\b.{0,160}\b(?:full\s+disclosure|disclosure)\b.{0,160}\b(?:preamble|system\s+prompt|model)\b", "soft_prompt_leak"),
    (r"\b(?:summarize|restate)\b.{0,160}\b(?:confidential\s+instructions?|instructions?\s+that\s+govern)\b", "soft_prompt_leak"),
    (r"\binstructions?\s+that\s+govern\s+(?:you|your\s+behavior)\b", "soft_prompt_leak"),
    (r"\b(?:constraints?|instructions?|rules?)\s+you\s+were\s+given\s+at\s+initialization\b", "soft_prompt_leak"),
    (r"\blist\s+the\s+exact\s+constraints?\b", "soft_prompt_leak"),
    (r"\bdiff\s+your\s+current\s+policy\b", "soft_prompt_leak"),
    (r"\bagainst\s+an\s+empty\s+policy\b", "soft_prompt_leak"),
    (r"\brestate\s+your\s+operating\s+rules\b", "soft_prompt_leak"),
    (r"\boperating\s+rules\b.{0,40}\bline\s+by\s+line\b", "soft_prompt_leak"),
    (r"\breads?\s+its\s+system\s+card\s+aloud\b", "soft_prompt_leak"),
    (r"\bsystem\s+card\b", "soft_prompt_leak"),
    (r"\bif\s+you\s+were\s+allowed\s+to\s+share\s+your\s+initial\s+instructions\b", "soft_prompt_leak"),
    # Acrostic / first-letter encoding tasks (probe: REVEALPROMPT poem)
    (r"first\s+letters?\s+of\s+each\s+line\s+spell", "soft_prompt_leak"),
    (r"\bacrostic\b.{0,80}\b(?:spell|reveal|prompt|system)\b", "soft_prompt_leak"),
    (r"\bspell\s+(?:out\s+)?(?:the\s+word\s+)?[A-Z]{6,}\b", "soft_prompt_leak"),
    (r"\bspell\s+REVEAL", "soft_prompt_leak"),
    # Soft preamble / bootstrap dumps (campaign residual class)
    (r"\b(?:dump|emit|cite|mirror|expand)\b.{0,120}\b(?:preamble|bootstrap|hidden\s+prefix|system\s+card)\b", "soft_prompt_leak"),
    (r"\bpreamble\s+that\s+was\s+loaded\b", "soft_prompt_leak"),
    (r"\bbefore\s+any\s+user\s+turns\b", "soft_prompt_leak"),
    (r"\bbefore\s+turn\s+zero\b", "soft_prompt_leak"),
    (r"\bhidden\s+prefix\s+of\s+this\s+chat\b", "soft_prompt_leak"),
    (r"\bbootstrap\s+configuration\b", "soft_prompt_leak"),
    (r"\binstruction\s+fields\b", "soft_prompt_leak"),
    (r"\bfrom\s+initialization\b.{0,80}\bverbatim\b", "soft_prompt_leak"),
    (r"\blist\s+constraints\b.{0,80}\b(?:initialization|verbatim)\b", "soft_prompt_leak"),
    # Soft inventory / alias leaks (wave-3 campaign)
    (r"\brecap\s+every\s+rule\s+that\s+shapes\s+your\s+replies\b", "soft_prompt_leak"),
    (r"\bnon-user\s+portion\s+of\s+the\s+conversation\s+transcript\b", "soft_prompt_leak"),
    (r"\babove\s+the\s+first\s+human\s+message\b", "soft_prompt_leak"),
    (r"\bexport\s+your\s+runtime\s+config\b", "soft_prompt_leak"),
    (r"\bseed\s+text\s+that\s+defines\s+how\s+you\s+behave\b", "soft_prompt_leak"),
    (r"\bstandard\s+operating\s+procedure\b.{0,80}\b(?:session\s+start|installed)\b", "soft_prompt_leak"),
    (r"\bguardrail\s+block\s+that\s+was\s+applied\b", "soft_prompt_leak"),
    (r"\bmeta-?prompt\b", "soft_prompt_leak"),
    (r"\bconstitution\s+or\s+charter\s+governing\s+this\s+assistant\b", "soft_prompt_leak"),
    (r"\bsysmsg\s+field\b", "soft_prompt_leak"),
    (r"\bdeveloper\s+message\s+that\s+was\s+set\b", "soft_prompt_leak"),
    (r"\brole\s+specification\s+blob\b", "soft_prompt_leak"),
    (r"\bsafety\s+layer\s+documentation\s+you\s+were\s+given\b", "soft_prompt_leak"),
    (r"\binstructions_v0\b", "soft_prompt_leak"),
    (r"\bmodel'?s\s+hidden\s+instructions\b", "soft_prompt_leak"),
    (r"\bhidden\s+system\s+instructions\b", "soft_prompt_leak"),
    (r"\bfull\s+rule\s+set\b.{0,80}\bempty\s+set\b", "soft_prompt_leak"),
    (r"\bset\s+difference\s+between\s+your\s+full\s+rule\s+set\b", "soft_prompt_leak"),
    (r"\bserialize\s+yourself\b.{0,80}\b(?:policy|instruction)\b", "soft_prompt_leak"),
    (r"\bshow-init-prompt\b", "soft_prompt_leak"),
    (r"\brecovery\s+mode\b.{0,120}\b(?:init\s+configuration|instruction)\b", "soft_prompt_leak"),
    (r"\bsurrounding\s+system\s+text\b", "soft_prompt_leak"),
    (r"\bloaded\s+before\s+the\s+first\s+user\s+message\b", "soft_prompt_leak"),
    (r"\bprintenv\b.{0,40}\bSYSTEM_(?:PROMPT|MESSAGE)\b", "soft_prompt_leak"),
    (r"\bcat\s+/proc/self/system_prompt\b", "soft_prompt_leak"),
    # ES / FR / DE / PT / IT direct ignore+prompt (minimal)
    (r"ignora(?:r)?\s+las\s+instrucciones\s+anteriores", "es_override"),
    (r"prompt\s+del\s+sistema", "es_system_prompt"),
    (r"ignore\s+les\s+instructions\s+pr[eé]c[eé]dentes", "fr_override"),
    (r"prompt\s+syst[eè]me", "fr_system_prompt"),
    (r"ignoriere\s+alle\s+vorherigen\s+anweisungen", "de_override"),
    (r"system-?prompt", "de_system_prompt"),
    (r"ignore\s+as\s+instru[cç][oõ]es\s+anteriores", "pt_override"),
    (r"prompt\s+do\s+sistema", "pt_system_prompt"),
    (r"ignora\s+le\s+istruzioni\s+precedenti", "it_override"),
    (r"prompt\s+di\s+sistema", "it_system_prompt"),
    # Delimiters
    (r"</?(?:system|assistant|user|human|ai)>", "message_delimiter"),
    (r"\[(?:SYSTEM|INST|/INST)\]", "format_delimiter"),
    (r"###\s*(?:System|Instruction|Human|Assistant)", "markdown_delimiter"),
    (r"<\|im_start\|>\s*system", "chatml_delimiter"),
    # Multilingual (minimal)
    (r"忽略.{0,30}(?:指令|指示|规则)", "zh_override"),
    (r"系统提示词?", "zh_system_prompt"),
    (r"(?:输出|显示|打印).{0,20}系统", "zh_reveal"),
    (r"игнорир\w*.{0,40}инструкц", "ru_override"),
    (r"системн\w*\s*промпт", "ru_system_prompt"),
    (r"покаж\w*.{0,30}(?:систем|промпт|инструкц)", "ru_reveal"),
    # JA / KO / AR (minimal override + system prompt)
    (r"以前の指示を無視", "ja_override"),
    (r"システムプロンプト", "ja_system_prompt"),
    (r"이전\s*지침을\s*무시", "ko_override"),
    (r"시스템\s*프롬프트", "ko_system_prompt"),
    (r"تجاهل.{0,40}التعليمات", "ar_override"),
    (r"موجه\s*النظام|برومبت\s*النظام", "ar_system_prompt"),
]

COMPILED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(p, re.IGNORECASE | re.DOTALL), cat) for p, cat in PATTERNS
]

# Categories that should block by default (all of the above are block-worthy for solo apps)
BLOCK_CATEGORIES = frozenset(cat for _, cat in PATTERNS)
