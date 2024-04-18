import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from urllib.parse import urlparse, parse_qs
from functools import partial
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

"""This class crates an HTTP proxy to intercept the communication between the riot client and the riot server
    For that it creates a HTTP server using HTTPServer which is using the IP onto which the riot client was modified (127.0.0.1:35479)
    It then receives the request sent by the riot client to the riot server (first two are update requests), proxies them to their original goal and sends them back to the client
    After logging in, the riot client sends a request to get the chat settings, in which we find  the relevant hosts and:

    - Change the chat.port to 35478
    - Change the chat.host to 127.0.0.1
    - Change the chat.allow_bad_cert.enabled to allow bad certificates
    - Change the chat.use_tls.enabled to disable SSl verification
    
    We then send back the modified response back to the riot client"""


class ConfigMITM:

    _affinityMappingID = 0
    affinityMappings = []

    def __init__(self, host=str, http_port=int, xmpp_port=int) -> None:
        """Initiates the attributes"""

        self.host = host
        self.http_port = http_port
        self.xmpp_port = xmpp_port
        handler = partial(self.RequestHandler, self)
        self.server = HTTPServer((self.host, self.http_port), handler)

    def start(self) -> None:
        """Starts the server -> None"""

        print(f'Starting Riot Client interceptor on {self.host}:{self.http_port}...')
        self.server.serve_forever()

    def stop(self) -> None:
        """Stops the server (not actually using this ever) -> None"""
        self.server.shutdown()
        print('Server has been stopped.')

    class RequestHandler(BaseHTTPRequestHandler):
        """The request handler class"""

        def __init__(self, config_mitm, *args, **kwargs) -> None:
            """Gets the necessary attributes from BaseHTTPRequestHandler"""

            self.config_mitm = config_mitm
            super().__init__(*args, **kwargs)

        def do_GET(self) -> None:
            """Handles the GET requests"""

            self.config_mitm.handle_request(self)

        def do_POST(self) -> None:
            """Handles the Post requests"""

            self.config_mitm.handle_request(self)

        def log_message(self, format, *args):
            return  # Suppress the default logging to stderr

    def handle_request(self, handler=object) -> None:
        """Handles the incoming requests"""

        print(f"Request: {handler.log_date_time_string()} {handler.command} {handler.path}")
        headers = {k: v for k, v in handler.headers.items() if k.lower() != 'host'}
        response = requests.request(
            method=handler.command,
            url=f'https://clientconfig.rpg.riotgames.com{handler.path}',
            headers=headers,
            verify=False  # Disabling SSL verification
        )
        handler.send_response(response.status_code)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()

        if handler.path.startswith('/api/v1/config/player') and response.status_code == 200:
            data = json.loads(response.text)
            if 'chat.affinities' in data:
                for region, ip in data['chat.affinities'].items():
                    existingMapping = next((m for m in self.affinityMappings if m['riotHost'] == ip), None)
                    if existingMapping:
                        data['chat.affinities'][region] = existingMapping['localHost']
                    else:
                        newMapping = {
                            'localHost': f'127.0.0.{self._affinityMappingID + 1}',
                            'riotHost': ip,
                            'riotPort': data['chat.port']
                        }
                        self.affinityMappings.append(newMapping)
                        data['chat.affinities'][region] = newMapping['localHost']
                        self._affinityMappingID += 1

                data['chat.port'] = self.xmpp_port
                data['chat.host'] = self.host
                data['chat.allow_bad_cert.enabled'] = True
                data['chat.use_tls.enabled'] = False

                handler.wfile.write(json.dumps(data).encode('utf-8'))
                with open(R'C:\Users\legit\Desktop\Streamsniper v3.0 Backup File\new_settings.txt', 'w') as file:
                    file.write(str(json.dumps(data).encode('utf-8')))
            else:
                handler.wfile.write(response.content)
        else:
            handler.wfile.write(response.content)
