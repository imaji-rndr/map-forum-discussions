import os
import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

api_key = "..."
api_username = "..."
base_url = "https://discourse.processing.org/"
rate_limit_text = "Too many crawling requests."

# Path to the file containing topic ids
topic_ids_file = "topic_ids_processing.txt"

# Directory to store individual topic files
base_dir = "individual_topics_processing"
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# Read the list of topic ids from the text file
with open(topic_ids_file, 'r') as f:
    topic_ids = [line.strip() for line in f]

# Headers to simulate 'curl' user agent
headers = {
    "User-Agent": "curl/8.1.2",
    "Api-Username": api_username,
    "Api-Key": api_key
}

# Maximum number of requests before taking a break to avoid rate limits
REQUESTS_BEFORE_SLEEP = 20
SLEEP_DURATION = 60  # Time to sleep after REQUESTS_BEFORE_SLEEP requests (in seconds)

def fetch_topic_data(topic_id):
    """Fetch data for a single topic and save it to a file."""
    topic_url = f"{base_url}/t/{topic_id}.json"
    try:
        # Make the request to get the topic data
        response = requests.get(topic_url, headers=headers)

        # Handle rate limit (HTTP 429)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))  # Default to 60 seconds if not provided
            print(f"Rate limit reached for topic '{topic_id}', retrying after {retry_after} seconds")
            time.sleep(retry_after)
            return fetch_topic_data(topic_id)  # Retry after sleeping

        # Check for non-200 status code
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} for topic '{topic_id}', skipping.")
            return None

        # Parse the JSON response body
        topic_data = response.json()

        # Save the response body to a file
        file_path = os.path.join(base_dir, f"topic_{topic_id}.json")
        with open(file_path, "w", encoding='utf-8') as out_file:
            json.dump(topic_data, out_file, indent=4)

        print(f"Received and saved data for topic '{topic_id}'")

        # Sleep for a short random time between each request
        time.sleep(random.uniform(1, 3))  # Random sleep between 1 to 3 seconds

        return topic_id

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for topic '{topic_id}': {e}")
        return None

def main():
    # Number of threads (you can adjust based on your system capacity)
    max_workers = 10
    requests_made = 0  # Initialize the counter for requests made

    # Use ThreadPoolExecutor to fetch data in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks for fetching topics
        future_to_topic = {executor.submit(fetch_topic_data, topic_id): topic_id for topic_id in topic_ids}

        # Process completed tasks as they finish
        for future in as_completed(future_to_topic):
            topic_id = future_to_topic[future]
            try:
                future.result()  # Raise exceptions if any occurred
                requests_made += 1  # Increment the request counter

                # Sleep after making a certain number of requests to avoid rate limit
                if requests_made % REQUESTS_BEFORE_SLEEP == 0:
                    print(f"Reached {REQUESTS_BEFORE_SLEEP} requests, sleeping for {SLEEP_DURATION} seconds.")
                    time.sleep(SLEEP_DURATION)

            except Exception as exc:
                print(f"Topic {topic_id} generated an exception: {exc}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Finished fetching all topics in {end_time - start_time:.2f} seconds.")
