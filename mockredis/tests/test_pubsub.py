"""
Tests for pubsub don't yet support verification against redis-server.
"""
from nose.tools import eq_, ok_
from mockredis.tests.fixtures import setup


class TestRedisPubSub(object):
    def setup(self):
        setup(self)

    def test_publish(self):
        """
        Test that we can subscribe to a channel, publish to it, and receive the messages back.
        """
        channel = 'ch#1'
        msg = 'test message{}'

        # Subscribe.
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)

        # Publish.
        self.redis.publish(channel, msg.format('2'))

        eq_(pubsub.get_message(), {'channel': channel,
                                   'data': 1,
                                   'type': 'subscribe',
                                   'pattern': None})

        eq_(pubsub.get_message(), {'channel': channel,
                                   'data': msg.format('2'),
                                   'type': 'message',
                                   'pattern': None})

        # Unsubscribe.
        pubsub.unsubscribe(channel)

        # Make sure we no longer get messages on the channel.
        self.redis.publish(channel, msg.format('3'))

        eq_(pubsub.get_message(), {'channel': channel,
                                   'data': 0,
                                   'type': 'unsubscribe',
                                   'pattern': None})

        eq_(pubsub.get_message(), None)

    def test_ignore_subscribe_messages(self):
        """
        Test that calls to get_message properly return None for subscribe/unsubscribe when ignore_subscribe_messages=True.
        """
        channel = 'ch#1'
        msg = 'test message{}'

        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)

        self.redis.publish(channel, msg.format('2'))

        eq_(pubsub.get_message(ignore_subscribe_messages=True), None)

        eq_(pubsub.get_message(ignore_subscribe_messages=True), {'channel': channel,
                                                                 'data': msg.format('2'),
                                                                 'type': 'message',
                                                                 'pattern': None})

        pubsub.unsubscribe(channel)

        eq_(pubsub.get_message(ignore_subscribe_messages=True), None)

        self.redis.publish(channel, msg.format('3'))

        eq_(pubsub.get_message(ignore_subscribe_messages=True), None)

    # def test_subscribed(self):
    #     """
    #     Test that the subscribed property is accurate.
    #     """
    #
    #     channel = 'ch#1'
    #
    #     pubsub = self.redis.pubsub()
    #
    #     eq_(pubsub.subscribed, False)
    #
    #     pubsub.subscribe(channel)
    #
    #     eq_(pubsub.subscribed, True)
    #
    #     pubsub.unsubscribe()
    #
    #     eq_(pubsub.subscribed, False)

    def test_multiple_unsubscribe(self):
        pubsub = self.redis.pubsub()

        channels = ['1', '2', '3']

        for channel in channels:
            pubsub.subscribe(channel)

        for channel in channels:
            eq_(pubsub.get_message(), {'channel': channel,
                                       'data': int(channel),
                                       'type': 'subscribe',
                                       'pattern': None})

        pubsub.unsubscribe()

        import time
        time.sleep(1)

        channels_unsubscribed = []
        num_channels_left = []

        for channel in channels:
            message = pubsub.get_message()

            if message is not None:
                channels_unsubscribed.append(message['channel'])
                num_channels_left.append(message['data'])

        eq_(num_channels_left, [2, 1, 0])

        ok_('1' in channels_unsubscribed)
        ok_('2' in channels_unsubscribed)
        ok_('3' in channels_unsubscribed)

    def test_patterns(self):
        pubsub = self.redis.pubsub()

        pubsub.psubscribe('h?llo')

        import time
        time.sleep(1)

        eq_(pubsub.get_message(), {'channel': 'h?llo',
                                   'data': 1,
                                   'type': 'psubscribe',
                                   'pattern': None})

        self.redis.publish('hello', 'there')

        time.sleep(1)

        eq_(pubsub.get_message(), {'channel': 'hello',
                                   'data': 'there',
                                   'type': 'pmessage',
                                   'pattern': 'h?llo'})

        pubsub.punsubscribe()

        time.sleep(1)

        eq_(pubsub.get_message(), {'channel': 'h?llo',
                                   'data': 0,
                                   'type': 'punsubscribe',
                                   'pattern': None})