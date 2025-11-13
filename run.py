import argparse
import sys
import os
import socket
import threading
import time
import webbrowser

def init_db(app, db):
    with app.app_context():
        db.create_all()
        print("DB initialized.")

def create_admin_if_missing(app, db, username="admin", password="root64"):
    from models import User
    from werkzeug.security import generate_password_hash
    with app.app_context():
        existing = db.session.query(User).filter_by(username=username).first()
        if existing:
            print(f"Admin user '{username}' already exists.")
            return
        admin = User(username=username, password=generate_password_hash(password), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created: {username} / {password}")

def serve_waitress(app, host, port):
    try:
        from waitress import serve as waitress_serve
    except ImportError:
        print("Waitress not installed. Please install it in your environment.")
        sys.exit(1)
    print(f"Starting waitress on {host}:{port} ...")
    waitress_serve(app, host=host, port=port)

def wait_for_port_and_open(host, port, path='/', timeout=10):
    url = f"http://{host}:{port}{path}"
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                try:
                    webbrowser.open_new_tab(url)
                    print(f"Opened browser at {url}")
                except Exception as e:
                    print("Failed to open browser:", e)
                return
        except Exception:
            pass
        if time.time() - start > timeout:
            print(f"Timeout waiting for {host}:{port} to open (after {timeout}s)")
            return
        time.sleep(0.2)

def serve(app, host, port, open_browser=True, browser_path='/contracts'):
    if open_browser:
        t = threading.Thread(target=wait_for_port_and_open, args=(host, port, browser_path, 15), daemon=True)
        t.start()
    serve_waitress(app, host, port)

def main(argv=None):
    parser = argparse.ArgumentParser(prog="run", description="Manager for Contracts App")
    sub = parser.add_subparsers(dest="command")

    sub_init = sub.add_parser("init-db", help="Create database tables")
    sub_create = sub.add_parser("create-admin", help="Create admin user")
    sub_create.add_argument("username", nargs="?", default="admin")
    sub_create.add_argument("password", nargs="?", default="root64")

    sub_serve = sub.add_parser("serve", help="Run production server (waitress)")
    sub_serve.add_argument("--host", default="127.0.0.1")
    sub_serve.add_argument("--port", type=int, default=8000)
    sub_serve.add_argument("--no-browser", dest="no_browser", action="store_true",
                           help="Do not open the browser automatically (useful for service mode)")

    args = parser.parse_args(argv)

    # Импортируем create_app и единый экземпляр db из models
    from app import create_app
    from models import db

    app = create_app()

    default_admin = (os.environ.get("CONTRACTS_ADMIN_USER") or "admin")
    default_password = (os.environ.get("CONTRACTS_ADMIN_PASS") or "root64")

    if args.command == "init-db":
        init_db(app, db)
        return
    elif args.command == "create-admin":
        create_admin_if_missing(app, db, args.username, args.password)
        return
    else:
        init_db(app, db)
        create_admin_if_missing(app, db, default_admin, default_password)

        host = "127.0.0.1"
        port = 8000
        open_browser = True

        if args.command == "serve":
            host = args.host
            port = args.port
            open_browser = not getattr(args, "no_browser", False)

        browser_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
        serve(app, browser_host, port, open_browser=open_browser, browser_path='/contracts')

if __name__ == "__main__":
    main()