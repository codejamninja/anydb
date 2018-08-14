from cfoundation import Service
from os import path
from sarge import run
from subprocess import Popen, PIPE
from sys import stdout
from time import sleep
import pydash as _

class Docker(Service):
    def run(self, image, config={}, cmd=None):
        s = self.app.services
        log = self.app.log
        command = self.create_command('docker run', config) + ' ' + image
        if cmd:
            command = command + ' ' + cmd
        log.debug('command: ' + command)
        run(command)

    def start(self, name, config={}, daemon=False):
        s = self.app.services
        log = self.app.log
        command = self.create_command('docker start', config) + ' ' + name
        log.debug('command: ' + command)
        run(command)
        if not daemon:
            run('docker logs --tail 100 -f ' + name)

    def execute(self, name, config={}, cmd='echo'):
        log = self.app.log
        command = self.create_command('docker exec', config) + ' ' + name + ' ' + cmd
        log.debug('command: ' + command)
        run(command)

    def get_container(self, name):
        docker = self.app.docker
        exists = False
        def find(value):
            nonlocal exists
            return value.name == name
        return _.find(docker.containers.list(all=True), find)

    def stop_container(self, name, container=None, signal=None):
        if not container:
            container = self.get_container(name)
        if not container:
            print('\'' + name + '\' does not exist')
            return
        elif container.status == 'exited':
            print('\'' + name + '\' already stopped')
            return
        print('stopping \'' + name + '\'')
        container.kill(signal)
        while(True):
            container = self.get_container(name)
            if container.status == 'exited':
                break
            sleep(1)

    def remove_container(self, name):
        container = self.get_container(name)
        if not container:
            print('\'' + name + '\' does not exist')
            return
        if container.status != 'exited':
            self.stop_container(name, container=container)
        print('removing \'' + name + '\'')
        container.remove(v=True, force=True)

    def create_command(self, command, config):
        def each(value, key):
            nonlocal command
            key = '--' + key
            if key == '--port':
                key = '-p'
            if key == '--daemon':
                key = '-d'
            if isinstance(value, list):
                def each(value):
                    nonlocal key, command
                    if isinstance(value, bool):
                        if value:
                            command = command + ' ' + key
                    else:
                        command = command + ' ' + key + ' "' + value + '"'
                _.for_each(value, each)
            else:
                if isinstance(value, bool):
                    if value:
                        command = command + ' ' + key
                else:
                    command = command + ' ' + key + ' "' + value + '"'
        _.for_each(config, each)
        return command
