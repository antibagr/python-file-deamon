if __name__ == '__main__':

    from argparse import ArgumentParser
    from app import create_app, setup_logging
    from config import HOST, DEBUG

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port: int = args.port

    setup_logging()

    application = create_app()

    application.run(host=HOST, port=port, debug=DEBUG, use_reloader=False)

