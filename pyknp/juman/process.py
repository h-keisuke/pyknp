import signal
import os
import time

import six
import re
import socket
import platform
import sys
from subprocess import PIPE, Popen
import subprocess


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
        self.subproc_args = {'cwd': '.', 'close_fds': sys.platform != "win32"}
        try:
            self.env = os.environ.copy()
            self.process_command = command
            self.process_timeout = timeout
            if platform.system() == "Windows":
                self.process = Popen(self.process_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=self.env, creationflags=subprocess.HIGH_PRIORITY_CLASS | subprocess.DETACHED_PROCESS, **self.subproc_args)
            else:
                self.process = Popen(self.process_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=self.env, **self.subproc_args)
            self.encoding = "CP932" if platform.system() == "Windows" else sys.getdefaultencoding()

        except OSError:
            raise

    def __del__(self):
        self.kill()

    def kill(self):
        if platform.system() == "Windows":
            if self.process:
                pid = self.process.pid
                try:
                    os.kill(pid, signal.CTRL_C_EVENT)
                    time.sleep(60)
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        # pid is unassigned
                        pass
                    else:
                        try:
                            os.kill(pid, signal.CTRL_BREAK_EVENT)
                        except:
                            pass
                except OSError:
                    # pid is unassigned
                    pass
        else:
            self.process.stdin.close()
            self.process.stdout.close()
            try:
                self.process.kill()
                self.process.wait()
            except OSError:
                pass
            except TypeError:
                pass
            except AttributeError:
                pass

    def reopen(self):
        self.kill()
        if platform.system() == "Windows":
            self.process = Popen(self.process_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=self.env, creationflags=subprocess.HIGH_PRIORITY_CLASS | subprocess.DETACHED_PROCESS, **self.subproc_args)
        else:
            self.process = Popen(self.process_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=self.env, **self.subproc_args)

    def query(self, sentence, pattern):
        assert(isinstance(sentence, six.text_type))
        sentence = sentence.rstrip() + os.linesep
        self.process.stdout.flush()
        self.process.stdin.write(sentence.encode(self.encoding, 'replace'))
        self.process.stdin.flush()
        result = ''
        while True:
            line = self.process.stdout.readline().decode(self.encoding).rstrip()
            if re.search(pattern, line):
                break
            result += line + os.linesep
        self.process.stdout.flush()
        return result
