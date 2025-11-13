#!/usr/bin/env python3
# Скрипт безопасно создаёт таблицы (если нужно), добавляет колонку user.created_at при её отсутствии
# и создаёт admin-пользователя, если его нет.
# Запуск: python create_db_and_admin_fix.py

from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash
from sqlalchemy import text
import os, sys, traceback

def get_columns(conn, table):
    try:
        res = conn.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
        return [r[1] for r in res]
    except Exception as e:
        print("PRAGMA error:", e)
        return None

def main():
    app = create_app()
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    print(f"Using database URI: {db_uri}")

    with app.app_context():
        engine = db.get_engine()
        with engine.begin() as conn:
            cols = get_columns(conn, "user")
            if cols is None:
                print("Не удалось получить информацию о таблице user (возможно БД отсутствует).")
            else:
                print("Текущие колонки в user:", cols)

            # Если таблицы нет (cols == []), или PRAGMA вернул None, создаём всё из моделей
            if cols is None or cols == []:
                print("Создаю все таблицы (db.create_all)...")
                try:
                    db.create_all()
                except Exception as e:
                    print("Ошибка при db.create_all():", e)
                    traceback.print_exc()
                    sys.exit(1)
                # повторно получить колонки
                cols = get_columns(conn, "user")
                print("После create_all колонки user:", cols)

            # Если колонка created_at отсутствует, добавляем её
            if cols is not None and "created_at" not in cols:
                try:
                    print("Добавляю колонку created_at в таблицу user...")
                    conn.execute(text("ALTER TABLE user ADD COLUMN created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)"))
                    # commit automatic in engine.begin()
                    cols = get_columns(conn, "user")
                    print("После ALTER TABLE колонки user:", cols)
                except Exception as e:
                    print("Ошибка при добавлении колонки created_at:", e)
                    traceback.print_exc()
                    print("Если ALTER TABLE не поддерживается в вашей версии SQLite или возникла другая ошибка,")
                    print("вам нужно либо пересоздать таблицу user вручную, либо использовать Flask-Migrate.")
                    sys.exit(1)

            # Теперь безопасно проверяем/создаём admin
            try:
                admin_user = db.session.query(User).filter_by(username='admin').first()
            except Exception as e:
                print("Ошибка при попытке прочитать таблицу user:", e)
                print("PRAGMA table_info('user') вывел(а):", get_columns(conn, "user"))
                traceback.print_exc()
                sys.exit(1)

            if admin_user:
                print(f"Admin уже существует: {admin_user.username}")
                return

            default_pass = os.environ.get("CONTRACTS_ADMIN_PASS", "root64")
            admin = User(username='admin', password=generate_password_hash(default_pass), is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Admin создан: username='admin' password='{}'".format(default_pass))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Скрипт завершился с ошибкой:", exc)
        traceback.print_exc()
        sys.exit(1)