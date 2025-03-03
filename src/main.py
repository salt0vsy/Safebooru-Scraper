import asyncio, os, aiohttp, aiofiles
import db_module as db
import links_parser as ps
import flet as ft
import flet_video as ftv

async def main(page: ft.Page):
    
    page.title = "Safebooru Scraper"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#464646"
    page.update()

    post_index = 0
    active_posts = []
    menu_visible = False

    async def add_artist(e):
        artist_name = artist_input.value
        if await db.add_artist(artist_name):
            await load_dropdown()

    async def del_artist(e):
        artist_name = artist_input.value
        if await db.del_artist(artist_name):
            await load_dropdown()

    async def load_dropdown():
        options = await db.get_all_artists()
        search_select.options = [ft.dropdown.Option(option) for option in options]
        page.update()

    def on_dropdown_change(e):
        search_input.value = search_select.value
        artist_input.value = search_select.value
        page.update()

    
    async def show_all_posts(e):
        nonlocal active_posts, post_index
        media_container.controls.clear()
        active_posts = await db.get_all_posts()
        post_index = 0
        if active_posts:
            await display_post()

    async def search_posts(e):
        nonlocal active_posts, post_index
        media_container.controls.clear()
        artist_name = search_input.value.strip()
        if not artist_name:
            return
        artist_id = await db.get_artist_id(artist_name)
        if artist_id is None:
            return

        seen_posts = await db.get_seen_posts(artist_id)
        total_pages = await ps.get_pages_count(artist_name)
        active_posts = []

        for page_num in range(1, total_pages + 1):
            new_posts = await ps.get_posts_links(f"https://safebooru.donmai.us/posts?page={page_num}&tags={artist_name}")
            filtered_posts = [post for post in new_posts if int(post) not in seen_posts]
            active_posts.extend(filtered_posts)

        post_index = 0
        if active_posts:
            await display_post()

    async def next_post(e):
        nonlocal post_index
        if active_posts and post_index < len(active_posts) - 1:
            post_index += 1
            await display_post()

    async def prev_post(e):
        nonlocal post_index
        if active_posts and post_index > 0:
            post_index -= 1
            await display_post()

    async def display_post():
        media_container.controls.clear()
        if active_posts:
            post_id = active_posts[post_index]
            media_url, media_type = await ps.get_media_url(f"https://safebooru.donmai.us/posts/{post_id}")
            if media_url:
                if media_type == "video":
                    media_container.controls.append(
                        ftv.Video(
                            expand=True,
                            playlist=[ftv.VideoMedia(media_url)],
                            playlist_mode=ftv.PlaylistMode.LOOP,
                            fill_color=ft.Colors.BLACK,
                            volume=100,
                            autoplay=False,
                            filter_quality=ft.FilterQuality.HIGH,
                            muted=False
                        )
                    )
                else:
                    media_container.controls.append(
                        ft.Container(
                            content=ft.Image(src=media_url, fit=ft.ImageFit.CONTAIN, expand=True),
                            alignment=ft.alignment.center,
                            expand=True
                        )
                    )
        page.update()

    async def download_media(e):
        if not active_posts:
            return
        
        post_id = active_posts[post_index]
        media_url, _ = await ps.get_media_url(f"https://safebooru.donmai.us/posts/{post_id}")

        if media_url:
            filename = f"{post_id}.{media_url.split('.')[-1]}"
            filepath = os.path.join("downloads", filename)
            os.makedirs("downloads", exist_ok=True)

            async with aiohttp.ClientSession() as session:
                async with session.get(media_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(filepath, "wb") as f:
                            await f.write(await response.read())

            artist_id = await db.get_artist_id_by_post(post_id)
            if artist_id:
                await db.add_seen_post(artist_id, post_id)

    async def skip_post(e):
        if not active_posts:
            return
        
        post_id = active_posts[post_index]

        artist_id = await db.get_artist_id_by_post(post_id)
        if artist_id:
            await db.add_seen_post(artist_id, post_id)

    async def update_all_posts(e):
        all_artists = await db.get_all_artists()
        
        if not all_artists:
            return

        new_posts_count = 0

        for artist_name in all_artists:
            artist_id = await db.get_artist_id(artist_name)
            if artist_id is None:
                continue

            existing_posts = set(await db.get_all_posts_by_artist(artist_id))

            total_pages = await ps.get_pages_count(artist_name)
            new_posts = set()

            for page_num in range(1, total_pages + 1):
                post_links = await ps.get_posts_links(f"https://safebooru.donmai.us/posts?page={page_num}&tags={artist_name}")
                new_posts.update(post_links)

            new_posts_to_add = new_posts - existing_posts
            for post_url in new_posts_to_add:
                await db.add_all_post(artist_id, post_url)
                new_posts_count += 1

    def toggle_menu(e):
        nonlocal menu_visible
        menu_visible = not menu_visible
        menu_container.width = 200 if menu_visible else 0
        content_container.margin = ft.margin.only(left=200 if menu_visible else 0)
        menu_container.update()
        content_container.update()

    show_all_posts_button = ft.ElevatedButton("View All Posts", icon=ft.icons.LIST, on_click=show_all_posts)
    update_db_button = ft.ElevatedButton("Update Database", icon=ft.icons.UPDATE, on_click=update_all_posts)

    artist_input = ft.TextField(label="Enter artist name", expand=True)
    search_input = ft.TextField(label="Search posts", expand=True)
    search_select = ft.Dropdown(label="Select option", expand=True, on_change=on_dropdown_change)

    search_button = ft.ElevatedButton("Search posts", icon=ft.icons.SEARCH, on_click=search_posts)
    next_button = ft.IconButton(icon=ft.icons.NAVIGATE_NEXT, on_click=next_post)
    prev_button = ft.IconButton(icon=ft.icons.NAVIGATE_BEFORE, on_click=prev_post)
    download_button = ft.ElevatedButton("Download", icon=ft.icons.DOWNLOAD, on_click=download_media)
    skip_button = ft.ElevatedButton("Skip", icon=ft.icons.SKIP_NEXT, on_click=skip_post)
    add_button = ft.ElevatedButton("Add artist", icon=ft.icons.ADD, on_click=add_artist)
    remove_button = ft.ElevatedButton("Remove artist", icon=ft.icons.REMOVE, on_click=del_artist)
    menu_button = ft.IconButton(icon=ft.icons.MENU, on_click=toggle_menu)
    menu_label = ft.Text("Safebooru Scraper", size=24)

    media_container = ft.Column(spacing=10, expand=True)

    menu_container = ft.Container(
        width=200,
        bgcolor="#2d2d2d",
        padding=10,
        content=ft.Column(
            [
                ft.Divider(),
                artist_input, add_button, remove_button,
                ft.Divider(),
                search_input, search_select, search_button,
                ft.Divider(),
                show_all_posts_button,
                update_db_button,
                ft.Divider(),
            ],
            spacing=10
        )
    )

    content_container = ft.Container(
        expand=True,
        padding=20,
        bgcolor="#1e1e1e",
        content=ft.Column(
            [
                ft.Row([menu_button, menu_label], alignment=ft.MainAxisAlignment.START),
                ft.Container(media_container, height=400, bgcolor="#333", padding=5, expand=True),
                ft.Row([prev_button, next_button, download_button, skip_button], alignment=ft.MainAxisAlignment.CENTER)
            ]
        )
    )

    page.add(
        ft.Stack([menu_container, content_container], expand=True)
    )

    await load_dropdown()

asyncio.run(db.create_db())
ft.app(target=main)
