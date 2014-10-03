from collections import defaultdict
import sys
PY2 = sys.version_info[0] == 2

if not PY2:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty

from six import with_metaclass


class Singleton(type):
    """
    Metaclass to ensure that a class instance is only instantiated once.
    Subsequent instantiations will just return the first instance.
    """
    instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance


class PubSubTransport(with_metaclass(Singleton, object)):
    """
    Singleton object used to coordinate communications between multiple Pubsub objects.
    """

    def __init__(self):
        # Container mapping channel names to the subscribers.
        self.callbacks = defaultdict(list)

    def clear(self):
        """
        TODO
        """
        pass

    def subscribe(self, pubsub, *args):
        """
        Subscribe to the named channels.
        """
        for channel in args:
            self.callbacks[channel].append(pubsub)

            # Push the subscribe message back down to the pubsub instance.
            pubsub.handle_message(channel,
                                  self.num_subscriptions(pubsub),
                                  'subscribe')

    def num_subscriptions(self, pubsub):
        """
        Get the number of channels the given pubsub instance is subscribed to.
        """
        return len([x for x in self.callbacks.values() if pubsub in x])

    def unsubscribe(self, pubsub, *args):
        """
        Unsubscribe from the named channels, or if no channels are specified, unsubscribe from all channels.
        """
        if len(args) == 0:
            # Unsubscribe from all channels.
            for channel, channel_list in self.callbacks.items():
                try:
                    channel_list.remove(pubsub)
                except ValueError:
                    pass
                else:
                    # Push the unsubscribe message back down to the pubsub instance.
                    pubsub.handle_message(channel,
                                          self.num_subscriptions(pubsub),
                                          'unsubscribe')
        else:
            # Unsubscribe from specified channels.
            for channel in args:
                try:
                    self.callbacks[channel].remove(pubsub)
                except ValueError:
                    pass

        # Push the unsubscribe message back down to the pubsub instance.
        pubsub.handle_message(channel,
                              self.num_subscriptions(pubsub),
                              'unsubscribe')

    def publish(self, channel, data):
        """
        Push the message out to each subscribed pubsub instance.
        """
        for pubsub in self.callbacks[channel]:
            pubsub.handle_message(channel, data, 'message')


class MockPubSub(object):
    def __init__(self,
                 ignore_subscribe_messages=False,
                 **kwargs):
        self.ignore_subscribe_messages = ignore_subscribe_messages
        self.reset()

    def reset(self):
        self.channels = {}
        self.patterns = {}
        self.message_queue = Queue()
        self.transport = PubSubTransport()

    def close(self):
        """
        "Close" the pubsub. For the mock, we just unsubscribe from everything.
        """
        self.transport.unsubscribe(self)

    def handle_message(self, channel, data, _type, pattern=None):
        """
        Handle a message recieved on a channel we are subscribed to.
        """
        self.message_queue.put({'channel': channel,
                                'data': data,
                                'type': _type,
                                'pattern': pattern})


    @property
    def subscribed(self):
        """
        Return if we are subscribed to any channels.
        """
        return self.transport.num_subscriptions(self) > 0

    def psubscribe(self, *args, **kwargs):
        """
        TODO
        """
        pass

    def punsubscribe(self, *args):
        """
        TODO
        """
        pass

    def subscribe(self, *args, **kwargs):
        """
        Subscribe this pubsub to the specified channels.
        """
        self.transport.subscribe(self, *args)

    def unsubscribe(self, *args):
        """
        Unsubscribe this pubsub from the specified channels.
        If no channels are specified, remove this pubsub from all channels.
        """
        self.transport.unsubscribe(self, *args)

    def listen(self):
        """
        TODO
        """
        pass

    def get_message(self, ignore_subscribe_messages=False):
        """
        Get the next message recieved off the channel.
        If no message is waiting or recieved within the timeout, return None.
        If ignore_subscribe_messages is True, and a subscribe or unsubscribe is recieved, return None.
        """
        message = None
        try:
            message = self.message_queue.get_nowait()

            if ignore_subscribe_messages and message['type'] in ['subscribe', 'unsubscribe']:
                message = None
        except Empty:
            pass
        return message

