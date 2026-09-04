import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

USERS = ["postgres", "root", "arnav"]
PASSWORDS = [
    "Arnav2002@",
    "postgres",
    "admin",
    "root",
    "password",
    "1234",
    "12345",
    "123456",
    "",
]


def try_connect():
    for user in USERS:
        for pwd in PASSWORDS:
            try:
                conn = psycopg2.connect(
                    dbname="postgres",
                    user=user,
                    password=pwd,
                    host="localhost",
                    port="5432",
                )
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                print(f"SUCCESS: Connected with user '{user}' and password '{pwd}'")

                # Check if razorshield DB exists
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM pg_database WHERE datname = 'razorshield'")
                if not cur.fetchone():
                    print("Database 'razorshield' does not exist. Creating...")
                    cur.execute("CREATE DATABASE razorshield")

                # Check if user 'user' exists
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'user'")
                if not cur.fetchone():
                    print("Role 'user' does not exist. Creating...")
                    cur.execute(
                        "CREATE USER \"user\" WITH ENCRYPTED PASSWORD 'password'"
                    )
                    cur.execute(
                        'GRANT ALL PRIVILEGES ON DATABASE razorshield TO "user"'
                    )
                    # Postgres 15+ requires granting public schema access
                    try:
                        # Reconnect to the new DB to grant schema usage
                        conn_db = psycopg2.connect(
                            dbname="razorshield",
                            user=user,
                            password=pwd,
                            host="localhost",
                            port="5432",
                        )
                        conn_db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                        cur_db = conn_db.cursor()
                        cur_db.execute('GRANT ALL ON SCHEMA public TO "user"')
                        conn_db.close()
                    except Exception as e:
                        print(f"Schema grant warning: {e}")
                else:
                    # Update password just in case
                    cur.execute(
                        "ALTER USER \"user\" WITH ENCRYPTED PASSWORD 'password'"
                    )

                cur.close()
                conn.close()
                return True
            except psycopg2.OperationalError as e:
                # Authentication failed
                continue
            except Exception as e:
                print(f"Error with {user}/{pwd}: {e}")
                continue
    return False


if not try_connect():
    print("FAILED: Could not guess local PostgreSQL credentials.")
