import aiohttp
from bs4 import BeautifulSoup

base_url = "https://safebooru.donmai.us/"

async def fetch_page(session, url):

    async with session.get(url) as response:
        response.raise_for_status()  
        return await response.text()

async def get_posts_links(url):

    async with aiohttp.ClientSession() as session:
        page_content = await fetch_page(session, url)
        soup = BeautifulSoup(page_content, "html.parser")

        articles = soup.find_all("article", id=True)

        article_ids = [article["id"] for article in articles]
        article_ids = [article_id[5:] for article_id in article_ids]
        return article_ids

async def get_media_url(url):

    async with aiohttp.ClientSession() as session:
        page_content = await fetch_page(session, url)
        soup = BeautifulSoup(page_content, "html.parser")

        section = soup.find(lambda tag: tag.name == "section" and tag.has_attr("data-file-url"))
        
        if section:
            media_url = section["data-file-url"]
            media_type = "video" if media_url.endswith((".mp4", ".webm", ".ogg")) else "image"

            return media_url, media_type
        return None, None

async def get_pages_count(artist_name):

    async with aiohttp.ClientSession() as session:
        page_num = 1
        while True:

            page_url = f"{base_url}posts?page={page_num}&tags={artist_name}"
            
            async with session.get(page_url) as response:
                response.raise_for_status()  
                page_content = await response.text()
            
            soup = BeautifulSoup(page_content, "html.parser")
            
            paginator_pages = soup.find_all("a", class_="paginator-page")
            
            if not paginator_pages:
                break
            
            last_page = int(paginator_pages[-1].text)

            if last_page < page_num:
                break

            page_num += 1
        return page_num 