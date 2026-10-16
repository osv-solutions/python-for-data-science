"""Code from "8.6 Logging in: forms, sessions and cookies" that is shown in the book but not run on its own:
it needs your own data, a server or extra setup, or it is one step of an example
that the book builds up gradually. See the book for details."""

import scrapy

class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = ["http://127.0.0.1:8020/shop/catalogue/page-1.html"]
    custom_settings = {"DOWNLOAD_DELAY": 1, "ROBOTSTXT_OBEY": True}

    def parse(self, response):
        for book in response.css("article.book"):
            yield {"title": book.css("h3 a::attr(title)").get(),
                   "price": book.css("p.price::text").get()}
        yield from response.follow_all(css="li.next a")
