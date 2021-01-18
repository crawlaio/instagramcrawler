# -*- coding: utf-8 -*-
import json
import os
import re
from time import sleep

import requests


class InstagramCrawler:
    def __init__(self, user_id=None, username=None):
        self.cookies = ""
        self.proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        self.headers = {
            "authority": "www.instagram.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-dest": "document",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.username = username
        self.user_id = user_id
        self.video_dir = "."
        self.download_video_list = None

    def isexist_videos(self):
        download_video_list = []
        for root, dirs, files in os.walk(self.video_dir):
            files.sort()
            for file in files:
                if os.path.splitext(file)[1] == ".mp4":
                    download_video_list.append(file)
        return download_video_list

    def download(self, video_urls: list):
        for video_url in video_urls:
            video_name = "".join(re.findall(r".*/(.*?).mp4?", video_url))
            if f"{video_name}.mp4" not in self.download_video_list:
                response = requests.get(url=video_url, headers=self.headers, proxies=self.proxies)
                video_path = os.path.join(self.video_dir, f"{video_name}.mp4")
                with open(video_path, "wb") as f:
                    f.write(response.content)
                print("download", video_url, ">>", video_path)
            else:
                print("exists", video_url)

    def get_user_videos(self, after: str = ""):
        response = requests.get(
            url="https://www.instagram.com/graphql/query/",
            headers=self.headers,
            params={
                "query_hash": "f2405b236d85e8296cf30347c9f08c2a",
                "variables": json.dumps({"id": str(self.user_id), "first": 12, "after": after}),
            },
            proxies=self.proxies,
            cookies={item.split("=")[0]: item.split("=")[1] for item in self.cookies.split("; ")},
        ).json()
        has_next_page = (
            response.get("data").get("user").get("edge_owner_to_timeline_media").get("page_info").get("has_next_page")
        )
        end_cursor = (
            response.get("data").get("user").get("edge_owner_to_timeline_media").get("page_info").get("end_cursor")
        )
        video_urls = [
            one.get("node").get("video_url")
            for one in response.get("data").get("user").get("edge_owner_to_timeline_media").get("edges")
            if "http" in str(one.get("node").get("video_url")).strip()
        ]
        return has_next_page, end_cursor, video_urls

    def get_user_id(self):
        response = requests.get(
            url=f"https://www.instagram.com/{self.username}/",
            headers=self.headers,
            proxies=self.proxies,
            cookies={item.split("=")[0]: item.split("=")[1] for item in self.cookies.split("; ")},
        ).text
        if "登录 • Instagram" not in response:
            if re.findall(r'"owner":{"id":"(\d+)"', response):
                self.user_id = re.findall(r'"owner":{"id":"(\d+)"', response)[0]
                return self.user_id
            else:
                return None
        else:
            raise Exception("检查 Cookie")

    def main(self):
        if not self.user_id and self.username:
            user_id = self.get_user_id()
        if user_id:
            self.video_dir = os.path.join(os.path.dirname(__file__), "videos", str(self.user_id))
            if not os.path.exists(self.video_dir):
                os.makedirs(self.video_dir)
            self.download_video_list = self.isexist_videos()
            has_next_page, end_cursor, video_urls = self.get_user_videos()
            self.download(video_urls)
            while has_next_page:
                sleep(10)
                has_next_page, end_cursor, video_urls = self.get_user_videos(after=end_cursor)
                self.download(video_urls)
        else:
            raise Exception("获取用户 ID 失败，请手动填写")


if __name__ == "__main__":
    """
    # BY username
    InstagramCrawler(username="soyummy").main()
    # BY user_id
    InstagramCrawler(user_id=995282076).main()
    """
    InstagramCrawler(username="soyummy").main()
    # InstagramCrawler(user_id=995282076).main()
