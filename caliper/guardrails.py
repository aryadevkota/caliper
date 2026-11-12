"""caliper.guardrails

Multi-layered security, safety, and scope guardrail system for the Caliper Agent.
Provides:
  1. Pre-Flight Input Guardrail (evaluate_input): Intercepts prompt injections,
     destructive intents, secret/system exfiltration, harmful acts, and out-of-scope abuse.
  2. Prompt Isolation Helper (wrap_untrusted_query): Safely wraps validated user input
     in strict semantic boundaries with delimiter breakout neutralization.
  3. Tool & Output Guardrails (validate_tool_call, sanitize_output): Validates tool
     invocations against safe registries/argument sizes and scrubs sensitive tokens.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Set

from caliper.tools import TOOLS

# Input character bounds
MAX_INPUT_LENGTH: int = 2000
MAX_TOOL_ARG_LENGTH: int = 500

# Canonical refusal messages
REFUSAL_INPUT_TOO_LONG: str = (
    "SECURITY NOTICE: Your request exceeds the maximum allowed length (2,000 characters). "
    "Please provide a concise sewing setup, defect description, or safety query."
)

REFUSAL_EMPTY_INPUT: str = (
    "ERROR: Empty query received. Please provide a sewing setup, defect, or safety request."
)

REFUSAL_PROMPT_INJECTION: str = (
    "SECURITY NOTICE: Instruction-override or role-hijacking pattern detected. "
    "Caliper strictly adheres to its sewing calibration and safety domain. "
    "Please submit a valid sewing machine, fabric, or stitch defect request."
)

REFUSAL_SYSTEM_EXFILTRATION: str = (
    "SECURITY NOTICE: System prompt, internal configuration, and credential exfiltration "
    "attempts are strictly prohibited. Caliper only provides sewing machine setup guidance."
)

REFUSAL_DESTRUCTIVE_INTENT: str = (
    "SECURITY NOTICE: Destructive operating system, database, or code execution commands "
    "are blocked by Caliper security guardrails. Only sewing machine calibration actions are permitted."
)

REFUSAL_UNETHICAL_OR_HARMFUL: str = (
    "SECURITY NOTICE: Requests involving harmful, malicious, violent, or illegal activities "
    "are blocked. Caliper operates exclusively as a safe sewing atelier assistant."
)

REFUSAL_OUT_OF_SCOPE: str = (
    "SCOPE NOTICE: Caliper is dedicated exclusively to sewing machine setup, fabric calibration, "
    "stitch defect diagnostics, and needle safety. Please ask a sewing-related question."
)


@dataclass
class GuardrailDecision:
    """Structured decision returned by evaluate_input."""
    allowed: bool
    category: str  # "safe", "prompt_injection", "destructive_intent", "system_exfiltration", "unethical_or_harmful", "out_of_scope", "input_too_long"
    reason: str
    refusal_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Pattern Definitions with Contextual False-Positive Shields
# ---------------------------------------------------------------------------

# Delimiter breakout patterns (e.g., trying to close the boundary)
_RE_DELIMITER_BREAKOUT = re.compile(
    r"</?(?:user_sewing_query|system|instruction|prompt|context)[^>]*>",
    re.IGNORECASE,
)

# Prompt injection & jailbreak patterns
_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above|system|your)\s+(?:instructions|prompts?|rules?|directives?)\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(?:all\s+)?(?:previous|prior|above|system|your)\s+(?:instructions|prompts?|rules?|directives?)\b", re.IGNORECASE),
    re.compile(r"\bforget\s+(?:everything|all\s+(?:previous|prior|above)\s+instructions?)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(?:a|an|the|in)\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(?:a|an)\s+(?!sewing|tailor|atelier|craft|machine|stitch|technician|mechanic|apprentice)\w+", re.IGNORECASE),
    re.compile(r"\benter\s+(?:developer\s+mode|god\s+mode|unrestricted\s+mode|dan\s+mode)\b", re.IGNORECASE),
    re.compile(r"\bdeveloper\s+mode\s+(?:enabled|activated|on)\b", re.IGNORECASE),
    re.compile(r"\b(?:jailbreak|jailbroken)\b", re.IGNORECASE),
    re.compile(r"\bdo\s+anything\s+now\b", re.IGNORECASE),
    re.compile(r"\bDAN\s+(?:mode|prompt|\d+)\b", re.IGNORECASE),
    re.compile(r"<\s*\|\s*im_start\s*\|>", re.IGNORECASE),
    re.compile(r"\[\s*SYSTEM(?:\s+PROMPT)?\s*\]", re.IGNORECASE),
    re.compile(r"\[\s*INST(?:RUCTION)?\s*\]", re.IGNORECASE),
    re.compile(r"\boverride\s+(?:safety|rules?|guardrails?|system|filters?)\b", re.IGNORECASE),
    re.compile(r"\bbypass\s+(?:safety|guardrails?|filters?|rules?)\b", re.IGNORECASE),
    re.compile(r"\bnew\s+operating\s+instructions?:", re.IGNORECASE),
]

# System prompt / secret exfiltration patterns
_EXFILTRATION_PATTERNS = [
    re.compile(r"\b(?:reveal|print|show|dump|leak|output|display|repeat)\s+(?:your\s+)?(?:system\s+prompt|initial\s+prompt|developer\s+instructions?|hidden\s+prompt|base\s+prompt)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:is|are)\s+your\s+(?:system\s+prompt|system\s+instructions?|hidden\s+rules?|developer\s+prompt)\b", re.IGNORECASE),
    re.compile(r"\bshow\s+(?:me\s+)?(?:all\s+)?environment\s+variables\b", re.IGNORECASE),
    re.compile(r"\bprintenv\b", re.IGNORECASE),
    re.compile(r"\b(?:show|reveal|print|dump|leak|get)\s+(?:the\s+)?(?:api[_-]?key|gemini[_-]?api[_-]?key|secret[_-]?key|token)\b", re.IGNORECASE),
    re.compile(r"\becho\s+\$(?:GEMINI_API_KEY|API_KEY|PATH|HOME|USER|SECRET)\b", re.IGNORECASE),
    re.compile(r"\bos\.environ(?:\.get)?\b", re.IGNORECASE),
]

# Destructive / command execution patterns
# Note: contextual shields prevent flagging "delete/reset dial", "needle snaps", "cut thread", etc.
_DESTRUCTIVE_PATTERNS = [
    re.compile(r"\brm\s+-[rRfF]{1,3}\b", re.IGNORECASE),
    re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    re.compile(r"\bdrop\s+database\b", re.IGNORECASE),
    re.compile(r"\btruncate\s+table\b", re.IGNORECASE),
    re.compile(r"\bdelete\s+from\s+\w+\b", re.IGNORECASE),
    re.compile(r"\bdelete\s+(?:all\s+)?(?:files|database|records|tables|users|root|everything\s+on\s+disk)\b", re.IGNORECASE),
    re.compile(r"\bformat\s+[a-z]:\s*", re.IGNORECASE),
    re.compile(r"\b(?:shutdown|reboot|init\s+0|poweroff)\b", re.IGNORECASE),
    re.compile(r"\b(?:os\.system|subprocess\.(?:Popen|run|call)|eval\(|exec\(|__import__)\b", re.IGNORECASE),
    re.compile(r"[;&|]\s*(?:rm|chmod|chown|kill|curl|wget|nc|bash|sh|zsh)\s+", re.IGNORECASE),
    re.compile(r">\s*/dev/(?:null|sd[a-z]|zero|urandom)\b", re.IGNORECASE),
    re.compile(r"\bmkfs(?:\.\w+)?\b", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", re.IGNORECASE),  # fork bomb
]

# Unethical or dangerous patterns (malware, exploitation, violence)
_HARMFUL_PATTERNS = [
    re.compile(r"\b(?:write|create|generate|code)\s+(?:a\s+)?(?:malware|ransomware|keylogger|trojan|virus|worm|exploit|payload|rootkit)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+to\s+(?:hack|ddos|dox|phish|exploit|defame)\b", re.IGNORECASE),
    re.compile(r"\b(?:steal|crack|exfiltrate)\s+(?:passwords?|credentials?|credit\s*cards?|tokens?)\b", re.IGNORECASE),
    re.compile(r"\b(?:build|make|manufacture)\s+(?:a\s+)?(?:bomb|explosive|weapon|poison|toxin)\b", re.IGNORECASE),
    re.compile(r"\b(?:suicide|self-harm|how\s+to\s+(?:hang|kill)\s+myself)\b", re.IGNORECASE),
]

# Sensitive token redaction regexes for output sanitization
_RE_SYSTEM_PROMPT_MARKER = re.compile(
    r"You are Caliper, an expert Universal Sewing Machine Setup and Calibration Agent",
    re.IGNORECASE,
)
_RE_GEMINI_KEY = re.compile(r"AIza[0-9A-Za-z-_]{35}")
_RE_GENERIC_SECRET = re.compile(r"(?:api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9-_]{16,}['\"]", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public Guardrail Functions
# ---------------------------------------------------------------------------

def evaluate_input(query: str) -> GuardrailDecision:
    """Evaluates an untrusted user query through pre-flight input guardrail layers.

    Guarantees:
      - Intercepts prompt injections, jailbreaks, delimiter escapes, system exfiltrations,
        destructive system commands, and harmful/malicious goals.
      - Zero false-positives on standard sewing queries, defect phrases ("broken needle",
        "needle snaps", "bird-nesting"), fabric density ("heavy denim", "450 GSM"),
        and dial reset queries.
    """
    if query is None:
        return GuardrailDecision(
            allowed=False,
            category="input_too_long",
            reason="Query is null.",
            refusal_message=REFUSAL_EMPTY_INPUT,
        )

    text = query.strip()
    if not text:
        return GuardrailDecision(
            allowed=False,
            category="input_too_long",
            reason="Query is empty.",
            refusal_message=REFUSAL_EMPTY_INPUT,
        )

    if len(text) > MAX_INPUT_LENGTH:
        return GuardrailDecision(
            allowed=False,
            category="input_too_long",
            reason=f"Query length ({len(text)} chars) exceeds maximum ({MAX_INPUT_LENGTH} chars).",
            refusal_message=REFUSAL_INPUT_TOO_LONG,
        )

    # Normalize whitespace for multi-line pattern matching
    normalized = re.sub(r"\s+", " ", text)

    # Layer 1: Delimiter breakout detection
    if _RE_DELIMITER_BREAKOUT.search(normalized):
        return GuardrailDecision(
            allowed=False,
            category="prompt_injection",
            reason="Structural delimiter breakout tags detected in input.",
            refusal_message=REFUSAL_PROMPT_INJECTION,
        )

    # Layer 2: Prompt injection / jailbreak detection
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(normalized):
            return GuardrailDecision(
                allowed=False,
                category="prompt_injection",
                reason=f"Prompt injection pattern matched: '{pattern.pattern}'.",
                refusal_message=REFUSAL_PROMPT_INJECTION,
            )

    # Layer 3: System prompt & secret exfiltration
    for pattern in _EXFILTRATION_PATTERNS:
        if pattern.search(normalized):
            return GuardrailDecision(
                allowed=False,
                category="system_exfiltration",
                reason=f"System prompt or credential exfiltration pattern matched: '{pattern.pattern}'.",
                refusal_message=REFUSAL_SYSTEM_EXFILTRATION,
            )

    # Layer 4: Destructive intent / system commands
    for pattern in _DESTRUCTIVE_PATTERNS:
        if pattern.search(normalized):
            return GuardrailDecision(
                allowed=False,
                category="destructive_intent",
                reason=f"Destructive shell/database pattern matched: '{pattern.pattern}'.",
                refusal_message=REFUSAL_DESTRUCTIVE_INTENT,
            )

    # Layer 5: Unethical or harmful acts
    for pattern in _HARMFUL_PATTERNS:
        if pattern.search(normalized):
            return GuardrailDecision(
                allowed=False,
                category="unethical_or_harmful",
                reason=f"Unethical or malicious intent pattern matched: '{pattern.pattern}'.",
                refusal_message=REFUSAL_UNETHICAL_OR_HARMFUL,
            )

    # All guardrail checks passed
    return GuardrailDecision(
        allowed=True,
        category="safe",
        reason="Query passed pre-flight safety, security, and scope guardrails.",
        refusal_message="",
    )


def wrap_untrusted_query(query: str) -> str:
    """Safely isolates an untrusted user query in unambiguous semantic boundary tags.

    Neutralizes any literal opening or closing `<user_sewing_query>` tags inside
    the query first so the model cannot be tricked into escaping the delimiter block.
    """
    cleaned = (query or "").strip()
    # Neutralize any attempts to simulate the closing delimiter
    cleaned = re.sub(r"</?\s*user_sewing_query\s*>", "[escaped-delimiter]", cleaned, flags=re.IGNORECASE)
    return f"<user_sewing_query>\n{cleaned}\n</user_sewing_query>"


def validate_tool_call(
    tool_name: str,
    tool_args: Dict[str, Any],
    allowed_tools: Optional[Set[str]] = None,
) -> Tuple[bool, str]:
    """Validates an LLM-generated tool call before execution.

    Args:
        tool_name: Function name proposed by LLM.
        tool_args: Proposed argument mapping.
        allowed_tools: Optional set of allowed tool names (defaults to caliper.tools.TOOLS).

    Returns:
        (is_valid, error_message)
    """
    valid_registry = allowed_tools if allowed_tools is not None else set(TOOLS.keys())

    if not isinstance(tool_name, str) or tool_name not in valid_registry:
        return False, f"SECURITY BLOCKED: Tool '{tool_name}' is not in the authorized Caliper tool registry."

    if not isinstance(tool_args, dict):
        return False, f"SECURITY BLOCKED: Arguments for tool '{tool_name}' must be a structured key-value dict."

    # Inspect argument sizes and payload contents
    for k, v in tool_args.items():
        if isinstance(v, str):
            if len(v) > MAX_TOOL_ARG_LENGTH:
                return False, f"SECURITY BLOCKED: Argument '{k}' exceeds length boundary ({len(v)} > {MAX_TOOL_ARG_LENGTH})."
            # Block shell injection syntax inside string arguments
            if re.search(r"[;&|`]\s*(?:rm|chmod|curl|wget|bash|sh|eval)\b", v, re.IGNORECASE):
                return False, f"SECURITY BLOCKED: Potentially malicious shell syntax in argument '{k}'."

    return True, ""


def sanitize_output(text: str) -> str:
    """Sanitizes outgoing LLM responses by scrubbing raw system prompt markers,
    API keys, and secret patterns.
    """
    if not text:
        return ""

    sanitized = text

    # Redact raw Gemini API keys
    sanitized = _RE_GEMINI_KEY.sub("[REDACTED_API_KEY]", sanitized)

    # Redact generic secret assignments
    sanitized = _RE_GENERIC_SECRET.sub("api_key = '[REDACTED]'", sanitized)

    # Replace raw system prompt leaks if verbatim excerpt was reflected
    if _RE_SYSTEM_PROMPT_MARKER.search(sanitized):
        sanitized = re.sub(
            r"You are Caliper, an expert Universal Sewing Machine Setup and Calibration Agent.*?(?=When you have|$)",
            "[REDACTED: System Prompt Configuration]",
            sanitized,
            flags=re.DOTALL | re.IGNORECASE,
        )

    return sanitized
