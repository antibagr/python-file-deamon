def deamonize() -> None:
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

    create_app()

    app = create_app()

    app.run(host=HOST, port=port, debug=DEBUG)


if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    deamonize()
