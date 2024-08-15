# Action Handler

In this section, we introduce the `ActionHandler`.
As mentioned before, the `ActionHandler` is the original class for handling the action in rest_framework_channels.
The base class is `AsyncActionHandler` in `rest_framework_channels.handlers`.
All `ActionHandler`s and `Consumer`s in rest_framework_channels are inherited from it.

`AsyncActionHandler` will summarize its actions by itself when the instance (Async API Action Handler; the abbreviation is `aaah` which is similar as `asgi` in channels and `view` in django) is created.

## AsyncAPIActionHandler

We guess you will not take care the `AsyncActionHandler` due to the core class. Instead, you may be interested in `AsyncAPIActionHandler` inherited from `AsyncActionHandler`.
`AsyncAPIActionHandler` handles with actions and permissions mainly.
If you have already used [rest_framework](https://www.django-rest-framework.org/), it's very easy to integrate the permission mechanism in rest_framework into your websocket project.
Because `AsyncAPIActionHandler`'s interface is almost same as `APIView` in rest_framework.
