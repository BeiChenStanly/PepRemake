import asyncio
import httpx
import os
import json
import aiofiles
from tqdm.asyncio import tqdm_asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from PIL import Image
class BookInfo:
    def __init__(self, id: int, name: str, page_count: int):
        self.id = id
        self.name = name
        self.page_count = page_count

    def __repr__(self):
        return f"BookInfo(id={self.id}, name='{self.name}', page_count={self.page_count})"

class PepDownloader:
    def __init__(self, ids: list[int], output_folder: str = 'output', 
                 max_concurrent_books: int = 3, max_concurrent_pages: int = 10, acw_sc__v3: str = "example"):
        self.books = []
        self.config = self.Config(output_folder, acw_sc__v3)
        self.max_concurrent_books = max_concurrent_books
        self.max_concurrent_pages = max_concurrent_pages
        
        for id in ids:
            self.books.append(BookInfo(id, '', 0))

    class Config:
        def __init__(self, output_folder: str, acw_sc__v3: str = "example"):
            self.output_folder = output_folder
            self.temp_folder = os.path.join(output_folder, "temp")
            self.pdf_folder = os.path.join(output_folder, "pdfs")
            self.acw_sc__v3 = acw_sc__v3
            os.makedirs(self.temp_folder, exist_ok=True)
            os.makedirs(self.pdf_folder, exist_ok=True)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_book_name(self, client: httpx.AsyncClient, id: int) -> str:
        response = await client.get(
            f"https://book.pep.com.cn/{id}/mobile/index.html",
            headers={"Referer": "https://book.pep.com.cn/"}
        )
        response.raise_for_status()
        return response.text.split('<title>')[1].split('</title>')[0]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_book_page_count(self, client: httpx.AsyncClient, id: int) -> int:
        response = await client.get(
            f"https://book.pep.com.cn/{id}/mobile/javascript/config.js",
            headers={"Referer": "https://book.pep.com.cn/"}
        )
        response.raise_for_status()
        content = response.text
        start = content.find("bookConfig.totalPageCount") + len("bookConfig.totalPageCount=")
        end = content.find(";", start)
        return int(content[start:end])
    
    async def get_book_info(self, client: httpx.AsyncClient) -> None:
        tasks = []
        for book in self.books:
            tasks.append(self._get_single_book_info(client, book))
        
        results = await tqdm_asyncio.gather(
            *tasks, 
            desc="获取书籍信息",
            total=len(tasks)
        )
        
        # 更新书籍信息
        for i, result in enumerate(results):
            if result:
                self.books[i].name = result[0]
                self.books[i].page_count = result[1]
    
    async def _get_single_book_info(self, client: httpx.AsyncClient, book: BookInfo):
        try:
            name = await self.get_book_name(client, book.id)
            page_count = await self.get_book_page_count(client, book.id)
            return (name, page_count)
        except Exception as e:
            print(f"获取书籍信息失败 ID {book.id}: {e}")
            return (f"Unknown_{book.id}", 0)
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def download_page(self, client: httpx.AsyncClient, book: BookInfo, page: int):
        output_folder = os.path.join(self.config.temp_folder, str(book.id))
        os.makedirs(output_folder, exist_ok=True)
        file_path = os.path.join(output_folder, f"{book.id}_{page}.jpg")
        
        if os.path.exists(file_path):
            return
            
        response = await client.get(
            f"https://book.pep.com.cn/{book.id}/files/mobile/{page}.jpg",
            headers={"Referer": f"https://book.pep.com.cn/{book.id}/mobile/index.html"},
            timeout=30.0
        )
        response.raise_for_status()
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(response.content)
    
    async def download_book_pages(self, client: httpx.AsyncClient, book: BookInfo):
        if book.page_count <= 0:
            print(f"书籍 {book.name} 无有效页面，跳过下载")
            return
            
        print(f"开始下载: {book.name} ({book.page_count}页)")
        
        # 创建页面下载任务
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent_pages)
        
        async def download_with_semaphore(page):
            async with semaphore:
                await self.download_page(client, book, page)
        
        for page in range(1, book.page_count + 1):
            tasks.append(download_with_semaphore(page))
        
        # 使用异步进度条
        for task in tqdm_asyncio.as_completed(
            tasks, 
            total=len(tasks),
            desc=f"下载 {book.name[:15]}",
            unit="页"
        ):
            await task
    
    def convert_to_pdf(self, book: BookInfo):
        if book.page_count <= 0:
            return
            
        image_folder = os.path.join(self.config.temp_folder, str(book.id))
        pdf_path = os.path.join(self.config.pdf_folder, f"{book.name}.pdf")
        
        # 确保PDF文件名合法
        safe_name = "".join(c for c in book.name if c.isalnum() or c in " _-")
        pdf_path = os.path.join(self.config.pdf_folder, f"{safe_name}.pdf")
        
        # 收集图片路径
        image_files = []
        for page in range(1, book.page_count + 1):
            img_path = os.path.join(image_folder, f"{book.id}_{page}.jpg")
            if os.path.exists(img_path):
                image_files.append(img_path)
        
        if not image_files:
            print(f"未找到 {book.name} 的图片文件")
            return
        try:
            images = [Image.open(img) for img in image_files]
            if images:
                first_image = images[0]
                first_image.save(pdf_path, save_all=True, append_images=images[1:], resolution=100.0)
                print(f"已创建PDF: {pdf_path}")
        except Exception as e:
            print(f"创建PDF失败 {book.name}: {e}")
    
    def cleanup_temp_files(self, book: BookInfo):
        temp_folder = os.path.join(self.config.temp_folder, str(book.id))
        if os.path.exists(temp_folder):
            for file in os.listdir(temp_folder):
                if file.endswith(".jpg"):
                    os.remove(os.path.join(temp_folder, file))
            os.rmdir(temp_folder)
    
    async def process_single_book(self, client: httpx.AsyncClient, book: BookInfo):
        try:
            await self.download_book_pages(client, book)
            self.convert_to_pdf(book)
            self.cleanup_temp_files(book)
        except Exception as e:
            print(f"处理书籍失败 {book.name}: {e}")
    
    async def download_books(self):
        # 创建全局HTTP客户端
        async with httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            http2=True
        ) as client:
            client.cookies.set("acw_sc__v3",self.config.acw_sc__v3)
            # 获取书籍元数据
            await self.get_book_info(client)
            
            # 创建书籍处理任务
            tasks = []
            semaphore = asyncio.Semaphore(self.max_concurrent_books)
            
            async def process_with_semaphore(book):
                async with semaphore:
                    await self.process_single_book(client, book)
            
            for book in self.books:
                if book.page_count > 0:  # 只处理有有效页数的书籍
                    tasks.append(process_with_semaphore(book))
            
            # 执行所有任务
            await tqdm_asyncio.gather(
                *tasks, 
                desc="下载书籍", 
                total=len(tasks)
            )
    
    @staticmethod
    def get_book_ids_from_json(file_path: str) -> list[int]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ids = []
                for xkdata in data:
                    for item in xkdata.get("xklist", []):
                        book_id = item.get('id')
                        if book_id:
                            ids.append(book_id)
                return ids
        except Exception as e:
            print(f"读取JSON文件失败 {file_path}: {e}")
            return []

async def main():
    # 从JSON文件获取书籍ID
    book_ids = PepDownloader.get_book_ids_from_json("data.json")
    
    
    # 创建下载器实例
    downloader = PepDownloader(
        ids=book_ids,
        output_folder="教材",
        max_concurrent_books=3,    # 同时下载3本书
        max_concurrent_pages=40,      # 每本书同时下载40页
        acw_sc__v3="example"         # 请根据实际情况设置cookie
    )
    
    # 开始下载
    await downloader.download_books()

if __name__ == "__main__":
    asyncio.run(main())