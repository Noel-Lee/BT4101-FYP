import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

global total_jobs

def configure_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver


def search_jobs(driver, country, job_position, job_location, date_posted):
    full_url = f'{country}/jobs?q={"+".join(job_position.split())}&l={job_location}&fromage={date_posted}'
    print(full_url)
    driver.get(full_url)
    global total_jobs
    try:
        job_count_element = driver.find_element(By.XPATH,
                                                '//div[starts-with(@class, "jobsearch-JobCountAndSortPane-jobCount")]')
        total_jobs = job_count_element.find_element(By.XPATH, './span').text
        print(f"{total_jobs} found")
    except NoSuchElementException:
        print("No job count found")
        total_jobs = "Unknown"

    driver.save_screenshot('screenshot.png')
    return full_url


def scrape_job_data(driver, country):
    # Initialize DataFrame with new columns for Job Description and Salary
    df = pd.DataFrame({
        'Link': [''], 'Job Title': [''], 'Company': [''],
        'Days since Post': [''], 'Location': [''],
        'Job Description': [''], 'Salary': [''], 'Job-type':['']
    })
    job_count = 0
    job_links = []

    # Gather all job links on the current page
    # True would mean that it would keep on finding pages until there are no more pages left (Groups of 15 job posts)
    while True:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        # job_links = []
        boxes = soup.find_all('div', class_='job_seen_beacon')
        for i in boxes:
            link = i.find('a').get('href')
            link_full = country + link if link else None
            if link_full:
                job_links.append(link_full)
        
        # Check for the next page link
        try:
            next_page = soup.find('a', {'aria-label': 'Next Page'}).get('href')
            driver.get(country + next_page)
        except:
            break
    
    print(f"Found {len(job_links)} job links to scrape.")

    max_jobs = 100
  
    

    # Visit each job posting individually and scrape detailed information
    for job_link in job_links:

        if job_count < max_jobs:

            driver.get(job_link)
            time.sleep(2)  # Give time for the page to load

            try:
                # Extract the job title
                job_title = driver.find_element(By.CLASS_NAME, 'jobsearch-JobInfoHeader-title').text

                # Extract the job description (using the div with id 'jobDescriptionText')
                description_element = driver.find_element(By.ID, 'jobDescriptionText')
                job_description = description_element.text.strip() if description_element else "No description available"

                # Extract the company name
                company_tag = i.find('span', {'data-testid': 'company-name'})
                company = company_tag.text if company_tag else "No company information"

                # Find the div with class 'metadata salary-snippet-container css-1f4kgma eu4oa1w0'
                job_type = i.find('div', class_='js-match-insights-provider-kyg8or eu4oa1w0')

                # Extract the text from the div, or provide a fallback if the div is not found
                job_type = job_type.text.strip() if job_type else "No job-type information provided"

                # Extract the location
                location_element = i.find('div', {'data-testid': 'text-location'})
                location = location_element.text if location_element else "No location specified"

                # Extract the date posted
                try:
                    date_posted = i.find('span', class_='date').text
                except AttributeError:
                    date_tag = i.find('span', {'data-testid': 'myJobsStateDate'})
                    date_posted = date_tag.text.strip() if date_tag else "No date provided"

                # Find the div with class 'metadata salary-snippet-container css-1f4kgma eu4oa1w0'
                salary_element = i.find('div', class_='metadata salary-snippet-container css-1f4kgma eu4oa1w0')

                # Extract the text from the div, or provide a fallback if the div is not found
                salary = salary_element.text.strip() if salary_element else "No salary information provided"

                # Add the data to the DataFrame
                new_data = pd.DataFrame({
                    'Link': [job_link],
                    'Job Title': [job_title],
                    'Company': [company],
                    'Days since Post': [date_posted],  # Date Posted may not be available on job detail page
                    'Location': [location],
                    'Job Description': [job_description],
                    'Salary': [salary],
                    'Job-type': [job_type]
                })

                df = pd.concat([df, new_data], ignore_index=True)
                job_count += 1

            except NoSuchElementException as e:
                print(f"Error scraping job: {e}")


            print(f"Scraped first {job_count} jobs.")

        else:
            print(f"max_jobs set at {max_jobs}. There are job postings not scraped")
            break

    return df


def clean_data(df):
    def posted(x):
        x = x.replace('PostedPosted', '').strip()
        x = x.replace('EmployerActive', '').strip()
        x = x.replace('PostedToday', '0').strip()
        x = x.replace('PostedJust posted', '0').strip()
        x = x.replace('today', '0').strip()

        return x

    def day(x):
        x = x.replace('days ago', '').strip()
        x = x.replace('day ago', '').strip()
        return x

    def plus(x):
        x = x.replace('+', '').strip()
        return x

    df['Days since Post'] = df['Days since Post'].apply(posted)
    df['Days since Post'] = df['Days since Post'].apply(day)
    df['Days since Post'] = df['Days since Post'].apply(plus)

    return df


def sort_data(df):
    def convert_to_integer(x):
        try:
            return int(x)
        except ValueError:
            return float('inf')

    df['Date_num'] = df['Days since Post'].apply(lambda x: x[:2].strip())
    df['Date_num2'] = df['Date_num'].apply(convert_to_integer)
    df.sort_values(by=['Date_num2'], inplace=True)

    df = df[['Link', 'Job Title', 'Company', 'Days since Post', 'Location', 'Job Description', 'Salary']]
    return df


def save_csv(df, job_position, job_location):
    def get_user_desktop_path():
        home_dir = os.path.expanduser("~")
        desktop_path = os.path.join(home_dir, "Desktop")
        return desktop_path

    file_path = os.path.join(get_user_desktop_path(), '{}_{}'.format(job_position, job_location))
    csv_file = '{}.csv'.format(file_path)
    df.to_csv('{}.csv'.format(file_path), index=False)

    return csv_file


def send_email(df, sender_email, receiver_email, job_position, job_location, password):
    sender = sender_email
    receiver = receiver_email
    password = password
    msg = MIMEMultipart()
    msg['Subject'] = 'New Jobs from Indeed'
    msg['From'] = sender
    msg['To'] = ','.join(receiver)

    attachment_filename = generate_attachment_filename(job_position, job_location)

    csv_content = df.to_csv(index=False).encode()

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(csv_content)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
    msg.attach(part)

    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.login(user=sender, password=password)

    s.sendmail(sender, receiver, msg.as_string())

    s.quit()


def send_email_empty(sender, receiver_email, subject, body, password):
    msg = MIMEMultipart()
    password = password

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(receiver_email)

    # Attach the body as the text/plain part of the email
    msg.attach(MIMEText(body, 'plain'))

    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.login(user=sender, password=password)

    s.sendmail(sender, receiver_email, msg.as_string())

    s.quit()


def generate_attachment_filename(job_title, job_location):
    filename = f"{job_title.replace(' ', '_')}_{job_location.replace(' ', '_')}.csv"
    return filename
