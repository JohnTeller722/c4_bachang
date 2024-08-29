import os
from flask import Flask, render_template, request
import paramiko
import websockets
import asyncio

async_mode = None
app = Flask(__name__)

socket = websockets

def ssh_conn():
    trans = paramiko.Transport(("localhost", 22))
    trans.start_client()
    trans.auth_password('pig2014', os.environ["NEKO_SSH_PASSWORD"])
    channel = trans.open_session()
    channel.get_pty(term="xterm")
    channel.invoke_shell()
    return channel

session = ssh_conn()

async def ssh_message_stdin(ws):
    async for message in ws:
        # print("AMESSAGE:", message)
        session.send(message)

async def ssh_message_stdout(ws):
    while True:
        if session.recv_ready():
            message = session.recv(4096)
            # print("ARESULT:", message)
            await ws.send(message)
        else:
            await asyncio.sleep(0.001)

async def ssh_message(ws):
    try:    
        receiver = asyncio.get_event_loop().create_task(ssh_message_stdin(ws))
        sender = asyncio.get_event_loop().create_task(ssh_message_stdout(ws))
        await receiver
        await sender
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection gracefully closed.")
    except OSError as e:
        print(e)

async def main():
    async with websockets.serve(ssh_message, "localhost", 5002):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())


