from scrapy_selenium import SeleniumRequest
from scrapy.spiders import Spider

class LeetCodeSpider(Spider):
    name = 'leetcode'
    start_urls = ['https://leetcode.com/problemset/all/']

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response):
        self.logger.info("Page loaded with Selenium")
        # Example: extract problem titles
        for row in response.css('.reactable-data tr'):
            title = row.css('td:nth-child(3) a::text').get()
            link = row.css('td:nth-child(3) a::attr(href)').get()
            if title and link:
                yield {
                    'title': title.strip(),
                    'url': response.urljoin(link)
                }
