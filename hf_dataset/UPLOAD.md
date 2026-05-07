# Uploading to Hugging Face

This folder is ready to be used as the root of a Hugging Face dataset repository.

## Option 1: Web Upload

1. Create a new dataset repository at https://huggingface.co/new-dataset.
2. Upload the contents of this `hf_dataset/` directory.
3. Keep `.gitattributes` so large JSONL files are stored with Git LFS.
4. After upload, the Dataset Viewer should show two configurations: `flattened` and `grouped`.

## Option 2: Command Line

```bash
pip install -U huggingface_hub
huggingface-cli login
huggingface-cli repo create YOUR_USERNAME/valor32k-avqa-v2 --type dataset
cd hf_dataset
git init
git lfs install
git remote add origin https://huggingface.co/datasets/YOUR_USERNAME/valor32k-avqa-v2
git add .
git commit -m "Add Valor32k-AVQA v2 dataset"
git push origin main
```

## Regenerating the Export

From the project root:

```bash
py code/prepare_hf_dataset.py --no-clean
```

Use `--no-clean` on Windows/OneDrive if metadata files are locked during deletion.
