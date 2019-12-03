# -*- coding: utf-8 -*-
"""This module implements sending messages via Slack

Author: Peter Pakos <peter@pakos.uk>

Copyright (C) 2019 Peter Pakos

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import print_function
from ppconfig import Config

import os
import logging
from slackclient import SlackClient

log = logging.getLogger(__name__)


class Slack(object):
    def __init__(self):
        self._app_name = os.path.splitext(__name__)[0].lower()

        try:
            self._config = Config(self._app_name)
        except Exception:
            raise

        try:
            self._slack_key = self._config.get('slack_key')
            self._email_domain = self._config.get('email_domain')
        except Exception:
            raise

        self._slack_client = SlackClient(self._slack_key)

    def send(self, sender, recipients, subject, message, code=False):
        if type(recipients) is not list:
            recipientsl = []
            if recipients:
                recipientsl.append(recipients)
            recipients = recipientsl

        if subject:
            subject = '*%s*\n' % subject.strip()

        if code:
            message = "```%s```" % message

        text = '%s%s' % (subject, message)

        if code:
            text = text.splitlines(True)

        failed = 0

        for recipient in recipients:
            recipient_id = None

            if '@%s' % self._email_domain in recipient:
                r = self._slack_client.api_call('users.lookupByEmail', email=recipient)
                if r.get('ok'):
                    recipient_id = r.get('user').get('id')
            elif str(recipient).startswith('@'):
                r = self._slack_client.api_call('users.lookupByEmail',
                                                email=str(recipient).strip('@') + '@%s' % self._email_domain)
                if r.get('ok'):
                    recipient_id = r.get('user').get('id')
            else:
                if str(recipient).startswith('#'):
                    recipient = str(recipient).lstrip('#')
                recipient_id = self._find_channel_id(recipient)

            if not recipient_id:
                failed += 1
                log.error('Slack user %s not found' % recipient)
                continue

            if code:
                to_print = []
                length = 0

                for i, line in enumerate(text):
                    to_print += text[i]
                    length += len(line)

                    if i == (len(text) - 1) or (length + len(text[i+1])) > 3800:
                        to_print = ''.join(to_print)

                        if not str(to_print).startswith('```') and not (subject and subject in to_print):
                            to_print = '```' + to_print
                        if not str(to_print).endswith('```'):
                            to_print = to_print + '```'

                        r = self._slack_client.api_call(
                            'chat.postMessage',
                            username=sender,
                            channel=recipient_id,
                            text=to_print,
                            as_user=False,
                            link_names=True
                        )

                        if not r.get('ok'):
                            failed += 1

                        to_print = []
                        length = 0
            else:
                r = self._slack_client.api_call(
                    'chat.postMessage',
                    username=sender,
                    channel=recipient_id,
                    text=text,
                    as_user=False,
                    link_names=True
                )

                if not r.get('ok'):
                    failed += 1

        return False if failed else True

    def _find_channel_id(self, channel):
        r = self._slack_client.api_call('channels.list')
        channels = r.get('channels')
        for c in channels:
            if c.get('name') == channel:
                channel_id = c.get('id')
                log.debug('Public channel name: %s, ID: %s' % (c.get('name'), c.get('id')))
                return channel_id

        r = self._slack_client.api_call('groups.list')
        private_channels = r.get('groups')
        for c in private_channels:
            if c.get('name') == channel:
                channel_id = c.get('id')
                log.debug('Private channel name: %s, ID: %s' % (c.get('name'), c.get('id')))
                return channel_id

        return False
