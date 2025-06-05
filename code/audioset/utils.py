import pandas as pd

def replace_by_class_names(audioset_df, coded_col_name, class_labels_df):
    # Create a dictionary mapping each mid to its display name
    label_mapping = dict(zip(class_labels_df['mid'], class_labels_df['display_name']))

    # Function to replace mids with display names in positive_labels column
    def replace_labels(label_str):
        # Split by commas to get each mid
        mids = label_str.split(',')
        # Map each mid to the corresponding display name, or keep the original if not found
        display_names = [label_mapping.get(mid, mid) for mid in mids]
        # Join the display names back into a single string
        return ', '.join(display_names)

    df_copy = audioset_df.copy()
    df_copy[coded_col_name] = df_copy[coded_col_name].apply(replace_labels)
    return df_copy
