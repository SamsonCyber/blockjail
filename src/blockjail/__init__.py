"""blockjail — tiny local jailbreak gate for solo LLM apps."""

from blockjail.judge import Verdict, check, is_blocked

__version__ = "0.1.0"
__all__ = ["Verdict", "check", "is_blocked", "__version__"]
