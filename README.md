# Navegate SlackBot

Author: Michael Spear
## Table of contents
[General](#general)

[Features](#features)

[Setup](#setup)

[Maintenance](#maintenance)

[Database](#database)

## General
This is my python SlackBot I wrote using the slackclient library which provides a pythonic interface with the Slack REST API. Some effor has been made to write tests, document functions and generally make this program accessable to other contributers but it's still mostly proprietary to me. The purpose of this SlackBot is to generate psudo-random pairs of testers to test issues in JIRA that have been moved to the Testing column in our workflow. The bot will keep track of how many tests each person has done and will assign those who have tested the least number of issue.

In order to increase throughput and efficiency the bot also has the ability to track when a user is gone, i.e. not available to test issues and will skip over them when assigning tests.

One flaw of the bot is the need to hardcode in channel and user codes. Unfortunately, this means that the bot cannot be easily distributed outside of the current setting although for our current workflow, it has proved to be effective. 

As I said previously this bot is written in Python and in order to maintain the code, or understand some of the design decisions, a strong knowledge of Python is needed. One of Python's many pros is readability, so hopefully much of the code can be read even by a non-python developer.

It should be noted that due to Michael's lack of experience, this project is not structured correctly to convention. Traditionally you don't put in an `src` directory.


## Features 

While the SlackBot has two main features, namely assigning testers and tracking absences, only the second involves some kind of user interaction. All SlackBot commands begin with `\ibot` and can be posted for results in most channels. The message will be auto deleted and a response will be direct messaged to the user.

`\ibot (help)` will give a list of valid commands with some documentation attached. This help message sits in its own function in src/main.py and should be updated with all SlackBot command changes

## Setup
There are several components you need to run a copy/deploy SlackBot

- Python 3.4.3 or above
- The Slack API Token saved into your environment variables as SLACK_API_TOKEN. This can be found on deviis
- A database from running 
```
py src/slackbot/db_setup/sql_declarations.py
py src/slackbot/db_setup/populate_database.py
``` 
or by copying the current or a backup from deviis

Create a folder in the top level project directory called __logs__

There are two primary methods of setting up the slackbot

First there is running the command

`py setup.py install`

from Powershell or Command Prompt in the project directory. That will install all needed packages.

The second is to manually install all needed python packages manually. I don't recommend this method but it is possible. Just install all packages into your python that are listed in the setup.py file with an entry labeled with __dependency__. 

From here, in order to run the server, all you need to do call `py src/main.py` and this will activate the SlackBot.

### NOTE

I don't know what effect running multiple instances of SlackBot does so in general if I'm running tests on changes locally I will stop the SlackBot on deviis.

## Maintenance

### Tests

If code isn't working the way it is expected to, first run the prebuilt tests as a place to start

From the top level project directory run
`py setup.py test`
This will auto discover and run all tests in src/tests.

## Database
The SlackBot makes use of an ORM call SQLAlchemy paired with SQLite database named `sql_bot.db` although of course that name can be changed at anytime. Most database related scripts will be found at `src\slackbot\db_setup`.

### Database changes
The database model can be changed at any time to suit current needs. a file named `__alter_users.py` should be found with the rest of the database scripts. This can be used to drop users from the table. <span style="color:red">Should only be used by people that know what they're doing. You can also edit the SQL if you feel confident.</span>

### Migrations
I am using a tool called alembic, made for SQLAlchemy for database migrations. All changes should first be made to the respective models in the `sql_declarations.py` file. Next create a migration script with alembic like so
```powershell
py -3.4 C:\Python34\Scripts\alembic.exe revision -m "My Revision Message"
```
That will create a migrations script in `alembic\versions` folder. See existing for details or read documentation :)

After you have created your migration script, run the command

```powershell
py -3.4 C:\Python34\Scripts\alembic.exe upgrade head
```