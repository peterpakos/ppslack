# -*- coding: utf-8 -*-
"""This module implements sending Slack messages

Copyright (c) 2019-2023 Peter Pakos. All rights reserved.

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

import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ppconfig import Config

log = logging.getLogger(__name__)


class Slack:
    def __init__(self):
        try:
            self._config = Config('ppslack')
            self._slack_key = self._config.get('slack_key')
            self._email_domain = self._config.get('email_domain')
        except Exception as e:
            log.debug(e)
            try:
                self._config = Config('ppmail')
                self._slack_key = self._config.get('slack_key')
                self._email_domain = self._config.get('email_domain')
            except Exception as e:
                log.debug(e)
                raise Exception('Config file not found')
            else:
                log.debug('Config file found: ppmail')
        else:
            log.debug('Config file found: ppslack')

        self._client = WebClient(self._slack_key)
        self._users = {}
        self._channels = {}

    @property
    def users(self):
        if not self._users:
            try:
                r = self._client.users_list()
            except SlackApiError:
                raise

            for user in r["members"]:
                if not user['deleted'] and not user['is_bot'] and user['id'] != 'USLACKBOT':
                    self._users[user['name']] = user

            log.debug('Active members: %s' % len(self._users))

        return self._users

    def find_user_by_email(self, email):
        for user in self.users.values():
            if user['profile']['email'] == email:
                log.debug('Found user with email %s: %s' % (email, user['name']))
                return user

        return

    @property
    def channels(self):
        if not self._channels:
            try:
                r = self._client.conversations_list(limit=1000)
            except SlackApiError:
                raise

            for channel in r['channels']:
                if not channel['is_archived'] and not channel['is_private']:
                    self._channels[channel['name']] = channel

            log.debug('Public channels: %s' % len(self._channels))

        return self._channels

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
                user = self.find_user_by_email(recipient)
                if user:
                    recipient_id = user['id']
            elif str(recipient).startswith('@'):
                user = self.users[str(recipient).strip('@')]
                if user:
                    recipient_id = user['id']
            else:
                if recipient in self.channels:
                    channel = self.channels[recipient]
                    recipient_id = channel['id']
                elif recipient in self.users:
                    user = self.users[recipient]
                    recipient_id = user['id']

            if not recipient_id:
                failed += 1
                log.error('User or channel %s not found' % recipient)
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

                        try:
                            r = self._client.chat_postMessage(
                                channel=recipient_id,
                                text=to_print,
                                username=sender,
                                link_names=True
                            )
                        except SlackApiError:
                            raise

                        if not r.get('ok'):
                            failed += 1

                        to_print = []
                        length = 0
            else:
                try:
                    r = self._client.chat_postMessage(
                        channel=recipient_id,
                        text=text,
                        username=sender,
                        link_names=True
                    )
                except SlackApiError:
                    raise

                if not r.get('ok'):
                    failed += 1

        return False if failed else True
