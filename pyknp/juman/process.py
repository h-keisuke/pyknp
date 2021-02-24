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
        subproc_args = {'cwd': '.', 'close_fds': sys.platform != "win32"}
        try:
            env = os.environ.copy()
            self.process = await asyncio.create_subprocess_exec(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env, **subproc_args)
            self.encoding = "CP932" if platform.system() == "Windows" else sys.getdefaultencoding()

        except OSError:
            raise

    def __del__(self):
        self.process.terminate()

    def query(self, sentence, pattern):
        assert(isinstance(sentence, six.text_type))
        sentence = sentence.rstrip() + os.linesep
        self.process.stdin.write(sentence.encode(self.encoding))
        result = ''
        while True:
            line = await self.process.stdout.readline()
            line = line.decode(self.encoding).rstrip()
            if re.search(pattern, line):
                break
            result += line + os.linesep
        return result
