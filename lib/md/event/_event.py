import typing
import psr.event

import md.python


__all__ = (
    # Type
    'EventCallbackType',
    'EventType',
    # Implementation
    'StoppableEvent',
    'Dispatcher',
)


# Type
EventCallbackType = typing.Callable[[object], typing.Any]
EventType = typing.Union[str, object]


# Implementation
class StoppableEvent(psr.event.StoppableEventInterface):  # abstract event
    def __init__(self) -> None:
        self._is_propagation_stopped = False

    def stop_propagation(self) -> None:
        self._is_propagation_stopped = True

    def is_propagation_stopped(self) -> bool:
        return self._is_propagation_stopped


class Dispatcher(psr.event.EventDispatcherInterface):
    def __init__(self) -> None:
        self._subscription_map: typing.Dict[str, typing.List[typing.Tuple[int, EventCallbackType]]] = {}
        self._sorted_subscription_map: typing.Dict[str, typing.List[typing.Tuple[int, EventCallbackType]]] = {}

    def subscribe(self, event: EventType, handler: EventCallbackType, priority: int = 0) -> None:
        event_class = md.python.reference(definition=event, explicit=False)
        if event_class in self._sorted_subscription_map:
            del self._sorted_subscription_map[event_class]

        if event_class not in self._subscription_map:
            self._subscription_map[event_class] = []

        self._subscription_map[event_class].append((priority, handler))

    def unsubscribe(self, event: EventType, handler: EventCallbackType) -> None:
        """ unsubscribes all handler subscriptions, even with different priority """
        event_class = md.python.reference(definition=event, explicit=False)
        if event_class not in self._subscription_map:
            assert event_class not in self._sorted_subscription_map
            return

        self._subscription_map[event_class] = list(filter(
            lambda subscription: subscription[1] is not handler, self._subscription_map[event_class]
        ))

        if 0 == len(self._subscription_map[event_class]):
            del self._subscription_map[event_class]

        if event_class in self._sorted_subscription_map:
            del self._sorted_subscription_map[event_class]

    def dispatch(self, event: EventType) -> EventType:
        event_class = event
        if not isinstance(event, str):
            event_class = md.python.reference(definition=event.__class__, explicit=False)

        if event_class not in self._subscription_map:
            return event

        subscription_map_length = len(self._subscription_map[event_class])
        assert 0 != subscription_map_length

        if event_class not in self._sorted_subscription_map:
            self._sorted_subscription_map[event_class] = self._subscription_map[event_class]
            if subscription_map_length > 1:
                self._sorted_subscription_map[event_class].sort(
                    key=lambda subscription: subscription[0],
                    reverse=True
                )

        if isinstance(event, psr.event.StoppableEventInterface):
            for priority, handler in self._sorted_subscription_map[event_class]:
                handler(event)
                if event.is_propagation_stopped():
                    break
        else:
            for priority, handler in self._sorted_subscription_map[event_class]:
                handler(event)

        return event

    def __repr__(self) -> str:
        return 'Dispatcher()'
