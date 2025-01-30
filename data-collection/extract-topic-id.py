import os
import json

#folder_path = "topics_processing_curl"
folder_path = "topics_cinder"

all_topic_ids = []

for file_name in os.listdir(folder_path):
    if file_name.endswith(".json"):
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)

                topics = data.get("topic_list", {}).get("topics", [])
                topic_ids = [topic["id"] for topic in topics]

                all_topic_ids.extend(topic_ids)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file {file_name}: {e}")

print(all_topic_ids)

#save_path = "topic_ids_processing.txt"
save_path = "topic_ids_cinder.txt"

with open(save_path, 'w', encoding='utf-8') as f:
    for topic_id in all_topic_ids:
        f.write(f"{topic_id}\n")
