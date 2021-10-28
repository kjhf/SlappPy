"""
This slapipes module handles the communication between Slapp and Dola.
The pipes to the Slapp.
"""

import asyncio
import base64
import json
import logging
import os
import re
import traceback
from asyncio import Queue
from asyncio.subprocess import Process
from typing import Callable, Any, Awaitable, Set, Optional, Tuple

import dotenv

from slapp_py.core_classes.friend_code import FriendCode

MAX_RESULTS = 20

if not os.getenv("SLAPP_DATA_FOLDER"):
    dotenv.load_dotenv()

SLAPP_DATA_FOLDER = os.getenv("SLAPP_DATA_FOLDER")


async def _default_response_handler(success_message: str, response: dict) -> None:
    assert False, f"Slapp response handler not set. Discarding: {success_message=}, {response=}"


class SlapPipe:
    def __init__(self):
        """Constructor for SlapPipe"""
        self.slapp_write_queue: Queue[str] = Queue()
        self.slapp_loop = True
        self.slapp_process: Optional[Process] = None
        self.response_function: Callable[[str, dict], Awaitable[None]] = _default_response_handler

    def kill_slapp(self):
        """Kill the Slapp Process. If keep open is on, this restarts Slapp."""
        logging.info('kill_slapp called')
        if self.slapp_process:
            self.slapp_loop = False
            self.slapp_write_queue.put_nowait('')
            logging.info('stopping pipes')
            self.slapp_process.stdin.close()
            self.slapp_process.stderr.feed_eof()
            self.slapp_process.stdout.feed_eof()
            logging.info('killing process')
            self.slapp_process.kill()
            self.slapp_process = None

    async def _read_stdout(self, stdout):
        logging.debug('_read_stdout')
        while self.slapp_loop:
            try:
                response = (await stdout.readline())
                if not response:
                    logging.info('stdout: (none response)')
                    await asyncio.sleep(1)
                elif response.startswith(b"eyJNZXNzYWdlIjo"):  # This is the b64 start of a Slapp message.
                    decoded_bytes = base64.b64decode(response)
                    response = json.loads(str(decoded_bytes, "utf-8"))
                    await self.response_function(response.get("Message", "Response does not contain Message."), response)
                elif b"Caching task done." in response:
                    logging.debug('stdout: ' + response.decode('utf-8'))
                    await self.response_function("Caching task done.", {})
                else:
                    logging.info('stdout: ' + response.decode('utf-8'))
            except Exception as e:
                logging.error(msg=f'_read_stdout EXCEPTION {traceback.format_exc()}', exc_info=e)

    async def _read_stderr(self, stderr):
        logging.debug('_read_stderr')
        while self.slapp_loop:
            try:
                response: str = (await stderr.readline()).decode('utf-8')
                if not response:
                    logging.info('stderr: none response, this indicates Slapp has exited.')
                    logging.warning('stderr: Terminating slapp_loop.')
                    self.slapp_loop = False
                    await asyncio.sleep(1)
                    break
                else:
                    logging.error('stderr: ' + response)
            except Exception as e:
                logging.error(f'_read_stderr EXCEPTION: {traceback.format_exc()}', exc_info=e)

    async def _write_stdin(self, stdin):
        logging.debug('_write_stdin')
        while self.slapp_loop:
            try:
                while not self.slapp_write_queue.empty():
                    query = await self.slapp_write_queue.get()
                    if self.slapp_loop:
                        logging.debug(f'_write_stdin: writing {query}')
                        stdin.write(f'{query}\n'.encode('utf-8'))
                        await stdin.drain()
                        await asyncio.sleep(0.1)
                    else:
                        logging.info(f'_write_stdin: exiting')
                        return
                await asyncio.sleep(1)  # 1 sec yield
            except Exception as e:
                logging.error(f'_write_stdin EXCEPTION: {traceback.format_exc()}', exc_info=e)

    async def _run_slapp(self, slapp_path: str, mode: str, restart_on_fail: bool = True):
        while True:
            self.slapp_process = await asyncio.create_subprocess_shell(
                f'dotnet \"{slapp_path}\" \"%#%@%#%\" {mode}',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                encoding=None,  # encoding must be None
                errors=None,  # errors must be None
                shell=True,
                limit=200 * 1024 * 1024,  # 200 MiB (That's a lot for shell piping!)
            )
            self.slapp_loop = True
            logging.info("_run_slapp: Beginning slapp_loop...")
            await asyncio.gather(
                self._read_stderr(self.slapp_process.stderr),
                self._read_stdout(self.slapp_process.stdout),
                self._write_stdin(self.slapp_process.stdin)
            )
            if restart_on_fail:
                logging.info("_run_slapp: asyncio tasks finished! Restarting ...")
            else:
                logging.info("_run_slapp: asyncio tasks finished!")
                break

    async def initialise_slapp(self, new_response_function: Callable[[str, dict], Any], mode: str = "--keepOpen"):
        """Initialise the Slap Pipe"""
        logging.info("Initialising Slapp ...")
        slapp_console_path = os.getenv("SLAPP_CONSOLE_PATH")
        assert os.path.isfile(slapp_console_path), f'{slapp_console_path=} not a file, expected .dll'
        assert os.path.isdir(SLAPP_DATA_FOLDER), f'{SLAPP_DATA_FOLDER=} not a directory.'
        self.response_function = new_response_function
        restart_on_fail = mode == "--keepOpen"
        await self._run_slapp(slapp_console_path, mode, restart_on_fail=restart_on_fail)

    async def query_slapp(self, query: str, limit: Optional[int] = 20):
        """Query Slapp. The response comes back through the callback function that was passed in initialise_slapp."""
        options: Set[str] = set()

        # Handle options
        query = self.conditionally_add_option(options, query, 'exactcase', 'exactCase')
        query = self.conditionally_add_option(options, query, 'matchcase', 'exactCase')
        query = self.conditionally_add_option(options, query, 'queryisregex', 'queryIsRegex')
        query = self.conditionally_add_option(options, query, 'regex', 'queryIsRegex')
        query = self.conditionally_add_option(options, query, 'queryisclantag', 'queryIsClanTag')
        query = self.conditionally_add_option(options, query, 'clantag', 'queryIsClanTag')
        query = self.conditionally_add_option(options, query, 'team', 'queryIsTeam')
        query = self.conditionally_add_option(options, query, 'player', 'queryIsPlayer')
        query, has_limit_option = self.conditionally_add_limit(options, query)

        # If this is a friend code query
        if query.upper().startswith("SW-"):
            param = query[3:]
            try:
                _ = FriendCode(param)
                query = param
                options.add("--queryIsPlayer")
                options.add("--exactCase")
            except Exception as e:
                logging.debug(f"Query started with SW- but was not a friend code: {e} ")

        if not has_limit_option and limit is not None:
            options.add(f"--limit {limit}")

        logging.debug(f"Posting {query=} to existing Slapp process with options {' '.join(options)} ...")
        await self.slapp_write_queue.put(
            '--b64 ' + str(base64.b64encode(query.encode("utf-8")), "utf-8") + ' ' + ' '.join(options))

    async def slapp_describe(self, slapp_id: str):
        """Send a slappId command to Slapp"""
        await self.slapp_write_queue.put(f'--slappId {slapp_id}')

    @staticmethod
    def conditionally_add_option(options, query: str, typed_option_no_delimit: str, query_option_to_add: str) -> str:
        reg = re.compile(r"(--|–|—)" + typed_option_no_delimit, re.IGNORECASE)
        (query, n) = reg.subn('', query)
        if n:
            options.add("--" + query_option_to_add)
        return query.strip()

    @staticmethod
    def conditionally_add_limit(options, query: str) -> Tuple[str, bool]:
        reg = re.compile(r"(--|–|—)limit (\d+)", re.IGNORECASE)
        result = reg.search(query)
        custom_limit = True if result else False
        if custom_limit:
            lim = result.group(2)
            query = reg.sub('', query)
            options.add("--limit " + lim)
        return query.strip(), custom_limit
