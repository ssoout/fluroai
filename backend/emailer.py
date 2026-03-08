from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[EmailMessage] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    async def enqueue(self, message: EmailMessage) -> None:
        await self._queue.put(message)

    async def _worker(self) -> None:
        while True:
            message = await self._queue.get()
            # Здесь будет интеграция с SMTP/ESP. Пока просто логируем.
            print(
                f"[EMAIL] To: {message.to}\nSubject: {message.subject}\n\n{message.body}\n"
                "----------------------------------------"
            )
            self._queue.task_done()

