# %%
import pandas as pd
import selecting_frames

# Set display options to show full row content
pd.options.display.max_colwidth = None  # Display full content of each column
pd.options.display.max_columns = None   # Display all columns in the DataFrame
pd.options.display.width = None         # Auto-adjust width to display full content without wrapping

import audioset.utils as utils

# %%
def load_audioset_file(path, **kwargs):
    """
    Attempts to load a CSV/TSV file from the given path using pandas.
    If the file does not exist, raises a FileNotFoundError with instructions
    on where to download AudioSet files.
    """
    try:
        if path.endswith('.tsv'):
            return pd.read_csv(path, sep=kwargs.get('sep', '\t'), header=kwargs.get('header', 0), names=kwargs.get('names', None))
        else:
            return pd.read_csv(path, skiprows=kwargs.get('skiprows', 0), quotechar=kwargs.get('quotechar', '"'), skipinitialspace=kwargs.get('skipinitialspace', False))
    except FileNotFoundError:
        # Provide instructions based on the filename
        filename = path.split('/')[-1]
        
        if filename in ["unbalanced_train_segments.csv", "balanced_train_segments.csv", "eval_segments.csv", "class_labels_indices.csv"]:
            raise FileNotFoundError(
                f"Cannot find '{filename}'. Please download the AudioSet base CSV files (including '{filename}') from:\n"
                "    https://research.google.com/audioset/download.html\n"
                "Place the downloaded files in the './audioset/' directory."
            )
        elif filename in ["audioset_eval_strong.tsv", "mid_to_display_name.tsv"]:
            raise FileNotFoundError(
                f"Cannot find '{filename}'. Please download the AudioSet strong-label TSV files (including '{filename}') from:\n"
                "    https://research.google.com/audioset/download_strong.html\n"
                "Place the downloaded files in the './audioset/' directory."
            )
        else:
            raise FileNotFoundError(f"File '{filename}' not found. Please verify the path and existence of the file.")

# Attempt to load each file with custom error messages
audioset_train_unbalanced_df = load_audioset_file(
    './audioset/unbalanced_train_segments.csv',
    skiprows=2, quotechar='"', skipinitialspace=True
)

audioset_train_balanced_df = load_audioset_file(
    './audioset/balanced_train_segments.csv',
    skiprows=2, quotechar='"', skipinitialspace=True
)

audioset_eval_df = load_audioset_file(
    './audioset/eval_segments.csv',
    skiprows=2, quotechar='"', skipinitialspace=True
)

audioset_eval_strong_df = load_audioset_file(
    './audioset/audioset_eval_strong.tsv',
    sep='\t'
)

class_labels_df = load_audioset_file(
    './audioset/class_labels_indices.csv',
    index_col=0
).reset_index(drop=True)

class_labels_strong_df = load_audioset_file(
    './audioset/mid_to_display_name.tsv',
    sep='\t', names=['mid', 'display_name']
)

class_labels_df = pd.concat([class_labels_df, class_labels_strong_df]).drop_duplicates()

# %%
# For each 'mid', group rows by 'mid' and find the row index with the longest 'display_name'
class_labels_df = class_labels_df.loc[  
    # Group the DataFrame by 'mid' and calculate the index of the row with the longest 'display_name' in each group
    class_labels_df.groupby('mid')['display_name']
    .apply(lambda group: group.str.len().idxmax())
    .drop_duplicates()  # Remove any duplicate indices that might arise after finding the longest display_name
]

#%%
audioset_train_balanced_df = utils.replace_by_class_names(audioset_train_balanced_df,
                                                          'positive_labels',
                                                          class_labels_df,
                                                          )

audioset_eval_df = utils.replace_by_class_names(audioset_eval_df,
                                                          'positive_labels',
                                                          class_labels_df,
                                                          )

audioset_eval_strong_df = utils.replace_by_class_names(audioset_eval_strong_df,
                                                          'label',
                                                          class_labels_df,
                                                          )

# %%
audioset_eval_strong_df[['video_id', 'video_start_time']] = audioset_eval_strong_df['segment_id'].str.extract(r'(.+)_(\d+)$')
audioset_eval_strong_df['video_start_time'] = audioset_eval_strong_df['video_start_time'].astype(int) / 1000
audioset_eval_strong_df = audioset_eval_strong_df.drop(columns=['segment_id'])

# %%
audioset_eval_strong_df_reconstructed = audioset_eval_strong_df.groupby(["video_id", "video_start_time"]).apply(
    lambda group: '; '.join(f"{row['start_time_seconds']}s-{row['end_time_seconds']}s -> {row['label']}" for _, row in group.iterrows())
).reset_index().rename({0: "timing_string"}, axis=1)

# %%
valor_train = pd.read_csv('./gpt35_dataset/processed_train_data.csv', on_bad_lines='skip')
valor_val = pd.read_csv('./gpt35_dataset/processed_val_data.csv', on_bad_lines='skip')
valor_test = pd.read_csv('./gpt35_dataset/processed_test_data.csv', on_bad_lines='skip')
# %%
# Combine all valor datasets
valor_combined = pd.concat([valor_train, valor_val, valor_test])

# Merge the data: keeping only rows in valor_combined that exist in either audioset_eval_df or audioset_train_balanced_df
# Combine the two audio set DataFrames for easier lookup
combined_audioset_df = pd.concat([audioset_eval_df, audioset_train_balanced_df])

# Filter combined_audioset_df to include only the entries found in valor_combined
matching_ids = valor_combined["video_id"].unique()
combined_filtered_df = combined_audioset_df[combined_audioset_df["# YTID"].isin(matching_ids)]

# Merge the class names with valor_combined, retaining the original order
# Rename '# YTID' to match valor_combined's 'video_id' for merging
combined_filtered_df = combined_filtered_df.rename(columns={'# YTID': 'video_id'})
merged_df = pd.merge(valor_combined, combined_filtered_df[['video_id', 'positive_labels']], on='video_id', how='left')

# %%
def generate_prompt_text(video_id, valor_combined, combined_audioset_df, audioset_eval_strong_df_reconstructed, frame_timestamps):
    caption = valor_combined[valor_combined['video_id'] == video_id]['caption'].values[0]

    # Check if video_id exists in audioset_eval_strong_df_reconstructed
    filtered_strong = audioset_eval_strong_df_reconstructed[audioset_eval_strong_df_reconstructed['video_id'] == video_id]
    if not filtered_strong.empty:
        audio_tags = filtered_strong["timing_string"].values[0]
        # Dynamic instructions for categories when tags are available
        count_instruction = "Ask 3 questions. Visual: Count items visible in the video. Audio: Count the frequency of specific sounds. Audio-Visual: Link counts across modalities (example \"How many <items> do you both see and hear?\")."
        temporal_instruction = "Ask 3 questions. Visual: Compare events happening before, after, or during specific times visually. Audio: Compare events happening before, after, or during specific times from audio. Audio-Visual: Combine events from both modalities (example \"What do you see before hearing <event>?\")."
        description_instruction = "Ask 3 questions. Visual: about visual details, excluding movement. Audio: about audio-only details (example background sounds). Audio-Visual: Combine visual and audio details (example \"Does <item> produce sound?\")"
    else:
        # Fallback instructions when no audio tags are found
        audio_tags = combined_audioset_df[combined_audioset_df["# YTID"] == video_id]["positive_labels"].values[0]
        count_instruction = "Ask 1 question about how many specific items seen (visual)"
        temporal_instruction = "Ask 1 question which event happened before the other (visual)"
        description_instruction = "Ask 2 questions. Visual: about visual details, excluding movement. Audio: about audio-only details (example background sounds)"

    # Frame timestamps information
    frame_info = ", ".join([f"{i + 1}st->{timestamp:0.1f}s" for i, timestamp in enumerate(frame_timestamps)])

    # Build the prompt string with trimmed spaces
    prompt = "\n".join([
        f"You are provided with {len(frame_timestamps)} sequential video frames,"
        + ("The video includes audio, which I can describe for you as tags" if filtered_strong.empty else "along with their time spans for audio and video."),
        "Additionally, a brief caption describes the video content and audio details. Use this information to create questions that require watching the video to be answerable, avoiding general knowledge questions.",
        "Modality Definitions:",
        "Visual: Answer is fully derived from the video frames alone. Audio: Answer relies only on audio information. Audio-Visual: Both audio and visual information are essential for a 100% accurate answer.",
        "Question Categories:",
        "Relative Position (Visual): Ask about the position of one object relative to another.",
        f"Description: {description_instruction}",
        f"Action: Ask 2 questions. Visual: about movements in the video. Audio-Visual: Link sounds to movements (example \"What sound accompanies a movement?\")",
        f"Temporal: {temporal_instruction}",
        f"Count: {count_instruction}",
        "Location: Visual: Ask about the locations of objects or scenes in the video.",
        "Guidelines for Question Generation: Only generate questions when the video or caption provides clear and specific information. Do not invent details\nAvoid using the term “frames” in questions. Refer to \"the video\" instead\nEnsure questions require specific observation of the video and are not general knowledge",
        "Answer Format: 1.Multiple-choice format:\nProvide 4 options, with only one correct answer\nEnsure all options are of similar length\nAnswer Variations:\nInclude the correct answer along with three rephrased versions of the answer",
        "Additional Fields for Each Question:\nQuality Rating:-Obvious: The answer is easily inferred from the provided information. -Guess: The answer likely exists but is not obvious.\nInference Check:Indicate whether the question itself contains part of the answer or if the answer can’t be inferred directly.\nModality: Visual, Audio, or Audio-Visual.Category: from the listed categories (example Relative Position, Description).\nSource Tags:Indicate the sources used to create the question as tags: Frames, Caption, Audio",
        ""
        f"Frame timestamps: {frame_info}",
        f"Audio tags: {audio_tags}",
        "",
        f"Caption: {caption}",
        'Return format one line json: {"questions":[{"question":"string","options":["string","string","string","string"],"correct_answer_idx":int,"rephrased_answers":["string","string","string"],"quality_rating":"string (obvious | guess)","modality":"string (visual | audio | audio-visual)","category":"string (relative_position | description | action | temporal | count | location)","source_tags":["frames","caption","audio"]}]}'
    ])

    return prompt

# Wrapper function to generate prompt with only video_id input
def generate_prompt_and_frames(video_id, directory="./video_samples"):
    filtered_frames, filtered_timestamps = selecting_frames.get_filtered_frames(video_id, directory, max_frames=5)
    # Convert frames to base64
    filtered_frames_base64 = selecting_frames.convert_frames_to_base64(filtered_frames)
    return generate_prompt_text(video_id, valor_combined, combined_audioset_df, audioset_eval_strong_df_reconstructed, filtered_timestamps), filtered_frames_base64