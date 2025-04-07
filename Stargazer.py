#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @Author  :   Arthals
# @File    :   Stargazer.py
# @Time    :   2025/01/22 16:16:16
# @Contact :   zhuozhiyongde@126.com
# @Software:   Visual Studio Code


import json
import os
import re

import requests


class Stargazer:
    def __init__(self):
        self.username = os.getenv("GITHUB_USERNAME")
        self.token = os.getenv("GITHUB_TOKEN")
        self.template = os.getenv("TEMPLATE_PATH", "template/template.md")
        self.output = os.getenv("OUTPUT_PATH", "README.md")
        self.star_lists = []
        self.star_list_repos = {}
        self.data = {}

    def get_all_starred(self):
        url = f"https://api.github.com/users/{self.username}/starred?per_page=100"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Stargazer",
        }
        all_repos = {}
        while url:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            for repo in response.json():
                all_repos[repo["full_name"]] = {
                    "html_url": repo["html_url"],
                    "description": repo["description"] or None,
                    "listed": False,
                }
            url = response.links.get("next", {}).get("url")
        self.data = all_repos
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(all_repos, f, indent=4, ensure_ascii=False)

        return all_repos

    def get_lists(self):
        url = f"https://github.com/{self.username}?tab=stars"
        response = requests.get(url)
        pattern = f'href="/stars/{self.username}/lists/(\S+)".*?<h3 class="f4 text-bold no-wrap mr-3">(.*?)</h3>'
        match = re.findall(pattern, response.text, re.DOTALL)
        self.star_lists = match
        return match

    def get_list_repos(self, list_name):
        url = "https://github.com/stars/{username}/lists/{list_name}?page={page}"
        page = 1
        while True:
            response = requests.get(
                url.format(username=self.username, list_name=list_name, page=page)
            )
            pattern = r'<h3>\s*<a href="[^"]*">\s*<span class="text-normal">(\S+) / <\/span>(\S+)\s+<\/a>\s*<\/h3>'
            match = re.findall(pattern, response.text)
            page += 1
            if list_name not in self.star_list_repos:
                self.star_list_repos[list_name] = []
            self.star_list_repos[list_name].extend(match)
            if match == []:
                break
        return self.star_list_repos[list_name]

    def get_all_repos(self):
        for list_url, _ in self.star_lists:
            self.get_list_repos(list_url)
        return self.star_list_repos

    def generate_readme(self):
        text = ""

        for list_url, list_name in self.star_lists:
            text += f"## {list_name}\n\n"
            for user, repo in self.star_list_repos[list_url]:
                key = f"{user}/{repo}"
                if key not in self.data:
                    print(f"{key} not in self.data")
                    self.data[key]["listed"] = True
                    continue

                if not self.data[key]["listed"]:
                    self.data[key]["listed"] = True

                if self.data[key]["description"]:
                    text += f"-   [{key}](https://github.com/{key}) - {self.data[key]['description']}\n"
                else:
                    text += f"-   [{key}](https://github.com/{key})\n"

            text += "\n"

        text += "## Unlisted\n\n"

        for key in self.data:
            if not self.data[key]["listed"]:
                if self.data[key]["description"]:
                    text += f"-   [{key}](https://github.com/{key}) - {self.data[key]['description']}\n"
                else:
                    text += f"-   [{key}](https://github.com/{key})\n"

        text += "\n"

        with open(self.template, "r") as f:
            template = f.read()

        text = template.replace("[[GENERATE HERE]]", text.rstrip())

        with open("README.md", "w") as f:
            f.write(text)
        f.close()


if __name__ == "__main__":
    stargazer = Stargazer()
    stargazer.get_all_starred()
    stargazer.get_lists()
    stargazer.get_all_repos()
    stargazer.generate_readme()
