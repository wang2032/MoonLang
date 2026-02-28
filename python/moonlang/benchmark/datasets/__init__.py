from typing import Dict, Type

from moonlang.benchmark.datasets.common import BaseDataset, DatasetRow
from moonlang.benchmark.datasets.custom import CustomDataset
from moonlang.benchmark.datasets.generated_shared_prefix import (
    GeneratedSharedPrefixDataset,
)
from moonlang.benchmark.datasets.image import ImageDataset
from moonlang.benchmark.datasets.mmmu import MMMUDataset
from moonlang.benchmark.datasets.mooncake import MooncakeDataset
from moonlang.benchmark.datasets.openai_dataset import OpenAIDataset
from moonlang.benchmark.datasets.random import RandomDataset
from moonlang.benchmark.datasets.sharegpt import ShareGPTDataset

DATASET_MAPPING: Dict[str, Type[BaseDataset]] = {
    "sharegpt": ShareGPTDataset,
    "custom": CustomDataset,
    "openai": OpenAIDataset,
    # TODO: "random" vs "random-ids" should be a flag (e.g. --random-source=sharegpt|integers),
    # not two separate dataset names sharing the same class.
    "random": RandomDataset,
    "random-ids": RandomDataset,
    "generated-shared-prefix": GeneratedSharedPrefixDataset,
    "mmmu": MMMUDataset,
    "image": ImageDataset,
    "mooncake": MooncakeDataset,
}


def get_dataset(args, tokenizer, model_id=None):
    dataset_name = args.dataset_name
    if dataset_name.startswith("random") and dataset_name not in DATASET_MAPPING:
        dataset_name = "random-ids"

    if dataset_name not in DATASET_MAPPING:
        raise ValueError(f"Unknown dataset: {args.dataset_name}")

    dataset_cls = DATASET_MAPPING[dataset_name]
    dataset = dataset_cls.from_args(args)
    return dataset.load(tokenizer=tokenizer, model_id=model_id)


__all__ = [
    "DATASET_MAPPING",
    "DatasetRow",
    "get_dataset",
]
