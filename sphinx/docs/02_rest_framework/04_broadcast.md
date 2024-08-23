# Broadcast

You can handle the broadcast in the `ActionHandler` as well.

See the below example first. As you can see this example, you can pass the data to the event method when you pass the arguments in the `async_action`.

```python
class ChildConsumer(AsyncAPIActionHandler):
    permission_classes = (IsAuthenticated,)

    @async_action(
        mode='broadcast',
        broadcast_type='test.called',
    )
    async def test_async_action(self, **kwargs):
        return {'test': 'content'}, 200

class ParentConsumer(AsyncAPIConsumer):
    group_send_lookup_kwargs = 'group_id'

    routepatterns = [
        path(
            'test_async_child_route/',
            ChildConsumer.as_aaah(),
        ),
    ]

    async def test_called(self, event):
        await self.send_json(event)
```

The available arguments about broadcast are here;

- `mode` : str
  - The available modes are `['response', 'broadcast', 'none']`
    - `'response'`: Send the response to the user sending this action
    - `'broadcast'`: Broadcast the response to the users in the specific group
    - `'none'`: Do nothing at all
- `broadcast_type` : str
  - The type for broadcasting. If you specify this variable, use `'_general.broadcast'`
- `send_response_in_broadcast` : bool
  - Whether to send the response in broadcast mode, default to True
