from config import DAEMON_DIR, DEBUG
from app import create_app

import os
import sys
import logging
from argparse import ArgumentParser
import traceback

try:
    import daemon
    from daemon import pidfile
except ImportError as e:
    print(traceback.format_exc())
    if e.__str__() == "No module named 'pwd'":
        print("This probably means you're a Windows user. Windows doesn't support daemonize")
        sys.exit(1)


def start_daemon(pid_file: str, log_file: str):
    """
    Function launches  daemon in its context
    :param pid_file:
    :type str:
    :param log_file:
    :type str:
    """

    if DEBUG:
        print('storage_daemon: pid file {}'.format(pid_file))
        print('storage_daemon: log file {}'.format(log_file))
        print('storage_daemon: about to start daemonization')

    # pidfile is a context
    with daemon.DaemonContext(
            working_directory=DAEMON_DIR,
            umask=0o002,
            pidfile=pidfile.TimeoutPIDLockFile(pid_file),
    ) as context:
        create_app(log_file)


def daemonize() -> None:
    # Do the Unix double-fork magic

    import os
    import sys
    from app import create_app
    from config import HOST, DEBUG

    if sys.platform == 'win32':
        print('Deamoization is only works in UNIX system')
        sys.exit(1)

    print("This is the parent PID {}".format(os.getpid()))
    try:
        pid = os.fork()
        if pid > 0:
            # Exit first parent
            sys.exit(0)
    except OSError as e:
        print("fork #1 failed: {} ({})".format(e.errno, e.strerror), sys.stderr)
        sys.exit(1)

    print("Detaching from parent environment")

    # Detach from parent environment
    os.chdir("/")
    """ The call to os.setsid() creates a new session.
    The process becomes the leader of a new session and a new process group,
    and is disassociated from its controlling terminal.
    """
    os.setsid()
    os.umask(0)

    # Do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from second parent; print eventual PID before exiting
            print("Detached Daemon PID {}".format(pid))
            sys.exit(0)
    except OSError as e:
        print("fork #2 failed:{} ({})".format(e.errno, e.strerror), sys.stderr)
        sys.exit(1)

    # Start the daemon main loop

    print("executing daemon background......")

    # create_app()

    # app = create_app()

    # app.run(host=HOST, port=port, debug=DEBUG)


def stop_daemon() -> None:
    import os

    pid = int(open(os.path.join(DAEMON_DIR, 'storage_daemon.pid')).read())
    try:
        os.kill(pid, 9)
        print('Stopped!')
    except Exception:
        print('No process with PID {} found'.format(str(pid)))


if __name__ == "__main__":

    parser = ArgumentParser(description='Storage daemon with Flask backend')
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-s', '--stop', default=False, action="store_true" , help="Run with this flag to stop running daemon")
    parser.add_argument('-pid', '--pid-file', default=os.path.join(DAEMON_DIR, 'storage_daemon.pid'), help='absolute pid file name')
    parser.add_argument('-l', '--log-file', default=os.path.join(DAEMON_DIR,'storage_daemon.log'), help='absolute log file name')
    args = parser.parse_args()

    os.makedirs(DAEMON_DIR, exist_ok=True)

    if args.stop:
        stop_daemon()
    else:
        start_daemon(port=args.port, pid_file=args.pid_file, log_file=args.log_file)
