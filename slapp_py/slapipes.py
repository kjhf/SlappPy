import json
import os
import subprocess

slapp_path = None


def initialise_slapp():
    global slapp_path

    result = subprocess.run(['cd'], stdout=subprocess.PIPE, encoding='utf-8', shell=True)
    slapp_path = result.stdout
    print('cd: ' + slapp_path)
    slapp_path = slapp_path[0:slapp_path.index('PyBot')]
    slapp_path = os.path.join(slapp_path, 'venv', 'Slapp', 'SplatTagConsole.dll')
    assert os.path.isfile(slapp_path), f'Not a file: {slapp_path}'


async def query_slapp(query) -> (bool, dict):
    """Query Slapp. Returns success and the JSON response."""
    # global slapp_process
    # if slapp_process is None:
    slapp_process = subprocess.Popen(
        # f'dotnet \"{slapp_path}\" {query} --keepOpen',
        f'dotnet \"{slapp_path}\" {query}',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding='utf-8',
        errors='replace'
    )
    # else:
    #     slapp_process.stdin.writelines([query])
    #     await sleep(0.005)

    while True:
        response: str = slapp_process.stdout.readline()
        if response.startswith('{'):
            break
    response: dict = json.loads(response)
    print(response)
    return response["Message"] == "OK", response
