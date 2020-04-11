#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode().rstrip()

        if self.login is not None:
            self.send_message(decoded)

            # Обновление истории сообщений
            if len(self.server.history) == 10:
                self.server.history.pop(0)
            message = f"{self.login}: {decoded}"
            self.server.history.append(message)
        else:
            if decoded.startswith("login:"):
                temp_login = decoded.replace("login:", "")

                # Проверка введенного логина на уникальность
                for user in self.server.clients:
                    if user.login == temp_login:
                        self.transport.write(
                            f"Логин {temp_login} занят, попробуйте другой\n".encode()
                        )
                        self.transport.close()
                        break
                else:
                    # Успешное подключение под введенным логином
                    self.login = temp_login
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}"

        for user in self.server.clients:
            if user.login is not None:
                user.transport.write(message.encode())

    # Отправка истории сообщений
    def send_history(self):
        for message in self.server.history:
            self.transport.write(message.encode())


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")