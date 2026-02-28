# Copied and adapted from: https://github.com/hao-ai-lab/FastVideo

from moonlang.multimodal_gen.configs.models.base import ModelConfig
from moonlang.multimodal_gen.configs.models.dits.base import DiTConfig
from moonlang.multimodal_gen.configs.models.encoders.base import EncoderConfig
from moonlang.multimodal_gen.configs.models.vaes.base import VAEConfig

__all__ = ["ModelConfig", "VAEConfig", "DiTConfig", "EncoderConfig"]
