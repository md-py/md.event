# Documentation
## Overview

md.event is [psr.event](../psr.event/) contract implementation component 
that provides mediator pattern API to dispatch events.
Inspired by `symfony/event-dispatcher`.

## Architecture overview

[![Architecture overview][architecture-overview]][architecture-overview]

## Installation

```sh
pip install md.event --index-url https://source.md.land/python/
```

## Usage example

```python3
#!/usr/bin/env python3
import md.event


class ClientRegistrationFinished(md.event.StoppableEvent):
    def __init__(self, client: int) -> None:
        super().__init__()
        self.client = client


class SendWelcomeEmailAfterClientRegistration:
    def after_client_registration(self, event: ClientRegistrationFinished) -> None:
        print('Welcome email sent to client', event.client)
    
        
class AssignManagerAfterClientRegistration:
    def after_client_registration(self, event: ClientRegistrationFinished) -> None:
        print('Manager assigned to client', event.client)



if __name__ == '__main__':
    # arrange
    event_dispatcher = md.event.Dispatcher()
    event_dispatcher.subscribe(
        event=ClientRegistrationFinished,
        handler=AssignManagerAfterClientRegistration().after_client_registration,
        priority=10,
    )
    event_dispatcher.subscribe(
        event=ClientRegistrationFinished,
        handler=SendWelcomeEmailAfterClientRegistration().after_client_registration,
    )
    
    # act
    event_dispatcher.dispatch(event=ClientRegistrationFinished(client=42))
```

[architecture-overview]: _static/architecture.class-diagram.png
