# Scrapy settings for leetcode_scraper project

BOT_NAME = "leetcode_scraper"

SPIDER_MODULES = ["leetcode_scraper.spiders"]
NEWSPIDER_MODULE = "leetcode_scraper.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# ========== Scrapy-Selenium Configuration ==========
DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800,
}

# Update this path to the location of your ChromeDriver
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = 'D:/Apps/chromedriver/chromedriver-win64/chromedriver.exe'
SELENIUM_DRIVER_ARGUMENTS = ['--headless', '--no-sandbox', '--disable-dev-shm-usage']
# ===================================================

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
