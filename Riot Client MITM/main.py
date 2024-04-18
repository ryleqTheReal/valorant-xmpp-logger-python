import asyncio
import aiofiles
import os
import subprocess
from datetime import datetime
from src.ConfigMITM import ConfigMITM
from src.XMPPMitm import XmppMITM
from src.SharedValues import affinityMappings, xmppPort, host, port
import json
import threading
import sys

"""Here it first checks whether the riot client is running because it needs to modify the --client-config-url="http://host:port to our middleman host and port
    After finding out that the client does not run it initiates the HTTP server to listen for incoming riot client requests 
    Then it initates the XMPPMitm to listen for the incoming riot client chat requests
    At last it launches the riot client on the middleman host and port (this is why you need to start it using code sadly)"""

async def is_riot_client_running() -> bool:
    """Checks whether the riot client is running -> `bool`"""

    try:
        proc = await asyncio.create_subprocess_shell(
            "tasklist /FI \"IMAGENAME eq RiotClientServices.exe\" /NH",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if b"RiotClientServices.exe" in stdout:
            return True
        else:
            return False
    except Exception as e:
        return False

async def start_riot_client(riot_client_path=str, host=str, http_port=int) -> None:
    """Starts riot client on the given `host` and `http_port` -> None or Thread object for debugging"""
    
    command = f'"{riot_client_path}" --client-config-url="http://{host}:{http_port}" --launch-product=valorant --launch-patchline=live'

    print('Riot Client started!')

    process = await asyncio.create_subprocess_shell(command)
    await process.wait()
    print('Riot client closed!')
    sys.exit(0)

async def run_config_mitm(config_mitm) -> None:
    """Runs the synchronous ConfigMITM server in a separate thread -> None or Thread object for debugging"""

    thread = threading.Thread(target=config_mitm.start)
    thread.daemon = True
    thread.start()
    return thread  # Return the thread object for potential management

async def main():
    try:
        if await is_riot_client_running():
            print('Riot client is running, please close it before running this tool')
            return

        log_dir = './logs'
        os.makedirs(log_dir, exist_ok=True)
        log_path = f"{log_dir}/{int(datetime.now().timestamp())}.txt"

        async with aiofiles.open(log_path, mode='w', encoding='utf-8') as log_stream:
            await log_stream.write(json.dumps({'type': 'valorant-xmpp-logger-python', 'version': '1.0.0'}) + '\n')
        
            config_mitm = ConfigMITM(host=host, http_port=port, xmpp_port=xmppPort)
            # Run the blocking server in a separate thread
            asyncio.create_task(run_config_mitm(config_mitm))

            xmpp_mitm = XmppMITM(xmppPort, config_mitm, log_stream)
            xmpp_task = asyncio.create_task(xmpp_mitm.start())  # Start XMPP server as a background task

            await xmpp_task  # Wait for the XMPP server task if needed elsewhere

            print('Starting Riot Client...')
            riot_client_path = R'C:\Riot Games\Riot Client\RiotClientServices.exe' #Maybe change if path not found
            await start_riot_client(riot_client_path, host, port)
            sys.exit(0)
    except Exception as e:
        sys.exit(1)


if __name__ == '__main__':
    """Runs the Program"""
    asyncio.run(main())

