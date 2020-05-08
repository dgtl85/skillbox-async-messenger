"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        entered_login: str
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):

                entered_login = decoded.replace("login:", "").replace("\r\n", "")

                for client in self.server.clients:
                    if client.login == entered_login:
                        self.transport.write(
                            f"Login {entered_login} is busy, try another".encode()
                        )
                        self.connection_lost("Duplicate login attempt, disconnected.")
                        self.transport.close()
                        return

                self.login = entered_login
                self.transport.write(
                    f"Hi, {self.login}!".encode()
                )
                self.send_history()
            else:
                self.transport.write(
                    f"Unregistered. Please send ""login: <USERNAME>"" to register".encode()
                )
        else:
            if decoded.startswith("/count"): # To check number of active connections
                self.transport.write(
                    str(len(self.server.clients)).encode()
                )
            else:
                self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"

        self.update_history(format_string)

        encoded = format_string.encode()

        for client in self.server.clients:
            if not client.login is None and client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Connection estabilished")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Connection lost")

    def send_history(self):
        history_slice: []
        len_history = len(self.server.history)

        if len_history == 0:
            return
        elif len_history > 10:
            len_slice = -10
        else:
            len_slice = -1 * len_history

        history_slice = self.server.history[len_slice:]

        for current_message in history_slice:
            self.transport.write(
                f"{current_message}\n".encode()
            )

    def update_history(self, new_message):
         self.server.history.append(new_message)

class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Server started ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server stopped manually")
