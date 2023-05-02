from mitmproxy import ctx
from mitmproxy import http
import re
import json

class FilterJSONRPCMethod:
    def __init__(self):
        self.num = 0

    def load(self, loader):
        loader.add_option(
            name="methods",
            typespec=str,
            default="",
            help="Methods to whitelist",
        )

    def request(self, flow):
        json_dump = json.loads(flow.request.content)
        is_filtered = False
        if ctx.options.methods:
            _allmethods = json.loads(ctx.options.methods)
            for _method in _allmethods:
                if _method.strip() != '':
                    if re.search(_method, json_dump['method']) is not None:
                        is_filtered = True
                        break

        if is_filtered:
            status = 200
            content = {
                    "jsonrpc": "2.0",
                    "id": json_dump['id'],
                    "error": {
                        "code":-32601,
                        "message":"Method not allowed"
                        }
                    }
            header = {"Content-Type": "Content-Type: application/json"}

            content = json.dumps(content)

            flow.response = http.Response.make(status, content, header)

addons = [FilterJSONRPCMethod()]