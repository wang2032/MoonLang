# Copied and adapted from: https://github.com/hao-ai-lab/FastVideo
from moonlang.multimodal_gen.configs.pipeline_configs import PipelineConfig
from moonlang.multimodal_gen.configs.sample import SamplingParams
from moonlang.multimodal_gen.runtime.entrypoints.diffusion_generator import DiffGenerator

__all__ = ["DiffGenerator", "PipelineConfig", "SamplingParams"]

# Trigger multimodal CI tests
