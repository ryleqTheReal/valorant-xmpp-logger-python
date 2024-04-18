import asyncio
import ssl
import json
from datetime import datetime

"""This class creates connections to the previously in ConfigMITM modified chat-servers and logs the communication between that
    First it creates a local socket to listen for incoming requests on port 35478 (the previously modified port) to determine which chat server to connect to
    As soon as a request comes in, it saves the host it now communicates on (ipv4LocalHost) and finds the relevant chat socket in the mappings to connect to it
    After connecting to the chat socket, it starts logging all the incoming and outgoing traffic"""

class XmppMITM:
    def __init__(self, xmpp_port=int, config_mitm=object, log_stream=object):
        self.port = xmpp_port
        self.config_mitm = config_mitm
        self.log_stream = log_stream
        self.socketID = 0

    async def start(self) -> None:
        """Starts the XMPP server to listen to all hosts on port 35478 -> None"""

        print("Starting XMPP server...")

        self.server = await asyncio.start_server(
            self.handle_client, '0.0.0.0', self.port
        )

        print('Started XMPP Server!')
        asyncio.create_task(self.server.serve_forever())
        
    async def handle_client(self, client_reader:object, client_writer:object) -> None:
        """Handles incoming connections by connecting to the according chat socket -> None"""

        server_addr = client_writer.get_extra_info('sockname') #Find the IP for communcation
        ipv4LocalHost = server_addr[0]
        mapping = next((m for m in self.config_mitm.affinityMappings if m['localHost'] == ipv4LocalHost), None)
        if mapping is None:
            print(f'Unknown host {ipv4LocalHost}')
            await self.log_message(f'Unknown host {ipv4LocalHost}')
            client_writer.close()
            return

        self.socketID += 1
        current_socket_id = self.socketID
        await self.log_message(json.dumps({
            'type': 'open-valorant',
            'time': datetime.now().timestamp(),
            'host': mapping['riotHost'],
            'port': mapping['riotPort'],
            'socketID': current_socket_id
        }))

        pre_connect_buffer = bytearray()

        # Connect to the chat socket
        print(f"Conneting to: {mapping['riotHost']}:{mapping['riotPort']}...")
        riot_reader, riot_writer = await asyncio.open_connection(
            mapping['riotHost'], mapping['riotPort'], ssl=ssl.create_default_context()
        )
        print("Connected successfully!")

        if pre_connect_buffer:
            riot_writer.write(pre_connect_buffer)
            pre_connect_buffer.clear()
            await riot_writer.drain()

        asyncio.create_task(self.transfer_data(client_reader, riot_writer, current_socket_id, 'outgoing'))
        asyncio.create_task(self.transfer_data(riot_reader, client_writer, current_socket_id, 'incoming'))

    async def transfer_data(self, reader=object, writer=object, socket_id=int, direction=str) -> None:
        """Transfers the data into the necessary direction"""

        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
                await self.log_message(json.dumps({
                    'type': direction,
                    'time': datetime.now().timestamp(),
                    'data': data.decode(errors='ignore'),
                    'socketID': socket_id
                }))

        except ssl.SSLError as e:
            print('Connection closed!')

        finally:
            writer.close()
            await self.log_message(json.dumps({
                'type': f'close-{direction.split("-")[0]}',
                'time': datetime.now().timestamp(),
                'socketID': socket_id
            }))

    async def log_message(self, message=str) -> None:
        """Logs the messages"""
        
        await self.log_stream.write(message + '\n')