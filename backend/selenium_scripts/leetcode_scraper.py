import os
import django
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # Importing the correct exception
from webdriver_manager.chrome import ChromeDriverManager

# Add parent directory to path to locate Django project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from executor.models import Question, Topic, Company  # Adjust if needed

def get_all_problem_urls():
    # Initialize WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Running in headless mode (no UI)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    base_url = "https://leetcode.com/problemset/"
    driver.get(base_url)

    # Wait for a specific problem container to load, increasing the wait time
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".reactable-data .title")))


    except TimeoutException:
        print("Timeout: Problem containers did not load in time.")
        driver.quit()
        return []

    problem_links = set()

    # Extract problem links from the first page
    anchors = driver.find_elements(By.CSS_SELECTOR, ".reactable-data .title a")
    for a in anchors:
        href = a.get_attribute("href")
        if href and href.startswith("https://leetcode.com/problems/"):
            problem_links.add(href.split('?')[0])  # Clean up any query params

    # Handling pagination (scrolling down to load more questions)
    try:
        while True:
            # Scroll to the bottom to trigger loading of more questions
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Give time for content to load
            
            # Extract additional problem links
            anchors = driver.find_elements(By.CSS_SELECTOR, ".reactable-data .title a")
            for a in anchors:
                href = a.get_attribute("href")
                if href and href.startswith("https://leetcode.com/problems/"):
                    problem_links.add(href.split('?')[0])

            # Check if a "Next" button exists and is clickable
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, ".pagination-next")
                if next_button.is_enabled():
                    next_button.click()  # Click the "Next" button to load more problems
                    time.sleep(3)  # Wait for the next set of problems to load
                else:
                    break  # No more pages, exit the loop
            except:
                break  # No "Next" button found, exit the loop

    except Exception as e:
        print(f"Error during pagination: {e}")

    driver.quit()  # Close the browser
    return list(problem_links)

def scrape_leetcode():
    # Initialize WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Get all problem URLs
    problem_urls = get_all_problem_urls()
    print(f"Found {len(problem_urls)} problem URLs.")  # You can suppress this line

    for url in problem_urls:
        driver.get(url)
        time.sleep(3)

        # --- Title ---
        try:
            title = driver.find_element(By.CSS_SELECTOR, "div.text-body.text-sd-foreground .ellipsis").text.strip()
        except:
            title = "No title found"

        # --- Check if question already exists ---
        if Question.objects.filter(title=title).exists():
            print(f"Skipping duplicate question: {title}")  # Optional log for skipped duplicates
            continue

        # --- Difficulty ---
        try:
            difficulty = driver.find_element(By.CSS_SELECTOR, "p.text-[14px].text-sd-hard").text.strip().lower()
            if difficulty not in ["easy", "medium", "hard"]:
                difficulty = "easy"
        except:
            difficulty = "easy"

        # --- Companies ---
        try:
            company_elements = driver.find_elements(By.CSS_SELECTOR, "div.elfjS[data-track-load='description_content'] > div")
            companies = [elem.text.strip() for elem in company_elements]
        except:
            companies = []

        # --- Topics ---
        try:
            topic_elements = driver.find_elements(By.CSS_SELECTOR, ".relative.inline-flex.items-center.justify-center.text-caption.px-2.py-1.gap-1.rounded-full.bg-fill-secondary")
            topics = [elem.text.strip() for elem in topic_elements if elem.text.strip()]
        except:
            topics = []

        # --- Problem Description ---
        try:
            description = driver.find_element(By.CSS_SELECTOR, "div.elfjS[data-track-load='description_content']").text.strip()
        except:
            description = "No description found"

        # --- Sample Input ---
        try:
            sample_input = driver.find_element(By.XPATH, "//pre[contains(text(), 'Input:')]").text.strip()
        except:
            sample_input = "Not found"

        # --- Sample Output ---
        try:
            sample_output = driver.find_element(By.XPATH, "//pre[contains(text(), 'Output:')]").text.strip()
        except:
            sample_output = "Not found"

        # --- Explanation ---
        try:
            explanation = driver.find_element(By.XPATH, "//div[contains(text(), 'Explanation:')]").text.strip()
        except:
            explanation = ""

        year_asked = 2023  # Placeholder, as the year is not visible on the page

        # --- Save to DB ---
        question = Question.objects.create(
            title=title,
            description=description,
            sample_input=sample_input,
            sample_output=sample_output,
            explanation=explanation,
            difficulty=difficulty,
            year_asked=year_asked
        )

        for company_name in companies:
            if company_name:
                company_obj, _ = Company.objects.get_or_create(name=company_name)
                question.companies.add(company_obj)

        for topic_name in topics:
            if topic_name:
                topic_obj, _ = Topic.objects.get_or_create(name=topic_name)
                question.topics.add(topic_obj)

        question.save()
        print(f"✅ Question saved to database: {title}")  # Optional log for saved questions

    driver.quit()

if __name__ == "__main__":
    scrape_leetcode()
