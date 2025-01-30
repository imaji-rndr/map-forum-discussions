import os
import json
import pandas as pd

#folder_path = 'individual_topics_processing'
folder_path = 'individual_topics_cinder'

all_posts = []

for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(folder_path, filename)
    
        with open(file_path, 'r') as file:
            data = json.load(file)

            posts = data.get("post_stream", {}).get("posts", [])

            all_posts.extend(posts)

posts_df = pd.DataFrame(all_posts)

print(posts_df.columns)
print(posts_df.head())

#posts_df.to_csv('combined_posts_processing.csv', index=False)
posts_df.to_csv('combined_posts_cinder.csv', index=False)
