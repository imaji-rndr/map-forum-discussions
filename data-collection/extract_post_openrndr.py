#!/usr/bin/env python3
"""
This script does a basic archive of Discourse content by way of its API.

TODO: figure out how to handle post updates.

"""
import argparse
import urllib.request
import sys
import time
import os
import json
import functools
import datetime
from dataclasses import dataclass
from pathlib import Path
import logging

# Set up logging
loglevel = 'DEBUG' if os.environ.get('DEBUG') else 'INFO'
try:
    # If 'rich' is installed, use pretty logging
    from rich.logging import RichHandler
    logging.basicConfig(level=loglevel, datefmt="[%X]", handlers=[RichHandler()])
except ImportError:
    logging.basicConfig(level=loglevel)

log = logging.getLogger('archive')

# Argument parsing
parser = argparse.ArgumentParser(
    'discourse-archive',
    description='Create a basic content archive from a Discourse installation')
parser.add_argument(
    '-u', '--url', help='URL of the Discourse server',
    default=os.environ.get('DISCOURSE_URL', 'https://openrndr.discourse.group/'))
parser.add_argument(
    '--debug', action='store_true', default=os.environ.get('DEBUG'))
parser.add_argument(
    '-t', '--target_dir', help='Target directory for the archive',
    default=Path(os.environ.get('TARGET_DIR', './archive')))

# Cache the arguments for repeated access
@functools.cache
def args():
    return parser.parse_args()

# Enhanced HTTP GET function with retry and error handling
def http_get(path) -> str:
    log.debug("HTTP GET %s", path)
    backoff = 3
    while True:
        try:
            with urllib.request.urlopen(f"{args().url}{path}") as f:
                return f.read().decode()
        except urllib.error.URLError as e:
            log.error(f"Failed to reach the server. URL: {args().url}, Error: {e.reason}")
            time.sleep(backoff)
            backoff *= 2
            if backoff >= 256:
                log.exception('Ratelimit exceeded, or persistent network issues.')
                sys.exit(1)

# Function to get JSON data from HTTP response
def http_get_json(path) -> dict:
    try:
        return json.loads(http_get(path))
    except json.JSONDecodeError:
        log.warning("Unable to decode JSON response from %r", path)
        raise

# Post and Topic handling
@dataclass(frozen=True)
class PostSlug:
    @classmethod
    def id_from_filename(cls, name: str) -> int:
        return int(name.split('-', 1)[0])

@dataclass(frozen=True)
class PostTopic:
    id: int
    slug: str
    title: str

@dataclass(frozen=True)
class Post:
    id: int
    slug: str
    raw: dict

    def get_created_at(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.raw['created_at'])

    def save(self, dir: Path):
        """Write the raw post to disk"""
        idstr = str(self.id).zfill(10)
        filename = f"{idstr}-{self.raw['username']}-{self.raw['topic_slug']}.json"
        folder_name = self.get_created_at().strftime('%Y-%m-%B')
        full_path = dir / folder_name / filename
        full_path.parent.mkdir(parents=True, exist_ok=True)
        log.info("Saving post %s to %s", self.id, full_path)
        full_path.write_text(json.dumps(self.raw, indent=2))

    def get_topic(self) -> PostTopic:
        return PostTopic(
            id=self.raw['topic_id'],
            slug=self.raw['topic_slug'],
            title=self.raw['topic_title'],
        )

    @classmethod
    def from_json(cls, j: dict) -> 'Post':
        return cls(
            id=j['id'],
            slug=j['topic_slug'],
            raw=j,
        )

@dataclass(frozen=True)
class Topic:
    id: int
    slug: str
    raw: dict
    markdown: str

    def get_created_at(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.raw['created_at'])

    def save_rendered(self, dir: Path):
        """Write the rendered (.md) topic to disk"""
        date = str(self.get_created_at().date())
        filename = f"{date}-{self.slug}-id{self.id}.md"
        folder_name = self.get_created_at().strftime('%Y-%m-%B')
        full_path = dir / folder_name / filename
        full_path.parent.mkdir(parents=True, exist_ok=True)
        log.info("Saving topic markdown %s to %s", self.id, full_path)
        markdown = f"# {self.raw['title']}\n\n{self.markdown}"
        full_path.write_text(markdown, encoding='utf-8')

    @classmethod
    def from_json(cls, t: dict, markdown: str) -> 'Topic':
        return cls(
            id=t['id'],
            slug=t['slug'],
            raw=t,
            markdown=markdown,
        )

# Main archive logic
def main() -> None:
    target_dir = args().target_dir
    target_dir = Path(target_dir) if not isinstance(target_dir, Path) else target_dir

    (posts_dir := target_dir / 'posts').mkdir(parents=True, exist_ok=True)
    (topics_dir := target_dir / 'rendered_topics').mkdir(parents=True, exist_ok=True)

    metadata_file = target_dir / '.metadata.json'
    last_sync_date = None
    metadata = {}

    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text())
        last_sync_date = datetime.datetime.fromisoformat(metadata['last_sync_date'])

    if last_sync_date:
        # Resync over the last day to catch any post edits
        last_sync_date -= datetime.timedelta(days=1)

    log.info("Detected latest synced post date: %s", last_sync_date)

    topics_to_get = {}
    max_created_at = None
    last_created_at = None
    last_id = None

    # Fetch posts from the latest page
    posts = http_get_json('/posts.json')['latest_posts']
    no_new_posts = False

    while posts:
        log.info("Processing %d posts", len(posts))
        for json_post in posts:
            try:
                post = Post.from_json(json_post)
            except Exception:
                log.warning("Failed to deserialize post %s", json_post)
                raise
            last_created_at = post.get_created_at()

            if last_sync_date and last_created_at < last_sync_date:
                no_new_posts = True
                break

            post.save(posts_dir)

            if not max_created_at:
                max_created_at = post.get_created_at()

            last_id = post.id
            topic = post.get_topic()
            topics_to_get[topic.id] = topic

        # Stop if no new posts or at the earliest post
        if no_new_posts or (last_id and last_id <= 1):
            log.info("No new posts, stopping.")
            break

        time.sleep(5)  # Handle rate limiting
        posts = http_get_json(f'/posts.json?before={last_id - 1}')['latest_posts']

        # Handle implicit Discourse limits by adjusting the 'before' parameter
        while not posts and last_id >= 0:
            last_id -= 49
            posts = http_get_json(f'/posts.json?before={last_id}')['latest_posts']
            time.sleep(1)

    if max_created_at:
        metadata['last_sync_date'] = max_created_at.isoformat()
        log.info("Writing metadata: %s", metadata)
        metadata_file.write_text(json.dumps(metadata, indent=2))

    time.sleep(3)

    for topic in topics_to_get.values():
        data = http_get_json(f"/t/{topic.id}.json")
        body = http_get(f"/raw/{topic.id}")
        page_num = 2

        if not body:
            log.warning("Could not retrieve topic %d markdown", topic.id)
            continue

        while (more_body := http_get(f"/raw/{topic.id}?page={page_num}")):
            body += f"\n{more_body}"
            page_num += 1

        t = Topic.from_json(data, body)
        t.save_rendered(topics_dir)
        log.info("Saved topic %s (%s)", t.id, t.slug)

        time.sleep(0.3)

if __name__ == "__main__":
    main()