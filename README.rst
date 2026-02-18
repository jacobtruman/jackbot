jackbot
#######

Retrieve results from various Jackbox games and push them to slack channel(s).

Installation
============

Clone this repo and run:

.. code-block::

    cd jackbot
    uv tool install .

Or with pip:

.. code-block::

    cd jackbot
    pip install .

Config
======

A config file containing the slack token and channel(s) should be stored in the ``~/.config/jackbot/config.json`` file.

Example config file:

.. code-block::

    {
        "dev": {
            "slack_token": "xoxb-1111111111-222222222222-AAAAAAAAAAAAAAAAAAAAAAAA",
            "slack_channel": "dev_channel"
        },
        "prod": {
            "slack_token": "xoxb-1111111111-222222222222-AAAAAAAAAAAAAAAAAAAAAAAA",
            "slack_channel": "prod_channel",
            "slack_channel_id": "C9876543210"
        }
    }

- ``slack_token``: Your Slack bot token (starts with ``xoxb-``)
- ``slack_channel``: The channel name to post to
- ``slack_channel_id`` (optional): The Slack channel ID. If provided, this is used directly instead of looking up the channel name via the API. This avoids rate limiting issues. To find the channel ID, right-click the channel in Slack → "View channel details" → scroll to the bottom.

Slack Bot Scopes
----------------

Your Slack bot needs the following OAuth scopes:

- ``chat:write`` - Send messages
- ``files:write`` - Upload files/images
- ``channels:read`` - List public channels (for channel name → ID lookup)
- ``groups:read`` - List private channels (for channel name → ID lookup)
- ``channels:history`` - Read message history from public channels (for message management)
- ``groups:history`` - Read message history from private channels (for message management)

Usage
=====

Post Game Results
-----------------

.. code-block::

    jackbot -g {GAME_NAME} -i {GAME_ID}

- ``GAME_NAME`` is the name of the game for which the results originate (see ./jackbox dir)
- ``GAME_ID`` is the ID of the game as provided by the link to the results/gallery provided at the conclusion of a game - the full url can be provided

Example:

.. code-block::

    jackbot -g drawful -i https://games.jackbox.tv/artifact/DrawfulGame/195dd2b39eab8af9bb08c1a090723ef9

You can also use the ``-u`` flag to provide the full URL directly:

.. code-block::

    jackbot -u https://games.jackbox.tv/artifact/DrawfulGame/195dd2b39eab8af9bb08c1a090723ef9

API Account Selection
---------------------

Use the ``-a`` flag to select which API account from your config to use (defaults to ``dev``):

.. code-block::

    jackbot -a prod -u https://games.jackbox.tv/artifact/DrawfulGame/195dd2b39eab8af9bb08c1a090723ef9

Dry Run Mode
------------

Use the ``-d`` flag to run without sending messages to Slack:

.. code-block::

    jackbot -d -u https://games.jackbox.tv/artifact/DrawfulGame/195dd2b39eab8af9bb08c1a090723ef9

Message Management
------------------

Use the ``-m`` flag to list and delete bot messages from the Slack channel:

.. code-block::

    jackbot -m

This will:

1. Fetch the last 50 messages sent by the bot
2. Display them with timestamps and previews
3. Allow you to select which messages to delete (comma-separated numbers, ``all``, or ``q`` to quit)
4. Confirm before deleting

You can combine with ``-a`` to manage messages in a different account's channel:

.. code-block::

    jackbot -m -a prod
