from productscraper import handle_request

async def on_request(context):
    req = context.request
    params = dict(req.url.params)

    class Req:
        def __init__(self, params):
            self.params = params

    data, status = handle_request(Req(params))
    return Response(
        json.dumps(data),
        status=status,
        headers={"Content-Type": "application/json"}
    )
