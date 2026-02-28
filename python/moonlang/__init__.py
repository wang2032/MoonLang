# MoonLang public APIs

# Frontend Language APIs
from moonlang.global_config import global_config
from moonlang.lang.api import (
    Engine,
    Runtime,
    assistant,
    assistant_begin,
    assistant_end,
    flush_cache,
    function,
    gen,
    gen_int,
    gen_string,
    get_server_info,
    image,
    select,
    separate_reasoning,
    set_default_backend,
    system,
    system_begin,
    system_end,
    user,
    user_begin,
    user_end,
    video,
)
from moonlang.lang.backend.runtime_endpoint import RuntimeEndpoint
from moonlang.lang.choices import (
    greedy_token_selection,
    token_length_normalized,
    unconditional_likelihood_normalized,
)

# Lazy import some libraries
from moonlang.utils import LazyImport
from moonlang.version import __version__

Anthropic = LazyImport("moonlang.lang.backend.anthropic", "Anthropic")
LiteLLM = LazyImport("moonlang.lang.backend.litellm", "LiteLLM")
OpenAI = LazyImport("moonlang.lang.backend.openai", "OpenAI")
VertexAI = LazyImport("moonlang.lang.backend.vertexai", "VertexAI")

# Runtime Engine APIs
ServerArgs = LazyImport("moonlang.srt.server_args", "ServerArgs")
Engine = LazyImport("moonlang.srt.entrypoints.engine", "Engine")

__all__ = [
    "Engine",
    "Runtime",
    "assistant",
    "assistant_begin",
    "assistant_end",
    "flush_cache",
    "function",
    "gen",
    "gen_int",
    "gen_string",
    "get_server_info",
    "image",
    "select",
    "separate_reasoning",
    "set_default_backend",
    "system",
    "system_begin",
    "system_end",
    "user",
    "user_begin",
    "user_end",
    "video",
    "RuntimeEndpoint",
    "greedy_token_selection",
    "token_length_normalized",
    "unconditional_likelihood_normalized",
    "ServerArgs",
    "Anthropic",
    "LiteLLM",
    "OpenAI",
    "VertexAI",
    "global_config",
    "__version__",
]
