""" https://github.com/symfony/event-dispatcher/blob/master/Tests/DispatcherTest.php """

import unittest.mock
import pytest

import md.event


class Event:
    pass


class StoppableEvent(Event, md.event.StoppableEvent):
    pass


module_name = Event.__module__


# Subscribe tests:
@pytest.mark.parametrize("priority", [-128, 0, 128])
def test_initial_subscribe(priority: int) -> None:
    # arrange
    handler = unittest.mock.Mock()

    # act & assert
    event_dispatcher = md.event.Dispatcher()

    assert len(event_dispatcher._subscription_map) == 0
    assert len(event_dispatcher._sorted_subscription_map) == 0

    event_dispatcher.subscribe(event=Event, handler=handler, priority=priority)

    assert len(event_dispatcher._subscription_map) == 1
    assert module_name + '.Event' in event_dispatcher._subscription_map
    assert len(event_dispatcher._subscription_map[module_name + '.Event']) == 1
    assert len(event_dispatcher._sorted_subscription_map) == 0
    assert (priority, handler) == event_dispatcher._subscription_map[module_name + '.Event'][0]


def test_second_subscribe() -> None:
    # arrange
    handler = unittest.mock.Mock()
    handler2 = unittest.mock.Mock()

    # act & assert
    event_dispatcher = md.event.Dispatcher()
    event_dispatcher.subscribe(event=Event, handler=handler, priority=0)
    event_dispatcher.subscribe(event=Event, handler=handler2, priority=1)

    assert len(event_dispatcher._subscription_map) == 1
    assert module_name + '.Event' in event_dispatcher._subscription_map
    assert len(event_dispatcher._subscription_map[module_name + '.Event']) == 2
    assert len(event_dispatcher._sorted_subscription_map) == 0
    assert (1, handler2) == event_dispatcher._subscription_map[module_name + '.Event'][1]


# Unsubscribe tests:
def test_unsubscribe_nothing():
    # arrange
    handler = unittest.mock.Mock()

    # act & assert
    event_dispatcher = md.event.Dispatcher()
    assert 0 == len(event_dispatcher._subscription_map)

    event_dispatcher.unsubscribe(event=Event, handler=handler)
    assert 0 == len(event_dispatcher._subscription_map)


def test_unsubscribe_one_subscription():
    # arrange
    handler = unittest.mock.Mock()

    # act & assert
    event_dispatcher = md.event.Dispatcher()
    event_dispatcher.subscribe(event=Event, handler=handler)
    event_dispatcher.unsubscribe(event=Event, handler=handler)

    assert 0 == len(event_dispatcher._subscription_map)
    assert 0 == len(event_dispatcher._sorted_subscription_map)


def test_unsubscribe_few_subscription():
    # arrange
    handler = unittest.mock.Mock()
    handler2 = unittest.mock.Mock()

    # act & assert
    event_dispatcher = md.event.Dispatcher()
    event_dispatcher.subscribe(event=Event, handler=handler)
    event_dispatcher.subscribe(event=Event, handler=handler2)
    event_dispatcher.unsubscribe(event=Event, handler=handler)

    assert 1 == len(event_dispatcher._subscription_map)
    assert 0 == len(event_dispatcher._sorted_subscription_map)

    assert handler2 == event_dispatcher._subscription_map[module_name + '.Event'][0][1]


# Dispatch tests:
@pytest.mark.parametrize("event", [Event(), StoppableEvent()])
def test_dispatch_one_handler(event: Event) -> None:
    # arrange
    handler = unittest.mock.Mock(return_value=event)

    # act
    event_dispatcher = md.event.Dispatcher()
    event_reference = module_name + '.' + event.__class__.__qualname__
    event_dispatcher.subscribe(event=event_reference, handler=handler)
    event_ = event_dispatcher.dispatch(event=event)

    # assert
    handler.assert_called_with(event)
    assert event_ == event

    assert event_dispatcher._sorted_subscription_map[event_reference] == event_dispatcher._subscription_map[event_reference]


@pytest.mark.parametrize("event", [Event(), StoppableEvent()])
def test_dispatch_few_handler(event: Event) -> None:
    # arrange
    handler_call_list = []

    def handler(event_: Event) -> None:
        assert event_ == event
        handler_call_list.append(1)

    def handler2(event_: Event) -> None:
        assert event_ == event
        handler_call_list.append(2)

    # act
    event_dispatcher = md.event.Dispatcher()
    event_reference = module_name + '.' + event.__class__.__qualname__
    event_dispatcher.subscribe(event=event_reference, handler=handler2, priority=128)
    event_dispatcher.subscribe(event=event_reference, handler=handler, priority=0)
    event_ = event_dispatcher.dispatch(event=event)

    # assert
    assert event_ == event
    assert handler_call_list == [2, 1]
    assert event_dispatcher._sorted_subscription_map[event_reference][0][1] == handler2
    assert event_dispatcher._sorted_subscription_map[event_reference][1][1] == handler


def test_dispatch_few_handler_stop_event_propagation() -> None:
    # arrange
    event = StoppableEvent()

    def handler(event_: StoppableEvent) -> None:
        assert event_ == event
        event.stop_propagation()

    def handler2() -> None:
        assert False, 'Handler must not be called when higher priority handler stop event propagation'

    # act
    event_dispatcher = md.event.Dispatcher()
    event_reference = module_name + '.' + event.__class__.__qualname__
    event_dispatcher.subscribe(event=event_reference, handler=handler2, priority=-128)
    event_dispatcher.subscribe(event=event_reference, handler=handler, priority=0)
    event_ = event_dispatcher.dispatch(event=event)

    # assert
    assert event_ == event
    assert event_dispatcher._sorted_subscription_map[event_reference][0][1] == handler
    assert event_dispatcher._sorted_subscription_map[event_reference][1][1] == handler2


@pytest.mark.parametrize("event", [Event(), StoppableEvent()])
def test_dispatch_and_subscribe(event: Event) -> None:
    # arrange
    handler_call_list = []

    def handler(event_: Event) -> None:
        handler_call_list.append(1)
        assert event_ == event

    def handler2(event_: Event) -> None:
        handler_call_list.append(2)
        assert event_ == event

    # act
    event_dispatcher = md.event.Dispatcher()
    event_reference = module_name + '.' + event.__class__.__qualname__
    event_dispatcher.subscribe(event=event_reference, handler=handler, priority=0)

    # assert event_dispatcher._sorted_subscription_map[event_reference][0][1] == handler
    # assert len(event_dispatcher._sorted_subscription_map[event_reference]) == 0

    event_ = event_dispatcher.dispatch(event=event)
    assert event_ == event

    assert event_reference in event_dispatcher._sorted_subscription_map
    assert 1 == len(event_dispatcher._sorted_subscription_map[event_reference])

    event_dispatcher.subscribe(event=event_reference, handler=handler2, priority=128)

    assert event_reference not in event_dispatcher._sorted_subscription_map

    event_ = event_dispatcher.dispatch(event=event)

    # assert
    assert event_ == event
    assert event_dispatcher._sorted_subscription_map[event_reference][0][1] == handler2
    assert event_dispatcher._sorted_subscription_map[event_reference][1][1] == handler
    assert [1, 2, 1] == handler_call_list


@pytest.mark.parametrize("event", [Event(), StoppableEvent()])
def test_dispatch_and_unsubscribe(event: Event) -> None:
    # arrange
    handler_call_list = []

    def handler(event_: Event) -> None:
        handler_call_list.append(1)
        assert event_ == event

    # act
    event_dispatcher = md.event.Dispatcher()
    event_reference = module_name + '.' + event.__class__.__qualname__
    event_dispatcher.subscribe(event=event_reference, handler=handler, priority=0)

    # assert event_dispatcher._sorted_subscription_map[event_reference][0][1] == handler
    # assert len(event_dispatcher._sorted_subscription_map[event_reference]) == 0

    event_ = event_dispatcher.dispatch(event=event)
    assert event_ == event

    event_dispatcher.unsubscribe(event=event_reference, handler=handler)

    assert event_reference not in event_dispatcher._sorted_subscription_map

    event_ = event_dispatcher.dispatch(event=event)

    # assert
    assert event_ == event
    assert 0 == len(event_dispatcher._sorted_subscription_map)
    assert [1] == handler_call_list


@pytest.mark.parametrize("event", [Event(), StoppableEvent()])
def test_dispatch_no_handler(event: Event) -> None:
    # act
    event_dispatcher = md.event.Dispatcher()
    event_ = event_dispatcher.dispatch(event=event)

    # assert
    assert event_ == event
    assert len(event_dispatcher._sorted_subscription_map) == 0
    assert len(event_dispatcher._subscription_map) == 0


def test_repr() -> None:
    # act
    event_dispatcher = md.event.Dispatcher()

    # assert
    assert isinstance(repr(event_dispatcher), str)
