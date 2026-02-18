import json
import re
import sys
from pathlib import Path
from slack_sdk import WebClient
import requests


class Jackbox:  # pylint: disable=too-many-instance-attributes

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        self.dry_run = dry_run
        self.api_account = api_account
        self.ext = 'gif'
        config_file = f'{str(Path.home())}/.config/jackbot/config.json'
        try:
            with open(config_file) as file:
                config_json = json.loads(file.read())
        except FileNotFoundError as _fe:
            sys.exit(f"ERROR: config file not found {config_file}:\n\t{_fe}")
        except json.decoder.JSONDecodeError as _je:
            sys.exit(f"ERROR: invalid config file format {config_file}:\n\t{_je}")

        if self.api_account in config_json:
            config = config_json[self.api_account]
        else:
            sys.exit(f"API account not defined: {self.api_account}")

        self.slack_client = None if self.dry_run else WebClient(token=config['slack_token'])
        # Use slack_channel_id if set, otherwise resolve slack_channel name to ID
        if config.get('slack_channel_id'):
            self.slack_channel = config['slack_channel_id']
            print(f"Using configured channel ID: {self.slack_channel}")
        else:
            self.slack_channel = self._resolve_channel_id(config['slack_channel'])

        self._fishery_url = "https://fishery.jackboxgames.com/artifact"
        self._data_url = None
        self._gallery_url = None
        self._base_image_url = None
        self._base_gen_image_url = None

        self._game_id = None
        self.game_id = game_id
        self._game_name = None
        self._max_attempts = 5

        # Message queue for batching Slack messages
        self._pending_messages = []
        self._pending_files = []  # Track files to clean up

    @property
    def game_id(self):
        if self._game_name is None:
            self.game_name = self.__class__.__name__
        return self._game_id

    @game_id.setter
    def game_id(self, value):
        self._game_id = value.strip().strip("/").split("/")[-1]

    @property
    def data_url(self):
        return self._data_url

    @data_url.setter
    def data_url(self, value):
        self._data_url = f"{self._fishery_url}/{value}/{self.game_id}"

    @property
    def gallery_url(self):
        print(self._gallery_url)
        return self._gallery_url

    @gallery_url.setter
    def gallery_url(self, value):
        self._gallery_url = f"http://games.jackbox.tv/artifact/{value}/{self.game_id}"

    @property
    def base_image_url(self):
        return self._base_image_url

    @base_image_url.setter
    def base_image_url(self, value):
        self._base_image_url = f"https://s3.amazonaws.com/jbg-blobcast-artifacts/{value}/{self.game_id}"

    @property
    def base_gen_image_url(self):
        return self._base_gen_image_url

    @base_gen_image_url.setter
    def base_gen_image_url(self, value):
        self._base_gen_image_url = f"{self._fishery_url}/{self.ext}/{value}/{self.game_id}"

    @property
    def game_name(self):
        return self._game_name

    @game_name.setter
    def game_name(self, value):
        self._game_name = re.sub(r"([A-Z,0-9])", r" \1", value).strip()

    @staticmethod
    def parse_game_url(url):
        url_parts = url.strip("/").split("/")
        return url_parts[-2].replace("Game", ""), url_parts[-1]

    @staticmethod
    def clean_string(_string, underscore=True):
        pattern = re.compile(r'<[^>]+>')
        _string = pattern.sub('', _string)
        chars = ["'", '"', ",", "’", '“', '”', ";", "_"]
        for char in chars:
            _string = _string.replace(char, "").strip()
        special_chars = [("Ñ", "N"), ("Ï", "I"), ("Æ", "AE")]
        for char, _char in special_chars:
            _string = _string.replace(char, _char)
        if underscore:
            _string = _string.replace(' ', '_')
        return _string

    def _resolve_channel_id(self, channel):
        """Resolve a channel name to a channel ID.

        If the channel is already an ID (starts with C, G, D, or Z followed by alphanumeric),
        return it as-is. Otherwise, look up the channel ID from the Slack API.
        """
        import builtins
        import time
        from slack_sdk.errors import SlackApiError

        print(f"DEBUG: _resolve_channel_id called with channel='{channel}'")
        if self.dry_run or not channel:
            return channel

        # Check if it's already a channel ID (matches pattern ^[CGDZ][A-Z0-9]{8,}$)
        # Use case-insensitive match since Slack IDs can have mixed case
        if re.match(r'^[CGDZ][A-Za-z0-9]{8,}$', channel):
            print(f"Channel '{channel}' is already an ID, using as-is")
            return channel

        # Strip # prefix if present
        channel_name = channel.lstrip('#')
        print(f"Looking up channel ID for '{channel_name}'...")

        # Look up channel ID from Slack API with retry logic for rate limiting
        max_retries = 5
        retry_delay = 1  # Start with 1 second

        for attempt in builtins.range(max_retries):
            try:
                cursor = None
                while True:
                    response = self.slack_client.conversations_list(
                        types="public_channel,private_channel",
                        limit=200,
                        cursor=cursor
                    )
                    if response['ok']:
                        for ch in response['channels']:
                            if ch['name'] == channel_name:
                                print(f"Found channel ID: {ch['id']} for '{channel_name}'")
                                return ch['id']
                        # Check for pagination
                        cursor = response.get('response_metadata', {}).get('next_cursor')
                        if not cursor:
                            break
                    else:
                        print(f"WARNING: Failed to list channels: {response.get('error')}")
                        break
                # If we get here without finding the channel, break out of retry loop
                break
            except SlackApiError as ex:
                if ex.response.get('error') == 'ratelimited':
                    # Get retry-after header if available, otherwise use exponential backoff
                    retry_after = int(ex.response.headers.get('Retry-After', retry_delay))
                    print(f"Rate limited. Waiting {retry_after} seconds before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_after)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"WARNING: Failed to resolve channel ID for '{channel}': {ex}")
                    break
            except Exception as ex:
                print(f"WARNING: Failed to resolve channel ID for '{channel}': {ex}")
                break

        # Return original value if lookup fails
        print(f"WARNING: Could not find channel ID for '{channel}', using as-is")
        return channel

    def process_game(self):
        response = requests.get(self.data_url)
        if response.status_code == 200:
            return response.json()
        print(
            f"ERROR: Invalid response from server for url {self.data_url}: ({response.status_code}) {response.text}"
        )
        return False

    def generate_images(self, index: str, filename: str, attempt: int = 0, image_urls: dict | None = None):
        if image_urls is None:
            image_urls = {
                "gif": f"{self.base_image_url}/anim_{index}.gif",
                "png": f"{self.base_image_url}/image_{index}.png"
            }

        if self.ext == 'gif':
            url = f"{self.base_gen_image_url}/{index}"
            response = requests.get(url)

            print(f"INFO: Generating image {url}")
            if response.status_code != 200:
                attempt += 1
                print(f"ERROR: There was a problem generating image:\n{response.status_code}\t{response.text}\n"
                      f"Attempt: {attempt} / {self._max_attempts}")
                if attempt < self._max_attempts:
                    return self.generate_images(index=index, filename=filename, attempt=attempt, image_urls=image_urls)
                return False

        print(f"INFO: Getting image {image_urls[self.ext]}")
        response = requests.get(image_urls[self.ext])
        if response.status_code != 200:
            print(f"ERROR: There was a problem getting image:\n{response.status_code}\t{response.text}")
            return False
        with open(filename, 'wb') as file_handle:
            file_handle.write(response.content)

        return True

    def queue_intro_message(self):
        """Queue the intro message. Must be called before other messages.

        The intro message will be sent first, and its thread_ts will be used
        for all subsequent messages that have use_intro_thread=True.
        """
        blocks = str([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{self.game_name}*"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": self.gallery_url
                    }
                ]
            }
        ])

        message = {
            'type': 'intro_message',
            'text': self.gallery_url,
            'blocks': blocks,
            'channel': self.slack_channel,
        }
        # Insert at the beginning so it's sent first
        self._pending_messages.insert(0, message)

    def send_intro_message(self):
        """Deprecated: Use queue_intro_message() instead for batched sending."""
        blocks = str([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{self.game_name}*"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": self.gallery_url
                    }
                ]
            }
        ])

        if self.slack_client:
            return self.slack_client.chat_postMessage(channel=self.slack_channel, text=self.gallery_url, blocks=blocks)
        return None

    def queue_file_upload(self, file: str, title: str, thread_to_intro: bool = True, initial_comment: str = None):
        """Queue a file upload to be sent later.

        Args:
            file: Path to the file to upload
            title: Title for the file
            thread_to_intro: If True, this message will be threaded to the intro message
            initial_comment: Initial comment for the file (optional)
        """
        message = {
            'type': 'file_upload',
            'file': file,
            'title': title,
            'channel': self.slack_channel,
            'thread_to_intro': thread_to_intro,
        }
        if initial_comment:
            message['initial_comment'] = initial_comment
        self._pending_messages.append(message)
        self._pending_files.append(file)

    def queue_chat_message(self, text: str, blocks: str = None, thread_to_intro: bool = True):
        """Queue a chat message to be sent later.

        Args:
            text: Text content of the message
            blocks: Slack blocks for rich formatting (optional)
            thread_to_intro: If True, this message will be threaded to the intro message
        """
        message = {
            'type': 'chat_message',
            'text': text,
            'channel': self.slack_channel,
            'thread_to_intro': thread_to_intro,
        }
        if blocks:
            message['blocks'] = blocks
        self._pending_messages.append(message)

    def send_queued_messages(self):
        """Send all queued messages to Slack.

        Returns:
            True if all messages were sent successfully, False otherwise.
        """
        if not self.slack_client:
            print("INFO: No Slack client configured, skipping message send")
            self.clear_queue()
            return True

        print(f"INFO: Sending {len(self._pending_messages)} queued messages to Slack...")
        intro_thread_ts = None
        try:
            for message in self._pending_messages:
                # Determine thread_ts for this message
                thread_ts = None
                if message.get('thread_to_intro') and intro_thread_ts:
                    thread_ts = intro_thread_ts

                if message['type'] == 'intro_message':
                    # Send intro message and capture its thread_ts
                    response = self.slack_client.chat_postMessage(
                        channel=message['channel'],
                        text=message['text'],
                        blocks=message['blocks']
                    )
                    intro_thread_ts = response['ts']
                    print(f"INFO: Sent intro message, thread_ts={intro_thread_ts}")
                elif message['type'] == 'file_upload':
                    kwargs = {
                        'file': message['file'],
                        'title': message['title'],
                        'channel': message['channel'],
                    }
                    if thread_ts:
                        kwargs['thread_ts'] = thread_ts
                    if 'initial_comment' in message:
                        kwargs['initial_comment'] = message['initial_comment']
                    self.slack_client.files_upload_v2(**kwargs)
                elif message['type'] == 'chat_message':
                    kwargs = {
                        'channel': message['channel'],
                        'text': message['text'],
                    }
                    if 'blocks' in message:
                        kwargs['blocks'] = message['blocks']
                    if thread_ts:
                        kwargs['thread_ts'] = thread_ts
                    self.slack_client.chat_postMessage(**kwargs)
            print("INFO: All messages sent successfully")
            return True
        except Exception as ex:
            print(f"ERROR: Failed to send messages: {ex}")
            return False
        finally:
            self.clear_queue()

    def clear_queue(self, cleanup_files: bool = True):
        """Clear the message queue and optionally clean up pending files.

        Args:
            cleanup_files: If True, delete any pending files that were queued for upload
        """
        if cleanup_files:
            import os
            for filepath in self._pending_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"INFO: Cleaned up file {filepath}")
        self._pending_messages = []
        self._pending_files = []

    def get_bot_messages(self, limit: int = 100):
        """Get messages sent by this bot in the configured channel.

        Args:
            limit: Maximum number of messages to retrieve (default 100)

        Returns:
            List of message dictionaries with 'ts', 'text', 'date' keys
        """
        if not self.slack_client:
            print("ERROR: No Slack client configured")
            return []

        try:
            # Get bot's own user ID
            auth_response = self.slack_client.auth_test()
            bot_user_id = auth_response['user_id']

            # Get conversation history
            response = self.slack_client.conversations_history(
                channel=self.slack_channel,
                limit=limit
            )

            bot_messages = []
            for message in response.get('messages', []):
                # Filter to only bot's messages (check user or bot_id)
                if message.get('user') == bot_user_id or message.get('bot_id'):
                    # Only include if it's from our bot
                    if message.get('user') == bot_user_id:
                        from datetime import datetime
                        ts = float(message['ts'])
                        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                        # Get preview text (first 80 chars)
                        text = message.get('text', '')[:80]
                        if len(message.get('text', '')) > 80:
                            text += '...'

                        bot_messages.append({
                            'ts': message['ts'],
                            'text': text,
                            'date': date_str,
                            'has_files': 'files' in message
                        })

            return bot_messages

        except Exception as ex:
            print(f"ERROR: Failed to get messages: {ex}")
            return []

    def delete_messages(self, timestamps: list):
        """Delete messages by their timestamps.

        Args:
            timestamps: List of message timestamps to delete

        Returns:
            Tuple of (success_count, failure_count)
        """
        if not self.slack_client:
            print("ERROR: No Slack client configured")
            return (0, 0)

        success = 0
        failed = 0

        for ts in timestamps:
            try:
                self.slack_client.chat_delete(
                    channel=self.slack_channel,
                    ts=ts
                )
                success += 1
            except Exception as ex:
                print(f"ERROR: Failed to delete message {ts}: {ex}")
                failed += 1

        return (success, failed)

    @classmethod
    def manage_messages(cls, api_account: str = 'dev'):
        """Interactive message management - list and delete bot messages.

        Args:
            api_account: API account key from config
        """
        # Create a minimal instance just for message management
        instance = cls.__new__(cls)
        instance.dry_run = False
        instance.api_account = api_account

        config_file = f'{str(Path.home())}/.config/jackbot/config.json'
        try:
            with open(config_file) as file:
                config_json = json.loads(file.read())
        except FileNotFoundError as _fe:
            sys.exit(f"ERROR: config file not found {config_file}:\n\t{_fe}")
        except json.decoder.JSONDecodeError as _je:
            sys.exit(f"ERROR: invalid config file format {config_file}:\n\t{_je}")

        if api_account in config_json:
            config = config_json[api_account]
        else:
            sys.exit(f"API account not defined: {api_account}")

        instance.slack_client = WebClient(token=config['slack_token'])
        # Use slack_channel_id if set, otherwise resolve slack_channel name to ID
        if config.get('slack_channel_id'):
            instance.slack_channel = config['slack_channel_id']
            print(f"Using configured channel ID: {instance.slack_channel}")
        else:
            instance.slack_channel = instance._resolve_channel_id(config['slack_channel'])

        print(f"\nFetching messages from channel...")
        messages = instance.get_bot_messages(limit=50)

        if not messages:
            print("No bot messages found in channel.")
            return

        print(f"\nFound {len(messages)} bot messages:\n")
        print("-" * 80)
        for i, msg in enumerate(messages):
            file_indicator = " [FILE]" if msg['has_files'] else ""
            print(f"  [{i+1}] {msg['date']}{file_indicator}")
            print(f"      {msg['text']}")
            print()

        print("-" * 80)
        print("\nEnter message numbers to delete (comma-separated), 'all' to delete all, or 'q' to quit:")
        selection = input("> ").strip().lower()

        if selection == 'q' or selection == '':
            print("Cancelled.")
            return

        timestamps_to_delete = []
        if selection == 'all':
            timestamps_to_delete = [msg['ts'] for msg in messages]
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(messages):
                        timestamps_to_delete.append(messages[idx]['ts'])
                    else:
                        print(f"Warning: Invalid index {idx + 1}, skipping")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
                return

        if not timestamps_to_delete:
            print("No valid messages selected.")
            return

        print(f"\nAbout to delete {len(timestamps_to_delete)} message(s). Continue? (y/n)")
        confirm = input("> ").strip().lower()

        if confirm != 'y':
            print("Cancelled.")
            return

        success, failed = instance.delete_messages(timestamps_to_delete)
        print(f"\nDeleted {success} message(s), {failed} failed.")
