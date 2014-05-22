#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""An IRC bot that acts as a secretary

So far it only logs channels messages, but I have plans to make it make minutes
of meetings, send mails, todo lists, etc.

The known commands are:
    help -- A list of available commands
    info -- Tell what I'm doing
    channel join <channel> -- Join a channel
    channel leave <channel> -- Leave a channel
    log start <channel>
    log stop <channel>
    bye -- Let the secretary cease to exist.
"""

from datetime import datetime
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr


class SecretaryBot(SingleServerIRCBot):
    def __init__(self, boss, server, port=6667):
        nickname = boss.rstrip('_') + '_sec'
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.boss = boss 
        self.logging = {}

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        self._report("Hi boss, I'm here to assist you. Type 'help' to view available commands.")

    def on_privmsg(self, c, e):
        self.do_command(e)

    def on_privnotice(self, c, e):
        self.do_command(e)

    def on_pubmsg(self, c, e):
        self._log_event(e)

    def on_action(self, c, e):
        self._log_event(e)

    def do_command(self, e):
        who = e.source().split('!')[0]
        cmd = e.arguments()[0]
        if who != self.boss:
            self.connection.notice(who, "I'm not allowed to talk with you")
        else:
            if cmd.startswith('channel'):
                self._channel_action(cmd)
            elif cmd.startswith('log'):
                self._log_action(cmd)
            elif cmd == 'help':
                self._helpmsg()
            elif cmd == 'info':
                self._info()
            elif cmd == "thanks":
                #self._finish_tasks()
                #self.die()
                pass
            elif cmd == "bye":
                self.die()
            else:
                self._report("Not understood: " + cmd)
    
    def _report(self, msg):
        self.connection.privmsg(self.boss, msg)

    def _channel_action(self, cmd):
        parts  = cmd.split()
        if len(parts) < 3:
            self._report("You must indicate at least one channel for this action.")
            return
        action = parts[1]
        channels = parts[2:]
        if action not in ('join', 'leave'):
            self._report('Unknown action for channels command')
            self._report('Usage: channel <join|leave> <channel> ...')
        for channel in channels:
            if action == 'join':
                self._report('Joining channel %s...' % channel)
                self.connection.join(channel)
            elif action == 'leave':
                self._report('Leaving channel %s...' % channel)
                self.connection.part(channel)

    def _log_action(self, cmd):
        parts  = cmd.split()
        if len(parts) < 3:
            self._report("You must indicate at least one channel for this action.")
            return
        action = parts[1]
        channels = parts[2:]

        msgs = {
            'start': 'Started logging as request of <someone>',
            'stop': 'Stoped logging as request of <someone>',
            'pause': 'Paused logging as request of <someone>',
            'resume': 'Resumed logging as request of <someone>',
        }

        today = datetime.today().strftime('%Y-%m-%d')
        now = datetime.now().strftime('%H:%M')
        for channel in channels:
            if action == 'start':
                if channel not in self.logging:
                    fname = '/tmp/%s-%s.log' % (today, channel)
                    self.logging[channel] = {'filename': fname, 'file': open(fname, 'a')}
                    self._log(channel, '----- Started logging at %s -----' % now)
                    self.connection.action(channel, 'started recording activity in this channel')
                    self._report('Start logging %s to %s' % (channel, fname))
            elif action == 'stop':
                if channel in self.logging:
                    self._log(channel, '----- Stoped logging at %s -----' % now)
                    fname = self.logging[channel]['filename']
                    del(self.logging[channel])
                    self.connection.action(channel, 'stoped recording activity in this channel')
                    self._report('Stoped logging %s to %s' % (channel, fname))

    def _info(self):
        self._report('------')
        self._report('Working in the following channels:')
        for channel in self.channels:
            logging = channel in self.logging
            self._report('%s\t Log: %s - Ask: %s' % (channel, str(logging), 'N/A'))
        self._report('------')

    def _log_event(self, e):
        fmt = {
            'pubmsg': '[%s] <%s> %s',
            'action': '[%s] \t* %s %s',
        }
        channel = e.target()
        if channel in self.logging:
            who = e.source().split('!')[0]
            what = e.arguments()[0]
            when = datetime.now().strftime('%H:%M')
            msg = fmt[e.eventtype()] % (when, who, what)
            self._log(channel, msg)

    def _log(self, channel, msg):
        self.logging[channel]['file'].write(msg + '\n')


def main():
    import sys
    if len(sys.argv) < 3:
        print "Usage: irc-secretary <server[:port]> <user>"
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print "Error: Erroneous port."
            sys.exit(1)
    else:
        port = 6667
    user = sys.argv[2]

    print 'starting secretary bot'
    bot = SecretaryBot(user, server, port)
    bot.start()

if __name__ == "__main__":
    main()
