"""
This slapipes module handles the communication between Slapp and Dola.
The pipes to the Slapp.
"""

import asyncio
import base64
import json
import os
import re
import traceback
from asyncio import Queue
from typing import Callable, Any, Awaitable, Set

MAX_RESULTS = 20
slapp_write_queue: Queue[str] = Queue()
slapp_loop = True

SLAPP_DATA_FOLDER = os.getenv("SLAPP_DATA_FOLDER")


async def _default_response_handler(success_message: str, response: dict) -> None:
    assert False, f"Slapp response handler not set. Discarding: {success_message=}, {response=}"


response_function: Callable[[str, dict], Awaitable[None]] = _default_response_handler


async def _read_stdout(stdout):
    global response_function
    global slapp_loop

    print('_read_stdout')
    while slapp_loop:
        try:
            response = (await stdout.readline())
            if not response:
                print('stdout: (none response)')
                await asyncio.sleep(1)
            elif response.startswith(b"eyJNZXNzYWdlIjo"):  # This is the b64 start of a Slapp message.
                decoded_bytes = base64.b64decode(response)
                response = json.loads(str(decoded_bytes, "utf-8"))
                await response_function(response.get("Message", "Response does not contain Message."), response)
            elif b"Caching task done." in response:
                print('stdout: ' + response.decode('utf-8'))
                await response_function("Caching task done.", {})
            else:
                print('stdout: ' + response.decode('utf-8'))
        except Exception as e:
            print(f'_read_stdout EXCEPTION: {e}\n{traceback.format_exc()}')


async def _read_stderr(stderr):
    global slapp_loop

    print('_read_stderr')
    while slapp_loop:
        try:
            response: str = (await stderr.readline()).decode('utf-8')
            if not response:
                print('stderr: none response, this indicates Slapp has exited.')
                print('stderr: Terminating slapp_loop.')
                slapp_loop = False
                break
            else:
                print('stderr: ' + response)
        except Exception as e:
            print(f'_read_stderr EXCEPTION: {e}\n{traceback.format_exc()}')


async def _write_stdin(stdin):
    global slapp_loop

    print('_write_stdin')
    while slapp_loop:
        try:
            while not slapp_write_queue.empty():
                query = await slapp_write_queue.get()
                print(f'_write_stdin: writing {query}')
                stdin.write(f'{query}\n'.encode('utf-8'))
                await stdin.drain()
                await asyncio.sleep(0.1)
            await asyncio.sleep(1)
        except Exception as e:
            print(f'_write_stdin EXCEPTION: {e}\n{traceback.format_exc()}')


async def _run_slapp(slapp_path: str, mode: str):
    global slapp_loop

    proc = await asyncio.create_subprocess_shell(
        f'dotnet \"{slapp_path}\" \"%#%@%#%\" {mode}',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        encoding=None,  # encoding must be None
        errors=None,  # errors must be None
        shell=True,
        limit=100 * 1024 * 1024,  # 100 MiB
    )

    slapp_loop = True
    await asyncio.gather(
        _read_stderr(proc.stderr),
        _read_stdout(proc.stdout),
        _write_stdin(proc.stdin)
    )
    print("_run_slapp returned!")


async def initialise_slapp(new_response_function: Callable[[str, dict], Any], mode: str = "--keepOpen"):
    global response_function

    print("Initialising Slapp ...")
    slapp_console_path = os.getenv("SLAPP_CONSOLE_PATH")
    assert os.path.isfile(slapp_console_path), f'{slapp_console_path=} not a file, expected .dll'
    assert os.path.isdir(SLAPP_DATA_FOLDER), f'{SLAPP_DATA_FOLDER=} not a directory.'
    response_function = new_response_function
    await _run_slapp(slapp_console_path, mode)


async def query_slapp(query: str):
    """Query Slapp. The response comes back through the callback function that was passed in initialise_slapp."""
    options: Set[str] = set()

    # Handle options
    insensitive_exact_case = re.compile(re.escape('--exactcase'), re.IGNORECASE)
    (query, n) = insensitive_exact_case.subn('', query)
    query = query.strip()
    if n:
        options.add("--exactCase")

    insensitive_match_case = re.compile(re.escape('--matchcase'), re.IGNORECASE)
    (query, n) = insensitive_match_case.subn('', query)
    query = query.strip()
    if n:
        options.add("--exactCase")

    insensitive_query_is_regex = re.compile(re.escape('--queryisregex'), re.IGNORECASE)
    (query, n) = insensitive_query_is_regex.subn('', query)
    query = query.strip()
    if n:
        options.add("--queryIsRegex")

    insensitive_regex = re.compile(re.escape('--regex'), re.IGNORECASE)
    (query, n) = insensitive_regex.subn('', query)
    query = query.strip()
    if n:
        options.add("--queryIsRegex")

    insensitive_query_is_clantag = re.compile(re.escape('--queryisclantag'), re.IGNORECASE)
    (query, n) = insensitive_query_is_clantag.subn('', query)
    query = query.strip()
    if n:
        options.add("--queryIsClanTag")

    insensitive_clantag = re.compile(re.escape('--clantag'), re.IGNORECASE)
    (query, n) = insensitive_clantag.subn('', query)
    query = query.strip()
    if n:
        options.add("--queryIsClanTag")

    print(f"Posting {query=} to existing Slapp process with options {' '.join(options)} ...")
    await slapp_write_queue.put('--b64 ' + str(base64.b64encode(query.encode("utf-8")), "utf-8") + ' ' +
                                ' '.join(options))


async def slapp_describe(slapp_id: str):
    await slapp_write_queue.put(f'--slappId {slapp_id}')
