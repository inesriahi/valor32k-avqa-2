# %%
import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim
import os
import base64
import io
from PIL import Image

# %%
def extract_frames(video_path, fps=1):
    cap = cv2.VideoCapture(video_path)
    frames = []
    timestamps = []
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    interval = max(1, int(frame_rate / fps))

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % interval == 0:
            frames.append(frame)
            timestamp = count / frame_rate
            timestamps.append(timestamp)
        count += 1

    cap.release()
    return frames, timestamps

# %%
def calculate_histograms(frames):
    histograms = []
    for frame in frames:
        hist = cv2.calcHist([frame], [0,1,2], None, [8,8,8], [0, 256, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        histograms.append(hist)
    return histograms

# Function to calculate block-based color histogram for each frame
def calculate_block_histograms(frames, num_blocks=4):
    histograms = []
    for frame in frames:
        h, w, _ = frame.shape
        block_size_h = h // num_blocks
        block_size_w = w // num_blocks
        block_hist = []

        for i in range(num_blocks):
            for j in range(num_blocks):
                block = frame[i*block_size_h:(i+1)*block_size_h, j*block_size_w: (j+1)*block_size_w]
                hist = cv2.calcHist([block], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()  # Normalize and flatten the histogram
                block_hist.extend(hist)
        histograms.append(np.array(block_hist))

    return histograms

# Function to calculate global and block-based color histogram for each frame
def calculate_combined_histograms(frames, num_blocks=4):
    histograms = []  # List of histograms; each histogram is a 1D numpy array
    for frame in frames:
        # Calculate global histogram
        global_hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        global_hist = cv2.normalize(global_hist, global_hist).flatten()  # Normalize and flatten the histogram
        
        h, w, _ = frame.shape
        block_size_h = h // num_blocks
        block_size_w = w // num_blocks
        block_hist = []
        # Divide the frame into blocks and calculate histogram for each block
        for i in range(num_blocks):
            for j in range(num_blocks):
                block = frame[i * block_size_h:(i + 1) * block_size_h, j * block_size_w:(j + 1) * block_size_w]
                hist = cv2.calcHist([block], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()  # Normalize and flatten the histogram
                block_hist.extend(hist)
        
        # Combine global and block-based histograms
        combined_hist = np.concatenate((global_hist, np.array(block_hist)))
        histograms.append(combined_hist)
    return histograms  # Output: list of 1D numpy arrays (combined histograms)


# %%
def select_representative_frames(frames, histograms, timestamps, num_clusters=5):
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(histograms)

    representative_frames = []
    representative_timestamps = [] 
    for cluster_idx in range(num_clusters):
        cluster_indices = np.where(kmeans.labels_ == cluster_idx)[0]
        if len(cluster_indices)> 0:
            cluster_frames = [frames[i] for i in cluster_indices]
            cluster_histograms = [histograms[i] for i in cluster_indices]

            entropy_scores = [np.sum(-h * np.log(h+1e-10)) for h in cluster_histograms]
            best_frame_idx = cluster_indices[np.argmax(entropy_scores)]
            representative_frames.append(frames[best_frame_idx])
            representative_timestamps.append(timestamps[best_frame_idx])
            
    # Sort the representative frames and timestamps based on timestamps
    sorted_indices = np.argsort(representative_timestamps)
    representative_frames = [representative_frames[i] for i in sorted_indices]
    representative_timestamps = [representative_timestamps[i] for i in sorted_indices]

    # Add the first and last frames to the representative frames
    # if len(frames) > 0:
    #     representative_frames.insert(0, frames[0])  # Add the first frame
    #     representative_timestamps.insert(0, timestamps[0])  # Add the first timestamp
    # if len(frames) > 1:
    #     representative_frames.append(frames[-1])  # Add the last frame
    #     representative_timestamps.append(timestamps[-1])  # Add the last timestamp

    return representative_frames, representative_timestamps


# %%
def get_distinct_frames(video_path, max_frames=3):
    frames, timestamps = extract_frames(video_path, fps=10)
    # Calculate combined histograms for the extracted frames
    histograms = calculate_combined_histograms(frames)  # Output: list of 1D numpy arrays (combined histograms)
    representative_frames, representative_timestamps = select_representative_frames(frames, histograms, timestamps, num_clusters=max_frames)
    return representative_frames, representative_timestamps

# %%
def find_video_path_by_id(video_id, directory="./video_samples"):
    """
    Search `directory` (and its subfolders) for any filename containing `video_id`.
    If found, return the full path. Otherwise, raise FileNotFoundError.
    """
    for root, dirs, files in os.walk(directory):
        for fname in files:
            if video_id in fname:
                return os.path.join(root, fname)

    # If we reach here, no file matched; raise an exception:
    raise FileNotFoundError(
        f"Video with ID '{video_id}' not found. "
        f"Make sure a file containing '{video_id}' is in the directory '{directory}'."
    )

# %%
def convert_frames_to_base64(frames):
    base64_frames = []
    for frame in frames:
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_bytes = buffer.tobytes()
        base64_str = base64.b64encode(jpg_bytes).decode('utf-8')
        base64_frames.append(base64_str)
    return base64_frames

# %%
# Function to remove consecutive frames with very little change
def remove_similar_frames(frames, timestamps, threshold=0.1, dynamic=False, min_frames=5):
    filtered_frames = [frames[0]]  # Start with the first frame
    filtered_timestamps = [timestamps[0]]
    removed_frames = []  # Keep track of removed frames
    removed_timestamps = []
    
    for i in range(1, len(frames)):
        # Calculate the difference between the current frame and the last added frame
        diff = cv2.absdiff(frames[i], filtered_frames[-1])
        # Calculate the mean difference
        mean_diff = np.mean(diff)
        # Dynamically adjust threshold if needed
        if dynamic:
            threshold = np.mean([threshold, mean_diff / 255])
        # If the mean difference is greater than the threshold, keep the frame
        if mean_diff > threshold * 255:  # Scale threshold by 255 (max pixel value)
            filtered_frames.append(frames[i])
            filtered_timestamps.append(timestamps[i])
        else:
            removed_frames.append((frames[i], timestamps[i], mean_diff))
    
    if len(filtered_frames) < min_frames:
        # Sort removed frames by their similarity and histogram difference (ascending order) to bring back the most different frames
        removed_frames.sort(key=lambda x: (x[2],), reverse=True)
        additional_needed = min_frames - len(filtered_frames)
        for i in range(additional_needed):
            filtered_frames.append(removed_frames[i][0])
            filtered_timestamps.append(removed_frames[i][1])

    # Sort the filtered frames by their timestamps
    sorted_indices = np.argsort(filtered_timestamps)
    filtered_frames = [filtered_frames[i] for i in sorted_indices]
    filtered_timestamps = [filtered_timestamps[i] for i in sorted_indices]
    return filtered_frames, filtered_timestamps

# %%
def get_filtered_frames(video_id, directory="./video_samples", max_frames=5):
    video_path = find_video_path_by_id(video_id, directory)
    if not video_path:
        raise FileNotFoundError(f"Video with ID {video_id} not found.")

    frames, timestamps = get_distinct_frames(video_path, max_frames=max_frames)

    # Concatenate frames selected at regular intervals
    interval_count = 10  # Number of frames to be plotted at regular intervals
    all_frames, all_timestamps = extract_frames(video_path)  # Extract all frames from the video
    regular_interval_indices = np.linspace(0, len(all_frames) - 1, interval_count, dtype=int)
    concat_frames = frames + [all_frames[i] for i in regular_interval_indices]
    concat_timestamps = timestamps + [all_timestamps[i] for i in regular_interval_indices]

    # Sort concatenated frames by timestamps
    sorted_indices = np.argsort(concat_timestamps)
    concat_frames_sorted = [concat_frames[i] for i in sorted_indices]
    concat_timestamps_sorted = [concat_timestamps[i] for i in sorted_indices]

    # Remove similar consecutive frames
    filtered_frames, filtered_timestamps = remove_similar_frames(concat_frames_sorted, concat_timestamps_sorted, dynamic=True, min_frames=5, threshold=0.08)

    return filtered_frames, filtered_timestamps

#%%
def get_base64_image_size(base64_string):
    """
    Computes the size of a Base64-encoded image.
    
    Parameters:
        base64_string (str): The Base64 string of the image.
    
    Returns:
        tuple: A tuple containing the size in bytes and kilobytes (bytes, kilobytes).
    """
    try:
        # Decode the Base64 string to bytes
        image_data = base64.b64decode(base64_string)
        
        # Calculate the size in bytes
        size_in_bytes = len(image_data)
        
        # Calculate the size in kilobytes
        size_in_kilobytes = size_in_bytes / 1024
        
        return size_in_bytes, size_in_kilobytes
    except Exception as e:
        print(f"Error decoding Base64 string: {e}")
        return None, None
    
# %%
from PIL import Image
from io import BytesIO
def get_base64_image_dimensions(base64_string):
    """
    Computes the dimensions (width, height) of a Base64-encoded image.
    
    Parameters:
        base64_string (str): The Base64 string of the image.
    
    Returns:
        tuple: A tuple containing the width and height of the image (width, height).
    """
    try:
        # Decode the Base64 string to bytes
        image_data = base64.b64decode(base64_string)
        
        # Create a BytesIO stream from the bytes
        image_stream = BytesIO(image_data)
        
        # Open the image using PIL
        image = Image.open(image_stream)
        
        # Get the dimensions
        width, height = image.size
        
        return width, height
    except Exception as e:
        print(f"Error decoding Base64 string or reading image: {e}")
        return None, None
