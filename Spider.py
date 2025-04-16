import aiofiles
import httpx
from lxml import etree
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
base_url = "xx"
import time
path = "xx"
sem = asyncio.Semaphore(50)
#下载每一画的漫画
async def download_comic(chapter, title):
    try:
         async with sem:
            async with httpx.AsyncClient() as client:
                res = await client.get(base_url+chapter,timeout=1000)
                res.raise_for_status()
                html = etree.HTML(res.text)
                src = html.xpath("//div[@id='content']//a/img/@src")[0]
                name = src.split('/')[-1]
                img = await client.get(src,timeout=1000)
                img.raise_for_status()
                async with aiofiles.open(f"./漫画/{title[0]+title[1]}/{name}","wb") as f:
                    await f.write(img.content)
                print(f"✔️  成功保存{title[0]+title[1]}/{name}")
    except Exception as e:
        print(f"🚫  下载{title}失败：{str(e)}")
#获取漫画目录
async def fetch_catalog(url):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url,timeout=1000)
            res.raise_for_status()
            html = etree.HTML(res.text)
            chapters = html.xpath("//div[@class='thumb-container']/a[@class='gallerythumb']/@href")
            if not chapters:
                print(f"🚫  无有效章节 {url}")
                return
            title = html.xpath("//div[@id='info']/h2[@class='title']//text()")
            if not title:
                print(f"🚫  无有效名字 {url}")
                return
            os.mkdir(f'./漫画/{title[0]+title[1]}')
            tasks = [download_comic(chapter,title) for chapter in chapters]
            await asyncio.gather(*tasks)
    except Exception as e:
        print(f"🚫  处理{url}失败: {str(e)}")
#获取漫画们
def start(url):
    asyncio.run(fetch_catalog(base_url+url))

async def main():
    async with httpx.AsyncClient() as client:
        res =await client.get(path,timeout=1000)
        html = etree.HTML(res.text)
        lists = html.xpath("//div[@class='container index-container']//div[@class='gallery']/a/@href")
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=4) as pool:
            tasks = [
                loop.run_in_executor(pool,start,list)
                for list in lists
            ]
            await asyncio.gather(*tasks)
        
   
if __name__=="__main__":
    os.mkdir("漫画")
    t1=time.time()
    asyncio.run(main())
    print(f"时间为{time.time()-t1}\n")