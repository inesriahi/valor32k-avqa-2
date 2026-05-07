import argparse
import json
import os
import shutil
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "data" / "data"
DEFAULT_OUTPUT_DIR = ROOT / "hf_dataset"

SPLITS = ("train", "val", "test")
HF_SPLIT_NAMES = {"train": "train", "val": "validation", "test": "test"}

DATASET_CARD = """---
license: other
pretty_name: Valor32k-AVQA v2.0
task_categories:
- question-answering
- visual-question-answering
- multiple-choice
- video-text-to-text
task_ids:
- visual-question-answering
language:
- en
size_categories:
- 100K<n<1M
tags:
- audio
- video
- text
- tabular
- datasets
- pandas
- mlcroissant
- json
- audio-visual-question-answering
- audio-visual
- avqa
- video-question-answering
- video-understanding
- visual-question-answering
- multiple-choice
- open-ended-qa
- multimodal
- multimodal-understanding
- evaluation
- benchmark
dataset_info:
- config_name: default
  features:
  - name: caption
    dtype: string
  - name: video_id
    dtype: string
  - name: question
    dtype: string
  - name: options
    sequence: string
  - name: correct_answer_idx
    dtype: int64
  - name: rephrased_answers
    sequence: string
  - name: quality_rating
    dtype: string
  - name: modality
    dtype: string
  - name: category
    dtype: string
  - name: source_tags
    sequence: string
  - name: id
    dtype: int64
  - name: oid
    dtype: int64
  - name: model
    dtype: string
  splits:
  - name: train
    num_bytes: 96003770
    num_examples: 177132
  - name: validation
    num_bytes: 12076506
    num_examples: 22267
  - name: test
    num_bytes: 14168218
    num_examples: 26088
  download_size: 122248494
  dataset_size: 122248494
configs:
- config_name: default
  data_files:
  - split: train
    path: data/flattened/train.jsonl
  - split: validation
    path: data/flattened/validation.jsonl
  - split: test
    path: data/flattened/test.jsonl
---

# Valor32k-AVQA v2.0

Valor32k-AVQA v2.0 is an open-ended audio-visual question answering dataset and benchmark with 28,861 videos and 225,487 question-answer pairs in this Hugging Face release. Each question is annotated with a modality label (`visual`, `audio`, or `audio-visual`) and one of six categories: `description`, `action`, `count`, `temporal`, `location`, and `relative-position`.

## Links

- **Paper:** [ACM Digital Library](https://doi.org/10.1145/3746027.3758261)
- **Project page:** [inesriahi.github.io/valor32k-avqa-2](https://inesriahi.github.io/valor32k-avqa-2/)
- **Code and documentation:** [GitHub repository](https://github.com/inesriahi/valor32k-avqa-2)

## Modalities and Format

- **Modalities:** text annotations and tabular metadata for audio-video QA samples. Source videos/audio are referenced by `video_id` but are not stored as media files in this Hugging Face release.
- **Tasks:** audio-visual question answering, video question answering, visual question answering
- **Formats:** JSONL on Hugging Face; original JSON release files are available from the project repository
- **Library:** compatible with `datasets.load_dataset`

The Hugging Face release provides the flattened QA format as the default configuration:

- `default`: one question-answer item per row. This is the recommended format for training, evaluation, and Dataset Viewer preview.

The `modality` column can be used to filter examples into `visual`, `audio`, and `audio-visual` subsets without duplicating the dataset into separate configurations.

## Loading

```python
from datasets import load_dataset

dataset = load_dataset("inesriahi/valor32k-avqa-v2")
train = dataset["train"]
```

## Flattened Schema

- `caption`: source video caption
- `video_id`: video identifier
- `question`: generated question
- `options`: four answer choices
- `correct_answer_idx`: zero-based index of the correct option
- `rephrased_answers`: three paraphrases of the correct answer
- `quality_rating`: `obvious` or `guess`
- `modality`: `visual`, `audio`, or `audio-visual`
- `category`: question category
- `source_tags`: generation cues such as `frames`, `audio`, and `caption`
- `id`: question id
- `oid`: original video-level group id
- `model`: generator model label

## Dataset Statistics

- Unique videos: 28,861
- Total questions: 225,487
- Train questions: 177,132
- Validation questions: 22,267
- Test questions: 26,088

### Questions by Modality

- Visual: 130,640
- Audio-Visual: 49,663
- Audio: 45,184

### Questions by Category

- Description: 62,701
- Action: 47,689
- Count: 41,896
- Temporal: 41,358
- Location: 19,245
- Relative Position: 12,598

## Notes

The release contains annotations only. Full source videos are not redistributed in this Hugging Face dataset. Sample clips and project documentation are available in the project repository.

## Citation

```bibtex
@inproceedings{riahi2025valor32k,
  author    = {Riahi, Ines and Radman, Abduljalil and Guo, Zixin and Hedjam, Rachid and Laaksonen, Jorma},
  title     = {Valor32k-AVQA v2.0: Open-Ended Audio-Visual Question Answering Dataset and Benchmark},
  booktitle = {Proceedings of the 33rd ACM International Conference on Multimedia},
  series    = {MM '25},
  year      = {2025},
  pages     = {13097--13103},
  publisher = {Association for Computing Machinery},
  address   = {New York, NY, USA},
  location  = {Dublin, Ireland},
  isbn      = {9798400720352},
  doi       = {10.1145/3746027.3758261},
  url       = {https://doi.org/10.1145/3746027.3758261}
}
```

## License

Research use only. See the project repository for the full license terms.
"""

GITATTRIBUTES = """*.jsonl filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
"""


def json_array_to_jsonl(source_path: Path, target_path: Path) -> int:
    with source_path.open("r", encoding="utf-8") as source_file:
        data = json.load(source_file)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8", newline="\n") as target_file:
        for item in data:
            target_file.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
            target_file.write("\n")

    return len(data)


def write_static_files(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "README.md").write_text(DATASET_CARD, encoding="utf-8", newline="\n")
    (output_dir / ".gitattributes").write_text(GITATTRIBUTES, encoding="utf-8", newline="\n")


def remove_readonly(func, path, _exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def export_dataset(source_dir: Path, output_dir: Path, clean: bool) -> dict:
    if clean and output_dir.exists():
        shutil.rmtree(output_dir, onerror=remove_readonly)

    write_static_files(output_dir)

    counts = {"default": {}}
    for split in SPLITS:
        hf_split = HF_SPLIT_NAMES[split]
        flattened_source = source_dir / f"combined_dataset_{split}_flattened.json"

        counts["default"][hf_split] = json_array_to_jsonl(
            flattened_source,
            output_dir / "data" / "flattened" / f"{hf_split}.jsonl",
        )

    (output_dir / "export_summary.json").write_text(
        json.dumps(counts, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a Hugging Face Dataset Viewer compatible export.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--no-clean", action="store_true", help="Do not remove an existing output directory first.")
    args = parser.parse_args()

    counts = export_dataset(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        clean=not args.no_clean,
    )
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
