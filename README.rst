jackbot
#######

Retrieve results from various Jackbox games and push them to slack channel(s).

Installation
============

Clone this repo and run:

.. code-block::

    cd jackbot
    pip install .

Config
======

A config file containing the slack token and channel(s) should be stored in the ``~/.config/jackbot/config.json`` file.

Example config file:

.. code-block::

    {
        "slack_token": "xoxb-1111111111-222222222222-AAAAAAAAAAAAAAAAAAAAAAAA",
        "slack_channel": "private_channel"
    }

Usage
=====

.. code-block::

    jackkbot -g {GAME_NAME} -i {GAME_ID}

- ``GAME_NAME`` the name of the game for which the results originate
- ``GAME_ID`` is the ID of the game as provided by the link to the results/gallery provided at the conclusion of a game - the full url can be provided

Example:

.. code-block::

    jackkbot -g drawful2 -i https://games.jackbox.tv/artifact/DrawfulGame/195dd2b39eab8af9bb08c1a090723ef9