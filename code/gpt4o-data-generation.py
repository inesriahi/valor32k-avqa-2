# %%

import base64
import os
import httpx
from openai import OpenAI
import prompt_builder
import pandas as pd
import random
import traceback
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import json
from tqdm import tqdm
import openai
from traceback import print_exc

@retry(wait=wait_random_exponential(min=6, max=10), stop=stop_after_attempt(5))
def completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)

# Open the image file and encode it as a base64 string
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

openai_endpoint_url = "/v1/openai/gpt4o/chat/completions"

OPENAI_API_KEY = "" # YOUR OpenAI API Key here

# %%
# read video_ids
split = "val" # change to train, val, test
valor_data = pd.read_csv(f'./processed_{split}_data.csv', on_bad_lines='skip') 
df = valor_data[["video_id","caption"]].drop_duplicates(subset=["video_id"])

# %%
def update_base_url(request: httpx.Request) -> None:
    if request.url.path == "/chat/completions":
        request.url = request.url.copy_with(path=openai_endpoint_url)

# File paths for storing results
results_file = f"results_gpt4o_{split}.json"
processed_videos_file = f"processed_videos_{split}.json"
error_videos_file = f"error_videos_{split}.json"
videoid_oid_file = "videoid_oid.json"

# Initialize files if they do not exist
def initialize_file(file_path, default_value):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(default_value, f, indent=4)

initialize_file(results_file, [])
initialize_file(processed_videos_file, [])
initialize_file(error_videos_file, [])

with open(videoid_oid_file, 'r', encoding='utf-8') as f:
    videoid_oid = json.load(f)

with open(processed_videos_file, 'r', encoding='utf-8') as f:
    processed_videos = set(json.load(f))

with open(error_videos_file, 'r', encoding='utf-8') as f:
    error_videos = json.load(f)
    error_videos_dict = {entry['video_id']: entry for entry in error_videos}
    error_videos = set(error_videos_dict.keys())

# Get the last question ID from results.json
with open(results_file, 'r', encoding='utf-8') as f:
    results = json.load(f)
    last_question_id = max((question.get("id", 0) for result in results for question in result.get("questions", [])), default=0)

client = OpenAI(
    base_url="https://xxx-openai-apigw.azure-api.net",
    api_key=False,  # API key not used, and rather set below
    default_headers={
        "Ocp-Apim-Subscription-Key": OPENAI_API_KEY,
    },
    http_client=httpx.Client(event_hooks={"request": [update_base_url]}),
)

# Filter dataframe before loop
df = df[~df['video_id'].isin(processed_videos | error_videos)]
print(f"Processing {len(df)} videos")

for row in tqdm(df.itertuples(index=False), total=len(df), desc="Processing videos"):
    video_id = row.video_id
    caption = row.caption
    # tqdm.write(f"Processing video ID: {video_id}")
    try:
        prompt, frames_base64 = prompt_builder.generate_prompt_and_frames(video_id)
        # print("===========================")
        content = []

        frames_to_process = frames_base64[:10]

        for frame_base64 in frames_to_process:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{frame_base64}"},
                    "detail": "low",
                }
            )
        content.append(
            {
                "type": "text",
                "text": prompt,
            }
        )
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI assistant that generates questions according to instructions.",
                    }
                ],
            },
            {
                "role": "user",
                "content": content,
            },
        ]

        completion = completion_with_backoff(
            model="no_effect",  # the model variable must be set, but has no effect, model selection done with URL
            messages=messages,
            temperature=0,
            top_p=0.95,
            max_tokens=3000,
        )

        # Assuming completion.choices[0].message.content is the string you're processing
        content_str = completion.choices[0].message.content

        # Find the first '{' and the last '}' in the string
        start_idx = content_str.find('{')
        end_idx = content_str.rfind('}')

        # Check if both '{' and '}' were found
        if start_idx != -1 and end_idx != -1:
            json_str = content_str[start_idx:end_idx + 1]
            try:
                # Parse the JSON content
                parsed_content = dict()
                if video_id in videoid_oid:
                    parsed_content["oid"] = videoid_oid[video_id]
                else:
                    new_oid = max(videoid_oid.values(), default=-1) + 1
                    videoid_oid[video_id] = new_oid
                    parsed_content["oid"] = new_oid
                    with open(videoid_oid_file, 'w', encoding='utf-8') as f:
                        json.dump(videoid_oid, f, indent=4)
                parsed_content["caption"] = caption
                parsed_content["video_id"] = video_id
                parsed_content["prompt"] = prompt
                parsed_content["questions"] = json.loads(json_str)["questions"]
                
                for question_item in parsed_content["questions"]:
                    last_question_id += 1
                    question_item["id"] = last_question_id
                    options = question_item["options"]
                    correct_answer_idx = question_item["correct_answer_idx"]
                    correct_option = options[correct_answer_idx]
                    random.shuffle(options)
                    correct_answer_idx = options.index(correct_option)

                    question_item["options"] = options
                    question_item["correct_answer_idx"] = correct_answer_idx
                

                # Append the result to results.json
                with open(results_file, 'r+', encoding='utf-8') as f:
                    results = json.load(f)
                    results.append(parsed_content)
                    f.seek(0)  # Move the file pointer to the beginning of the file
                    json.dump(results, f, indent=4)

                # Append the video ID to processed_videos.json
                with open(processed_videos_file, 'r+', encoding='utf-8') as f:
                    processed_videos = json.load(f)
                    processed_videos.append(video_id)
                    f.seek(0)  # Move the file pointer to the beginning of the file
                    json.dump(processed_videos, f, indent=4)

                # Print the parsed content in a nicely formatted way
                # print(json.dumps(parsed_content, indent=4))
            except json.JSONDecodeError as e:
                # print(f"Failed to parse JSON: {e}")
                # Use completion_fixed_json to fix the JSON content
                completion_fixed_json = completion_with_backoff(
                    model="no_effect",  # the model variable must be set, but has no effect, model selection done with URL
                    messages=[
                        {"role": "system", "content": [{"type": "text", "text": "fix the json in one line"}]},
                        {"role": "user", "content": json_str}
                    ],
                    temperature=0,
                    top_p=0.95,
                    max_tokens=3000,
                )
                fixed_json_str = completion_fixed_json.choices[0].message.content
                try:
                    parsed_content["questions"] = json.loads(fixed_json_str)["questions"]
                    
                    for question_item in parsed_content["questions"]:
                        last_question_id += 1
                        question_item["id"] = last_question_id
                        options = question_item["options"]
                        correct_answer_idx = question_item["correct_answer_idx"]
                        correct_option = options[correct_answer_idx]
                        random.shuffle(options)
                        correct_answer_idx = options.index(correct_option)

                        question_item["options"] = options
                        question_item["correct_answer_idx"] = correct_answer_idx

                    # Append the result to results.json
                    with open(results_file, 'r+', encoding='utf-8') as f:
                        results = json.load(f)
                        results.append(parsed_content)
                        f.seek(0)  # Move the file pointer to the beginning of the file
                        json.dump(results, f, indent=4)

                    # Append the video ID to processed_videos.json
                    with open(processed_videos_file, 'r+', encoding='utf-8') as f:
                        processed_videos = json.load(f)
                        processed_videos.append(video_id)
                        f.seek(0)  # Move the file pointer to the beginning of the file
                        json.dump(processed_videos, f, indent=4)

                except json.JSONDecodeError as e:
                    print(f"Failed to fix JSON: {e}", "fixed_json_str", fixed_json_str)
                    # Append the video ID and error message to error_videos.json
                    with open(error_videos_file, 'r+', encoding='utf-8') as f:
                        error_videos = json.load(f)
                        print_exc()
                        error_entry = {"video_id": video_id, "error": str(e), "trace": traceback.format_exc()}
                        error_videos.append(error_entry)
                        f.seek(0)  # Move the file pointer to the beginning of the file
                        json.dump(error_videos, f, indent=4)
        else:
            # print("No JSON content found")
            # Append the video ID and error message to error_videos.json
            with open(error_videos_file, 'r+', encoding='utf-8') as f:
                error_videos = json.load(f)
                error_entry = {"video_id": video_id, "error": "No JSON content found", "trace": completion.choices[0].content_filter_results}
                error_videos.append(error_entry)
                f.seek(0)  # Move the file pointer to the beginning of the file
                json.dump(error_videos, f, indent=4)

    except openai.BadRequestError as e:
        error_message = f"Error code: 400 - {str(e)}"
        error_entry = {
            "video_id": video_id,
            "error": error_message,
            "trace": traceback.format_exc()
        }
        print("error entry", error_entry)
        with open(error_videos_file, 'r+', encoding='utf-8') as f:
            error_videos = json.load(f)
            error_videos.append(error_entry)
            f.seek(0)
            json.dump(error_videos, f, indent=4)
            f.truncate()

    except Exception as e:
        # print("================== bad request error excpetion", e.__class__.__name__)
        error_message = str(e)
        print_exc()
        if "BadRequestError" in error_message:
            # Append the video ID and error message to error_videos.json
            with open(error_videos_file, 'r+', encoding='utf-8') as f:
                error_videos = json.load(f)
                import traceback
                error_entry = {
                    "video_id": video_id,
                    "error": error_message,  # Include the actual error message text
                    "trace": traceback.format_exc()  # Include the full error trace as a string
                }
                error_videos.append(error_entry)
                f.seek(0)  # Move the file pointer to the beginning of the file
                json.dump(error_videos, f, indent=4)

                # Skip to the next video
                continue

# gywN2QJ3QOs filtered content!!!