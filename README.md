# 🏞  Reservoir Level WebScraper

A **Python + Selenium** automation tool to scrape **reservoir water level data** from the [CMWSSB portal](https://cmwssb.tn.gov.in/lake-level) for **multiple dates listed in an Excel file**.  
This project converts **hours of manual data collection** into a **minutes-long batch process** with clean, structured Excel output for hydrological analysis.

---

## 📌 Features

- **Automated Data Extraction**  
  Fetches **1,000+ date-specific reservoir records** from the CMWSSB portal.  

- **Dynamic Date Parsing**  
  Reads and processes all dates from an Excel file, with **day-first support** and duplicate handling.  

- **Robust Scraping Logic**  
  Uses **CSS selectors + explicit waits** to handle asynchronous table loads without data loss.  

- **Structured Output**  
  Saves clean results in an Excel file for **instant trend analysis**.

---

## 📂 Project Structure

```
📁 cmwssb_scraper/
 ├── lake_level_scraper.py   # Main script
 ├── poondi.xlsx             # Input dates file
 ├── poondi_level.xlsx       # Output dataset
 ├── requirements.txt        # Dependencies
 └── README.md               # Project documentation
```

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/cmwssb-scraper.git
cd cmwssb-scraper

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt**
```
pandas
selenium
webdriver-manager
openpyxl
```

---

## 🚀 Usage

1. **Prepare Input File**  
   Create an Excel file (`poondi.xlsx`) with dates in the first column (format: `DD-MM-YYYY`).

2. **Run the Script**
   ```bash
   python lake_level_scraper.py
   ```

3. **Choose Mode**  
   - Test scrape for a single date  
   - Scrape **all dates** from the Excel file  

4. **Get Results**  
   Data will be saved to `poondi_level.xlsx`.

---

## 📊 Example Output

| RESERVOIR | Level (ft) | Date       |
|-----------|------------|------------|
| Poondi    | 94.23      | 04-08-2023 |
| Cholavaram| 20.56      | 04-08-2023 |
| Red Hills | 47.11      | 04-08-2023 |

---

## 🛠 Technical Details

- **Language:** Python 3.x  
- **Libraries:** Selenium, Pandas, WebDriver Manager, OpenPyXL  
- **Automation:** Headless Chrome (optional)  
- **Efficiency:** Reduces manual collection of **1,000+ records** from ~8 hours to **<5 minutes**  

---

## 📄 CV Highlights

- **Automated** extraction of **1,000+ date-specific reservoir records** from the **CMWSSB portal** via Selenium + Pandas, cutting processing time from **~8 hrs to <5 mins**.  
- **Engineered** dynamic Excel date parsing with **CSS selector scraping & explicit waits**, ensuring **zero data loss**.  
- **Delivered** structured Excel outputs enabling **instant multi-date hydrological trend analysis**.  
