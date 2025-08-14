import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
from datetime import datetime

def extract_table_data(driver, table_selector, column_headers):
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        thead = table.find_element(By.TAG_NAME, 'thead')
        tbody = table.find_element(By.TAG_NAME, 'tbody')

        header_row = thead.find_element(By.TAG_NAME, 'tr')
        ths = header_row.find_elements(By.TAG_NAME, 'th')
        header_texts = [th.text.strip() for th in ths]

        print(f"Available headers in table: {header_texts}")

        column_indexes = []
        actual_headers_found = []

        for header in column_headers:
            try:
                index = header_texts.index(header)
                column_indexes.append(index)
                actual_headers_found.append(header)
            except ValueError:
                print(f"Warning: Header '{header}' not found in the table.")

        if not column_indexes:
            print("No matching headers found. Cannot extract data.")
            return [], []

        print(f"Found {len(actual_headers_found)} matching headers: {actual_headers_found}")

        data = []
        rows = tbody.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            row_data = []
            for index in column_indexes:
                if index < len(cells):
                    row_data.append(cells[index].text.strip())
                else:
                    row_data.append("")
            data.append(row_data)

        return actual_headers_found, data

    except Exception as e:
        print(f"An error occurred: {e}")
        return [], []

class LakeLevelScraper:
    def __init__(self, excel_file_path, output_file_path="lake_level_data.xlsx"):
        self.excel_file_path = excel_file_path
        self.output_file_path = output_file_path
        self.base_url = "https://cmwssb.tn.gov.in/lake-level?date="
        self.driver = None

        self.table_selector = "table.lack-view.table.table-responsive.table-striped.table-bordered"
        self.desired_headers = [
            "RESERVOIR",

            "Level (ft)"
        ]

    def setup_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Enable if headless needed
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)

    def read_dates_from_excel(self):
        try:
            df = pd.read_excel(self.excel_file_path)
            dates_column = df.iloc[:, 0]
            dates = []

            for date_val in dates_column:
                if pd.notna(date_val):
                    try:
                        if isinstance(date_val, str):
                            if ' ' in date_val:
                                date_part = date_val.split(' ')[0]
                                parsed_date = pd.to_datetime(date_part, dayfirst=True)
                            else:
                                parsed_date = pd.to_datetime(date_val, dayfirst=True)
                        else:
                            parsed_date = pd.to_datetime(date_val, dayfirst=True)

                        formatted_date = parsed_date.strftime('%d-%m-%Y')
                        dates.append(formatted_date)

                    except Exception as e:
                        print(f"Could not parse date: {date_val} - Error: {e}")
                        continue

            print(f"Found {len(dates)} dates (including duplicates)")
            return dates

        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return []

    def extract_data_for_date(self, date_str):
        try:
            url = f"{self.base_url}{date_str}"
            print(f"Scraping data for date: {date_str}")
            self.driver.get(url)

            time.sleep(2)

            actual_headers, extracted_data = extract_table_data(self.driver, self.table_selector, self.desired_headers)

            if extracted_data and actual_headers:
                for row in extracted_data:
                    row.append(date_str)
                return actual_headers, extracted_data
            else:
                print(f"No data found for date: {date_str}")
                return [], []

        except TimeoutException:
            print(f"Timeout for date: {date_str}")
            return [], []
        except Exception as e:
            print(f"Error for {date_str}: {e}")
            return [], []

    def scrape_all_dates(self):
        dates = self.read_dates_from_excel()

        if not dates:
            print("No valid dates found in Excel")
            return

        print(f"Found {len(dates)} dates to process (with duplicates)")

        self.setup_driver()

        all_data = []
        final_headers = None

        try:
            for i, date_str in enumerate(dates):
                print(f"Processing {i+1}/{len(dates)}: {date_str}")
                actual_headers, date_data = self.extract_data_for_date(date_str)

                if date_data and actual_headers:
                    if final_headers is None:
                        final_headers = actual_headers + ["Date"]

                    all_data.extend(date_data)
                    print(f"  Found {len(date_data)} records")
                else:
                    print(f"  No data for {date_str}")

                time.sleep(2)

            if all_data and final_headers:
                df = pd.DataFrame(all_data, columns=final_headers)
                df.to_excel(self.output_file_path, index=False)
                print(f"\n✅ Data saved to {self.output_file_path}")
                print(f"Total records: {len(all_data)}")
                print(f"Columns: {final_headers}")
            else:
                print("No data extracted.")

        except KeyboardInterrupt:
            print("Interrupted by user.")
        except Exception as e:
            print(f"Scraping error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("Browser closed")

    def scrape_single_date(self, date_str):
        self.setup_driver()

        try:
            actual_headers, data = self.extract_data_for_date(date_str)
            if data and actual_headers:
                headers = actual_headers + ["Date"]
                df = pd.DataFrame(data, columns=headers)
                print(f"\nData for {date_str}:\n{df.to_string(index=False)}")
                return df
            else:
                print(f"No data found for {date_str}")
                return None
        finally:
            if self.driver:
                self.driver.quit()

def main():
    excel_file_path = "poondi.xlsx"
    output_file_path = "poondi_level.xlsx"

    if not os.path.exists(excel_file_path):
        print(f"Excel file not found: {excel_file_path}")
        return

    scraper = LakeLevelScraper(excel_file_path, output_file_path)

    print("Testing with single date...")
    test_date = "04-08-2023"
    result = scraper.scrape_single_date(test_date)

    if result is not None:
        print(f"\nTest successful! Found {len(result)} records.")

        print("\nProceed with scraping all dates from Excel?")
        user_input = input("Enter 'y' to continue or 'n' to exit: ")
        if user_input.lower() == 'y':
            scraper.scrape_all_dates()
        else:
            print("Scraping cancelled")
    else:
        print("Test failed. Please verify website/table structure.")

if __name__ == "__main__":
    main()
