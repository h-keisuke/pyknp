import asyncio
import sys
import os
from asyncio.subprocess import PIPE

import six
import re
import socket
import platform
import sys


class Socket(object):

    def __init__(self, hostname, port, option=None):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((hostname, port))
        except:
            raise
        if option is not None:
            self.sock.send(option)
        data = ""
        while "OK" not in data:
            data = self.sock.recv(1024)

    def __del__(self):
        if self.sock:
            self.sock.close()

    def query(self, sentence, pattern):
        assert(isinstance(sentence, six.text_type))
        sentence = sentence.strip() + '\n'  # ensure sentence ends with '\n'
        self.sock.sendall(sentence.encode('utf-8'))
        data = self.sock.recv(1024)
        recv = data
        while not re.search(pattern, recv):
            data = self.sock.recv(1024)
            recv = "%s%s" % (recv, data)
        return recv.strip().decode('utf-8')


class Subprocess(object):

    def __init__(self, command, timeout=180):
        try:
            self.process = None
            self.command = command
            self.encoding = "CP932" if platform.system() == "Windows" else sys.getdefaultencoding()

        except OSError:
            raise

    def __del__(self):
        if self.process is not None:
            self.process.terminate()

    async def get_instance(self):
        if self.process is None:
            env = os.environ.copy()
            subproc_args = {'cwd': '.', 'close_fds': sys.platform != "win32"}
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                env=env,
                **subproc_args)
        return self.process

    async def query(self, sentence, pattern):
        assert(isinstance(sentence, six.text_type))
        sentence = sentence.rstrip() + os.linesep
        subprocess = await self.get_instance()
        subprocess.stdin.write(sentence.encode(self.encoding))
        result = ''
        while True:
            line = await subprocess.stdout.readline()
            line = line.decode(self.encoding).rstrip()
            if re.search(pattern, line):
                break
            result += line + os.linesep
        return result
