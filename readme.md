[Project Webpage](https://inesriahi.github.io/valor32k-avqa-2/)

# Valor32k-AVQA v2.0

**Open-Ended Audio-Visual Question Answering Dataset and Benchmark**
May 30, 2025

---

## Overview

Valor32k-AVQA v2.0 is a large-scale audio-visual question answering dataset containing **28,863 videos** and **225,495 QA pairs**. Each question is tagged by modality (Visual / Audio / Audio-Visual) and categorized into one of six types:

* **Description**
* **Action**
* **Count**
* **Temporal**
* **Location**
* **Relative Position**

All annotations are generated via a GPT-4o pipeline with human validation on a representative subset. Both open-ended and multiple-choice formats are supported.

---

## Dataset Contents

### File Types

1. **Flattened JSONs** (one question per object)

   * Fields (per entry):

     * `caption` — original video caption
     * `video_id` — unique segment identifier
     * `question` — generated question
     * `options` — four answer choices
     * `correct_answer_idx` — index (0–3) of the correct choice
     * `rephrased_answers` — three paraphrases of the correct answer
     * `quality_rating` — “obvious” or “guess”
     * `modality` — “visual” | “audio” | “audio-visual”
     * `category` — one of \[relative-position, description, action, temporal, count, location]
     * `source_tags` — which cues were used (e.g. “frames,” “audio,” “caption”)
     * `id` — unique question ID
     * `oid` — grouping ID for unflattened entries
     * `model` — “gpt4o” or “gpt3.5”

   * Files:

     * `combined_dataset_train_flattened.json`
     * `combined_dataset_val_flattened.json`
     * `combined_dataset_test_flattened.json`

2. **Unflattened JSONs** (questions grouped by video\_id)

   * Fields (per entry):

     * `video_id`
     * `caption`
     * `prompt` — text prompt used to generate all questions in that entry
     * `questions` — array of question objects (same structure as above)
     * `oid`, `model`

   * Files:

     * `combined_dataset_train.json`
     * `combined_dataset_val.json`
     * `combined_dataset_test.json`

3. **AudioSet Base CSVs** (not included in ZIP)

   * `eval_segments.csv`
   * `balanced_train_segments.csv`
   * `unbalanced_train_segments.csv`
   * `class_labels_indices.csv`

4. **AudioSet Strong-Labels TSVs** (not included in ZIP)

   * `mid_to_display_name.tsv`
   * `audioset_eval_strong.tsv`

---

## Download

* **Project Webpage (for full documentation)**
  [https://inesriahi.github.io/valor32k-avqa-2/](https://inesriahi.github.io/valor32k-avqa-2/)

* **Dataset ZIP** (all JSONs, flattened + unflattened)
  [https://github.com/inesriahi/valor32k-avqa-2/raw/refs/heads/main/data.zip](https://github.com/inesriahi/valor32k-avqa-2/raw/refs/heads/main/data.zip)
  Contains:

  ```
  combined_dataset_train_flattened.json  
  combined_dataset_val_flattened.json  
  combined_dataset_test_flattened.json  
  combined_dataset_train.json  
  combined_dataset_val.json  
  combined_dataset_test.json  
  ```

* **Video Samples (Original Valor32K Repository)**
  [https://pan.baidu.com/s/1aHWCwUOX1lJi0lSsmJb6Tw?pwd=e3ve](https://pan.baidu.com/s/1aHWCwUOX1lJi0lSsmJb6Tw?pwd=e3ve)

* **AudioSet Base CSVs** (download separately)
  [https://research.google.com/audioset/download.html](https://research.google.com/audioset/download.html)

* **AudioSet Strong Labels TSVs** (download separately)
  [https://research.google.com/audioset/download\_strong.html](https://research.google.com/audioset/download_strong.html)

---

## Directory Structure (after extraction)

```
data.zip
├─ combined_dataset_train_flattened.json
├─ combined_dataset_val_flattened.json
├─ combined_dataset_test_flattened.json
├─ combined_dataset_train.json
├─ combined_dataset_val.json
└─ combined_dataset_test.json

video_samples/
└─ <video_id>_<start>_<end>.mp4
```

---

## Dataset Statistics

* **Unique Videos:** 28,863

  * Train: 22,456  | Val: 2,942  | Test: 3,465

* **Total Questions:** 225,495

  * Train: 177,140  | Val: 22,267  | Test: 26,088

* **Avg Questions per Video:** 7.81

  * Train: 7.89  | Val: 7.57  | Test: 7.53

* **Unique Words:** 22,639

  * Train: 20,480  | Val: 8,936  | Test: 9,409

### Breakdown by Category (overall)

* Description: 62,666
* Action: 47,689
* Count: 41,897
* Temporal: 41,359
* Location: 19,245
* Relative Position: 12,600

### Breakdown by Modality (overall)

* Visual: 130,626
* Audio-Visual: 49,658
* Audio: 45,189

### Question Length (tokens)

* Average: 9.95
* Minimum: 2
* Maximum: 31

---

## Prompt Examples

1. **Strong Audio Tags**
   **Video ID:** `-uGHAvfqs2I`

   * **Frames (timestamps):** 0.00s, 0.80s, 1.00s, 3.00s, 4.00s, 7.00s, 8.00s, 9.60s
   * **Audio tags:**

     * 0.0–10.0s → Mechanisms
     * 4.402–5.205s → Meow
     * 6.346–6.638s → Meow
   * **Caption:**

     > In the room, a cat whirled around the door, barking from time to time.
   * **Prompt Highlights:**

     * Modality definitions (Visual / Audio / Audio-Visual)
     * Categories (Relative Position, Description, Action, Temporal, Count, Location)
     * Answer format: multiple-choice, 4 options, 1 correct, 3 rephrasings
     * Additional fields: `quality_rating`, `modality`, `category`, `source_tags`
     * Frame timestamps & audio tags

2. **No Strong Audio Tags**
   **Video ID:** `Sv9fcuRfk2o`

   * **Frames (timestamps):** 0.0s, 1.0s, 2.0s, 2.9s, 3.7s, 5.0s, 6.0s, 6.4s, 8.0s, 9.2s
   * **Audio tags:** Car alarm
   * **Caption:**

     > With the sound of the horn, two men happily take drinks on the road while talking.
   * **Prompt Highlights:**

     * Same category & format guidelines, with 10 frames and “Car alarm” as audio tag.

---

## Example QA Entries

### Video ID: `-uGHAvfqs2I` (00:30 – 00:40)

**Caption:**

> In the room, a cat whirled around the door, barking from time to time.

1. **Q:** How many times does the cat meow in the video?

   * **Modality:** Audio  | **Category:** Count
   * **Rephrasings:**

     * The cat meows twice
     * The cat makes two meowing sounds
     * There are two meows from the cat
   * **Options:**

     1. Three times
     2. **Twice** (✓)
     3. Four times
     4. Once

2. **Q:** What happens after the cat meows the second time?

   * **Modality:** Audio-Visual  | **Category:** Temporal
   * **Rephrasings:**

     * The cat leaves the frame
     * The cat exits the frame
     * The cat moves out of view
   * **Options:**

     1. The cat jumps
     2. **The cat moves out of the frame** (✓)
     3. The cat sits down
     4. The cat runs away

---

## How to Use

1. **Download & Extract**

   ```bash
   wget https://github.com/inesriahi/valor32k-avqa-2/raw/refs/heads/main/data.zip
   unzip data.zip -d valor32k_avqa_v2
   ```
2. **Inspect JSONs**

   * Flattened files: one question per object
   * Unflattened files: questions grouped by `video_id`
3. **Browse Video Samples**

   * Located under `video_samples/` (10-second MP4 clips)
   * Corresponding captions/prompts are in the JSONs
4. **Training & Evaluation**

   * Use provided train/val/test splits
   * Follow your model’s instructions for zero-shot or fine‐tuning pipelines

---

## Citation (BibTeX)

```bibtex
@article{valor32k_avqa_v2,
  author  = {Jon Doe and Jane Smith and Alice Johnson},
  title   = {Valor32k-AVQA v2.0: Open-Ended Audio-Visual Question Answering Dataset and Benchmark},
  journal = {Journal of Example},
  year    = {2025}
}
```

---

## License & Acknowledgments

* **License:** Research use only. See repository for full terms.
* **Dataset Source:** VALOR Repository ([https://github.com/TXH-mercury/VALOR](https://github.com/TXH-mercury/VALOR))
* **AudioSet Source:** Google AudioSet

Thank you for exploring Valor32k-AVQA v2.0!
