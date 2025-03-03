import aiosqlite
import functools

db_location = "src/assets/posts.db"

def with_database(func):

    @functools.wraps(func)
    
    async def wrapper(*args, **kwargs):

        async with aiosqlite.connect(db_location) as posts_db:
            db_cursor = await posts_db.cursor()
            result = await func(db_cursor, *args, **kwargs)
            await posts_db.commit()
            return result
    return wrapper

def handle_exceptions(func):

    @functools.wraps(func)

    async def wrapper(*args, **kwargs):

        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            return None
    return wrapper

@with_database
@handle_exceptions
async def create_db(db_cursor):

    await db_cursor.execute("""CREATE TABLE IF NOT EXISTS stared_artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_name TEXT UNIQUE NOT NULL
    )""")

    await db_cursor.execute("""CREATE TABLE IF NOT EXISTS seen_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_id INTEGER NOT NULL,
        post_url TEXT NOT NULL,
        FOREIGN KEY (artist_id) REFERENCES stared_artists (id) ON DELETE CASCADE
    )""")

    await db_cursor.execute("""CREATE TABLE IF NOT EXISTS all_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_id INTEGER NOT NULL,
        post_url TEXT NOT NULL,
        FOREIGN KEY (artist_id) REFERENCES stared_artists (id) ON DELETE CASCADE
    )""")

    await db_cursor.execute("""CREATE TRIGGER IF NOT EXISTS move_to_viewed
        AFTER INSERT ON seen_posts
        BEGIN
            DELETE FROM all_posts
            WHERE post_url = NEW.post_url AND artist_id = NEW.artist_id;
        END;
    """)

@with_database
@handle_exceptions
async def add_artist(db_cursor, artist_name):

    await db_cursor.execute("SELECT 1 FROM stared_artists WHERE artist_name = ?", (artist_name,))
    if await db_cursor.fetchone():
        return False

    await db_cursor.execute("INSERT INTO stared_artists (artist_name) VALUES (?)", (artist_name,))
    return True

@with_database
@handle_exceptions
async def del_artist(db_cursor, artist_name):

    await db_cursor.execute("SELECT 1 FROM stared_artists WHERE artist_name = ?", (artist_name,))
    if not await db_cursor.fetchone():
        return False

    await db_cursor.execute("DELETE FROM stared_artists WHERE artist_name = ?", (artist_name,))
    return True

@with_database
@handle_exceptions
async def add_seen_post(db_cursor, artist_id, post_id):

    await db_cursor.execute("INSERT INTO seen_posts (artist_id, post_url) VALUES (?, ?)", (artist_id, post_id))

@with_database
@handle_exceptions
async def get_all_artists(db_cursor):

    await db_cursor.execute("SELECT artist_name FROM stared_artists")
    result = await db_cursor.fetchall()
    return [row[0] for row in result]

@with_database
@handle_exceptions
async def get_artist_id(db_cursor, artist_name):

    await db_cursor.execute("SELECT id FROM stared_artists WHERE artist_name = ?", (artist_name,))
    result = await db_cursor.fetchone()
    return result[0] if result else None

@with_database
@handle_exceptions
async def get_seen_posts(db_cursor, artist_id):

    await db_cursor.execute("SELECT post_url FROM seen_posts WHERE artist_id = ?", (artist_id,))
    result = await db_cursor.fetchall()
    return [int(row[0]) for row in result] if result else []

@with_database
@handle_exceptions
async def get_all_posts(db_cursor):

    await db_cursor.execute("SELECT post_url FROM all_posts")
    result = await db_cursor.fetchall()
    return [int(row[0]) for row in result] if result else []

@with_database
@handle_exceptions
async def get_all_posts_by_artist(db_cursor, artist_id):

    await db_cursor.execute("SELECT post_url FROM all_posts WHERE artist_id = ?", (artist_id,))
    result = await db_cursor.fetchall()
    return [row[0] for row in result] if result else []

@with_database
@handle_exceptions
async def add_all_post(db_cursor, artist_id, post_id):

    await db_cursor.execute("INSERT INTO all_posts (artist_id, post_url) VALUES (?, ?)", (artist_id, post_id))

@with_database
@handle_exceptions
async def get_artist_id_by_post(db_cursor, post_id):
    
    await db_cursor.execute("SELECT artist_id FROM all_posts WHERE post_url = ?", (post_id,))
    result = await db_cursor.fetchone()
    return result[0] if result else None