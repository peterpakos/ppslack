# ppslack
Tool to send messages via Slack

PyPI package: [ppslack](https://pypi.org/project/ppslack/)

If you spot any problems or have any improvement ideas then feel free to open
an issue. I will be glad to look into it for you.

## Installation
The tool is available in PyPI and can be installed using pip:
```
$ pip install --user ppslack
$ ppslack --help
```

Once installed, a command line tool `ppslack` should be available in your
system's PATH.

## Configuration
By default, the tool reads its configuration from `~/.config/ppslack` file (the
location can be overridden by setting environment variable `XDG_CONFIG_HOME`).

The config file should look like this:
```
[default]
slack_key=xxx
email_domain=example.com
```

## Usage - Help
```
$ ppslack --help
usage: ppslack [--version] [--help] [--debug] [--verbose] [-f SENDER] -t RECIPIENTS [RECIPIENTS ...] [-s SUBJECT] [-S] [-H]

Tool to send messages via Slack

optional arguments:
  --version             show program's version number and exit
  --help                show this help message and exit
  --debug               debugging mode
  --verbose             verbose debugging mode
  -f SENDER, --from SENDER
                        sender
  -t RECIPIENTS [RECIPIENTS ...], --to RECIPIENTS [RECIPIENTS ...]
                        recipient
  -s SUBJECT, --subject SUBJECT
                        subject
  -S, --slack           Slack message (keeping for backward compatibility)
  -H, --code            send code block
```

## Usage - CLI
```
$ echo 'The king is dead, long live the king!' \
  | ppslack -Hf 'Jon Snow' \
  -t 'arya.stark@winterfell.com' \
  -s 'Re: secret message'
```

## Usage - Python module
```
from ppslack import Slack

slack = Slack()

status = slack.send(
    sender='Jon Snow',
    recipients=['arya.stark@winterfell.com'],
    subject='Re: secret message',
    message='The king is dead, long live the king!',
    code=True
)
```
