from subprocess import check_call, Popen
from os import execv
from tempfile import mkstemp

def reboot(app):
    check_call(['systemctl', 'reboot'])

def upgrade(app):
    check_call(['sudo', '-u', 'pi', '/home/pi/pagerpi/updates/update-check'])

class Connector(object):
    returncode = None
    def __init__(self):
        self.process = self
        self.files = []

    def connect(self, app, host, port, identity):
        fd, name = mkstemp()
        fd.write(identity)
        fd.close()
        if self.process.returncode is None:
            self.process = Popen(['ssh',
                                  '-R', '22:%d:%d' % (host, port),
                                  '-i', name])

ACTIONS = {
    'reboot' : reboot,
    'upgrade' : upgrade,
    'connect' : Connector().connect
}


def perform(app, commands):
    """Do things that the server has requested.

    Right now, no actions are defined.  We can add actions here.
    """
    for name, args in commands:
        action = ACTIONS.get(name, default_action(name))
        action(app, *args)


def default_action(name):
    def action(*args):
        print("no such action %s (%d pos args)" % (name, len(args)))
    return action

