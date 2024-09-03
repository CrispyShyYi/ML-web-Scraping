from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# Step 1: Set up Selenium WebDriver
chrome_driver_path = ChromeDriverManager("128.0.6613.85").install()
driver = webdriver.Chrome(service=ChromeService(chrome_driver_path))
wait = WebDriverWait(driver, 10)

# Load the main page
driver.get("https://paperswithcode.com/sota")

# Step 2: Extract "Area" Names
areas = []
area_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "task-group-title")))

for element in area_elements:
    area_name = element.find_element(By.TAG_NAME, 'a').text.strip()
    area_url = element.find_element(By.TAG_NAME, 'a').get_attribute('href')
    areas.append({'Area': area_name, 'Area_URL': area_url})

# Step 3: Extract "Task" Names
tasks = []
for area in areas:
    driver.get(area['Area_URL'])
    # Locate all the divs that contain task information (h2 and cards)
    task_containers = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.container.content-buffer")))
    for task_element in task_containers:
        # Extract the task name from the h2 tag within col-md-12
        task_name = task_element.find_element(By.CSS_SELECTOR, "div.col-md-12 h2").text.strip()

        # Locate all the sota-all-tasks divs within the same task_container
        sota_all_tasks_divs = task_element.find_elements(By.CSS_SELECTOR, "div.sota-all-tasks")

        task_urls = []

        for sota_all_tasks_div in sota_all_tasks_divs:
            # Find all the <a> tags within each sota-all-tasks div and extract their href attributes
            a_tags = sota_all_tasks_div.find_elements(By.TAG_NAME, 'a')
            for a in a_tags:
                task_url = a.get_attribute('href')
                # Add a new entry for each task URL
                tasks.append({'Area': area['Area'], 'Task': task_name, 'Task_URL': task_url})

# Step 4: Extract "Subtask" Names
subtasks = []
for task in tasks:
    driver.get(task['Task_URL'])
    subtask_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'card')))

    for subtask_element in subtask_elements:
        subtask_name = subtask_element.find_element(By.CSS_SELECTOR, "div.card-body h1").text.strip()
        subtask_url = subtask_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
        subtasks.append(
            {'Area': task['Area'], 'Task': task['Task'], 'Subtask': subtask_name, 'Subtask_URL': subtask_url})

# Step 5: Extract "Dataset" Information
datasets = []
for subtask in subtasks:
    try:
        driver.get(subtask['Subtask_URL'])
        # Additional scraping code here
    except TimeoutException:
        print(f"Timeout occurred while accessing {subtask['Subtask_URL']}")
        continue
    try:
        # Wait until either the table or the "no data" message is present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'benchmarks'))
        )

        # Check if the "no data" div is present
        no_data_div = driver.find_elements(By.CSS_SELECTOR, 'div.sota-no-sota')
        if no_data_div:
            continue  # Skip to the next subtask if no data is available

        # If data is present, locate the table
        table = driver.find_element(By.CSS_SELECTOR, 'div.sota-table-preview.table-responsive table')

        # Extract headers
        headers = [th.text.strip() for th in table.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th')]

        # Extract rows
        for row in table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr'):
            # Find the first <td> element in the row and extract the <a> tag's href attribute
            first_td = row.find_element(By.TAG_NAME, 'td')
            a_tag = first_td.find_element(By.TAG_NAME, 'a')
            url = a_tag.get_attribute('href')

            data = [td.text.strip() for td in row.find_elements(By.TAG_NAME, 'td')]
            datasets.append({
                'Area': subtask['Area'],
                'Task': subtask['Task'],
                'Subtask': subtask['Subtask'],
                'Benchmark_URL': url,
                **dict(zip(headers, data))
            })

    except TimeoutException:
        continue  # Skip to the next subtask if timeout occurs

# Step 6: Extract "Benchmark" Information
benchmarks = []
for dataset in datasets:
    driver.get(dataset['Benchmark_URL'])  # Assuming you extract the URL for each benchmark
    benchmark_table = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-stripped.show-overflow-x')))

    benchmark_headers = [th.text.strip() for th in benchmark_table.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th')]
    for row in benchmark_table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr'):
        benchmark_data = [td.text.strip() for td in row.find_elements(By.TAG_NAME, 'td')]
        benchmarks.append({'Area': dataset['Area'], 'Task': dataset['Task'], 'Subtask': dataset['Subtask'],
                           **dict(zip(benchmark_headers, benchmark_data))})

# Store the extracted data in a Pandas DataFrame
df_areas = pd.DataFrame(areas)
df_tasks = pd.DataFrame(tasks)
df_subtasks = pd.DataFrame(subtasks)
df_datasets = pd.DataFrame(datasets)
df_benchmarks = pd.DataFrame(benchmarks)

# Save the data to CSV files for further analysis
df_areas.to_csv('areas.csv', index=False)
df_tasks.to_csv('tasks.csv', index=False)
df_subtasks.to_csv('subtasks.csv', index=False)
df_datasets.to_csv('datasets.csv', index=False)
df_benchmarks.to_csv('benchmarks.csv', index=False)


# Close the WebDriver
driver.quit()

