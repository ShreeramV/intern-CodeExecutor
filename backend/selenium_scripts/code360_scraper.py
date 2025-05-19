# import os
# import sys
# import django
# import time

# BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(BACKEND_DIR)

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
# django.setup()

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# from executor.models import Topic, Company, Question, TestCase
# from django.db import IntegrityError

# # Scraping Function
# def scrape_code360():
#     print("Starting scraper...")

#     # WebDriver setup
#     HEADLESS = False  # Change to True to run without GUI
#     options = webdriver.ChromeOptions()
#     if HEADLESS:
#         options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")

#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=options)
#     driver.get("https://www.naukri.com/code360/problems")
    
#     # Set implicit wait to handle dynamic content
#     driver.implicitly_wait(30)  # Wait for up to 30 seconds for elements to appear
    
#     # Scroll to load dynamic content
#     SCROLL_PAUSE_TIME = 2
#     last_height = driver.execute_script("return document.body.scrollHeight")

#     for _ in range(5):  # Scroll multiple times
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(SCROLL_PAUSE_TIME)
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height == last_height:
#             break
#         last_height = new_height

#     # Find all problem links
#     try:
#         elements = driver.find_elements(By.CLASS_NAME, "problem-card")
#         print(f"Found {len(elements)} questions.")
#     except Exception as e:
#         print(f"❌ Error: {e}. Could not find problem elements.")
#         elements = []

#     for el in elements:
#         try:
#             # Extract title and link
#             title = el.text.strip()
#             link = "https://www.naukri.com" + el.get_attribute("href")

#             # Placeholder for topics, companies, and difficulty
#             topics = ["Algorithm", "Sorting"]  # Example topics
#             companies = ["Company1", "Company2"]  # Example companies
#             difficulty = "easy"
#             year_asked = 2023

#             # Create/get related objects
#             topic_objs = [Topic.objects.get_or_create(name=topic)[0] for topic in topics]
#             company_objs = [Company.objects.get_or_create(name=company)[0] for company in companies]

#             # Create and save the question
#             question = Question(
#                 title=title,
#                 description="Description of the problem",
#                 sample_input="Sample input",
#                 sample_output="Sample output",
#                 max_score=10,
#                 difficulty=difficulty,
#                 year_asked=year_asked,
#             )

#             print(f"Attempting to save question: {title}")
#             question.save()
#             question.topics.set(topic_objs)
#             question.companies.set(company_objs)

#             # Add sample test case
#             test_case = TestCase(
#                 question=question,
#                 input_data={"input": "sample"},
#                 expected_output={"output": "sample"},
#             )
#             test_case.save()

#             print(f"✅ Added: {title}")

#         except IntegrityError:
#             print(f"⚠️ Duplicate skipped: {title}")
#         except Exception as e:
#             print(f"❌ Error processing question: {e}")

#     driver.quit()
#     print(f"✅ Scraping finished. {len(elements)} total questions processed.")

# # Run
# if __name__ == "__main__":
#     scrape_code360()

import os
import sys
import django
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Django setup
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from executor.models import Topic, Company, Question, TestCase
from django.db import IntegrityError


def scrape_code360():
    print("Starting Code360 scraper...")

    # Set up WebDriver
    HEADLESS = False
    options = webdriver.ChromeOptions()
    if HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Open problem listing page
    driver.get("https://www.codingninjas.com/studio/problems")
    time.sleep(5)

    # Scroll to load more problems
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    problem_links = []
    try:
        cards = driver.find_elements(By.CLASS_NAME, "problem-card")
        for card in cards:
            try:
                link = card.get_attribute("href")
                if link and "problems" in link:
                    problem_links.append(link)
            except Exception:
                continue
    except Exception as e:
        print(f"❌ Error getting problem cards: {e}")

    print(f"🔗 Found {len(problem_links)} problems.")

    for link in problem_links:
        try:
            driver.get(link)
            time.sleep(3)

            # Extract title
            title = driver.find_element(By.CLASS_NAME, "problem-title").text.strip()

            # Extract difficulty
            difficulty = driver.find_element(By.CLASS_NAME, "difficulty-level").text.strip().lower()

            # Extract companies
            company_imgs = driver.find_elements(By.CSS_SELECTOR, ".companies-main-container img")
            companies = [img.get_attribute("alt") for img in company_imgs]

            # Extract description
            description = driver.find_element(By.CLASS_NAME, "problem-statement").get_attribute("innerHTML")

            # Extract sample input/output
            samples = driver.find_elements(By.CSS_SELECTOR, ".sample-cases pre code")
            sample_input = samples[0].text.strip() if len(samples) > 0 else ""
            sample_output = samples[1].text.strip() if len(samples) > 1 else ""

            # Example topics — can be improved later if real tags are available
            topics = ["Miscellaneous"]
            year_asked = 2023

            # Create/get related objects
            topic_objs = [Topic.objects.get_or_create(name=topic)[0] for topic in topics]
            company_objs = [Company.objects.get_or_create(name=name)[0] for name in companies]

            # Save question
            question = Question(
                title=title,
                description=description,
                sample_input=sample_input,
                sample_output=sample_output,
                max_score=10,
                difficulty=difficulty,
                year_asked=year_asked,
            )
            question.save()
            question.topics.set(topic_objs)
            question.companies.set(company_objs)

            # Save sample test case
            test_case = TestCase(
                question=question,
                input_data={"input": sample_input},
                expected_output={"output": sample_output},
            )
            test_case.save()

            print(f"✅ Saved: {title}")

        except IntegrityError:
            print(f"⚠️ Duplicate skipped: {title}")
        except Exception as e:
            print(f"❌ Error processing {link}: {e}")

    driver.quit()
    print("✅ Scraping complete.")


if __name__ == "__main__":
    scrape_code360()
