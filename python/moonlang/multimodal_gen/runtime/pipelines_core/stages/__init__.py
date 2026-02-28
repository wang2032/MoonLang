# Copied and adapted from: https://github.com/hao-ai-lab/FastVideo

# SPDX-License-Identifier: Apache-2.0
"""
Pipeline stages for diffusion models.

This package contains the various stages that can be composed to create
complete diffusion pipelines.
"""

from moonlang.multimodal_gen.runtime.pipelines_core.stages.base import PipelineStage
from moonlang.multimodal_gen.runtime.pipelines_core.stages.causal_denoising import (
    CausalDMDDenoisingStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.comfyui_latent_preparation import (
    ComfyUILatentPreparationStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.decoding import DecodingStage
from moonlang.multimodal_gen.runtime.pipelines_core.stages.decoding_av import (
    LTX2AVDecodingStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.denoising import DenoisingStage
from moonlang.multimodal_gen.runtime.pipelines_core.stages.denoising_av import (
    LTX2AVDenoisingStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.denoising_dmd import (
    DmdDenoisingStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.encoding import EncodingStage
from moonlang.multimodal_gen.runtime.pipelines_core.stages.image_encoding import (
    ImageEncodingStage,
    ImageVAEEncodingStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.input_validation import (
    InputValidationStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.latent_preparation import (
    LatentPreparationStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.latent_preparation_av import (
    LTX2AVLatentPreparationStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.text_connector import (
    LTX2TextConnectorStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.text_encoding import (
    TextEncodingStage,
)
from moonlang.multimodal_gen.runtime.pipelines_core.stages.timestep_preparation import (
    TimestepPreparationStage,
)

__all__ = [
    "PipelineStage",
    "InputValidationStage",
    "TimestepPreparationStage",
    "LatentPreparationStage",
    "ComfyUILatentPreparationStage",
    "LTX2AVLatentPreparationStage",
    "DenoisingStage",
    "DmdDenoisingStage",
    "LTX2AVDenoisingStage",
    "CausalDMDDenoisingStage",
    "EncodingStage",
    "DecodingStage",
    "LTX2AVDecodingStage",
    "ImageEncodingStage",
    "ImageVAEEncodingStage",
    "TextEncodingStage",
    "LTX2TextConnectorStage",
]
