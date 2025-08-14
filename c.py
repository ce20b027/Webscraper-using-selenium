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
    """
    Extracts data from specified columns of a table using Selenium.

    Args:
        driver: The Selenium WebDriver instance.
        table_selector: The CSS selector for the target table.
        column_headers: A list of strings representing the desired column headers.

    Returns:
        A tuple: (actual_headers_found, data)
        - actual_headers_found: list of headers that were actually found
        - data: list of lists containing the extracted data
    """
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
                # If a header is not found, we'll skip it in the extraction

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
                    row_data.append("") # Add empty string if cell index is out of bounds
            data.append(row_data)

        return actual_headers_found, data

    except Exception as e:
        print(f"An error occurred: {e}")
        return [], []

class LakeLevelScraper:
    def __init__(self, excel_file_path, output_file_path="lake_level_data.xlsx"):
        """
        Initialize the scraper
        
        Args:
            excel_file_path (str): Path to Excel file containing dates
            output_file_path (str): Path for output Excel file
        """
        self.excel_file_path = excel_file_path
        self.output_file_path = output_file_path
        self.base_url = "https://cmwssb.tn.gov.in/lake-level?date="
        self.driver = None
        
        # Table selector and desired headers
        self.table_selector = "table.lack-view.table.table-responsive.table-striped.table-bordered"
        self.desired_headers = [
            "RESERVOIR",
            "Full Tank Level (ft.)",
            "Full Capacity (mcft)",
            "Level (ft)",
            "Storage (mcft)",
            "Storage Level (%)",
            "Inflow (cusecs)",
            "Outflow (cusecs)",
            "Rainfall (mm)",
            "Storage as on same day last year (mcft)"
        ]
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        # Uncomment the next line if you want to run in headless mode (background)
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize driver with automatic ChromeDriver management
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        def read_dates_from_excel(self):
        """Read dates from Excel file and extract only date part (ignore time)"""
        try:
            df = pd.read_excel(self.excel_file_path)
            
            # Assuming the dates are in the first column
            dates_column = df.iloc[:, 0]  # First column
            
            dates = []

            for date_val in dates_column:
                if pd.notna(date_val):
                    try:
                        # Handle different date formats
                        if isinstance(date_val, str):
                            if ' ' in date_val:
                                date_part = date_val.split(' ')[0]
                                parsed_date = pd.to_datetime(date_part, format='%d-%m-%Y')
                            else:
                                parsed_date = pd.to_datetime(date_val, format='%d-%m-%Y')
                        else:
                            parsed_date = pd.to_datetime(date_val)
                        
                        # Format as DD-MM-YYYY and keep all occurrences
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
        """Extract data for a specific date"""
        try:
            # Navigate to the URL
            url = f"{self.base_url}{date_str}"
            print(f"Scraping data for date: {date_str}")
            self.driver.get(url)
            
            # Wait a moment for the page to load
            time.sleep(2)
            
            # Extract table data using the provided function
            actual_headers, extracted_data = extract_table_data(self.driver, self.table_selector, self.desired_headers)
            
            if extracted_data and actual_headers:
                # Add date to each row
                for row in extracted_data:
                    row.append(date_str)
                return actual_headers, extracted_data
            else:
                print(f"No data found for date: {date_str}")
                return [], []
                
        except TimeoutException:
            print(f"Timeout waiting for page to load for date: {date_str}")
            return [], []
        except Exception as e:
            print(f"Error extracting data for date {date_str}: {e}")
            return [], []
    
    def scrape_all_dates(self):
        """Scrape data for all dates in the Excel file"""
        # Read dates from Excel
        dates = self.read_dates_from_excel()
        
        if not dates:
            print("No valid dates found in Excel file")
            return
        
        print(f"Found {len(dates)} dates to process")
        
        # Setup driver
        self.setup_driver()
        
        all_data = []
        final_headers = None
        
        try:
            for i, date_str in enumerate(dates):
                print(f"Processing {i+1}/{len(dates)}: {date_str}")
                
                # Extract data for this date
                actual_headers, date_data = self.extract_data_for_date(date_str)
                
                if date_data and actual_headers:
                    # Set headers from first successful extraction
                    if final_headers is None:
                        final_headers = actual_headers + ["Date"]
                    
                    all_data.extend(date_data)
                    print(f"  Found {len(date_data)} reservoir records")
                else:
                    print(f"  No data found for {date_str}")
                
                # Add delay between requests to be respectful
                time.sleep(2)
            
            # Save data to Excel
            if all_data and final_headers:
                df = pd.DataFrame(all_data, columns=final_headers)
                df.to_excel(self.output_file_path, index=False)
                print(f"\nData saved to {self.output_file_path}")
                print(f"Total records: {len(all_data)}")
                
                # Print summary
                print("\nSummary:")
                print(f"Unique dates processed: {df['Date'].nunique()}")
                print(f"Total reservoir records: {len(df)}")
                print(f"Columns extracted: {final_headers}")
                
            else:
                print("No data was successfully extracted")
                
        except KeyboardInterrupt:
            print("Scraping interrupted by user")
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("Browser closed")
    
    def scrape_single_date(self, date_str):
        """Scrape data for a single date (for testing)"""
        self.setup_driver()
        
        try:
            actual_headers, data = self.extract_data_for_date(date_str)
            if data and actual_headers:
                headers = actual_headers + ["Date"]
                df = pd.DataFrame(data, columns=headers)
                print(f"\nData for {date_str}:")
                print(df.to_string(index=False))
                print(f"\nColumns found: {headers}")
                return df
            else:
                print(f"No data found for {date_str}")
                return None
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function to run the scraper"""
    
    # Configuration
    excel_file_path = "datesn.xlsx"  # Change this to your Excel file path
    output_file_path = "lake_level_extract.xlsx"
    
    # Check if Excel file exists
    if not os.path.exists(excel_file_path):
        print(f"Excel file not found: {excel_file_path}")
        print("Please make sure your Excel file exists and update the path in the script")
        return
    
    # Create scraper instance
    scraper = LakeLevelScraper(excel_file_path, output_file_path)
    
    # Option 1: Test with single date first
    print("Testing with single date first...")
    test_date = "04-08-2023"
    result = scraper.scrape_single_date(test_date)
    
    if result is not None:
        print(f"\nTest successful! Found {len(result)} records.")
        
        # Option 2: Scrape all dates from Excel
        print("\nDo you want to proceed with scraping all dates from Excel?")
        user_input = input("Enter 'y' to continue or 'n' to exit: ")
        if user_input.lower() == 'y':
            scraper.scrape_all_dates()
        else:
            print("Scraping cancelled")
    else:
        print("Test failed. Please check the website and table structure.")

if __name__ == "__main__":
    main()