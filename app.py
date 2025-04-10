import os
import re
import time
import random
import undetected_chromedriver as uc
import winreg
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from urls import urls

# Create output directories for the scraped transcripts
WORD_COUNT_THRESHOLD = 500
output_dir_short = "scraped_transcripts_short"
output_dir_long = "scraped_transcripts_long"
os.makedirs(output_dir_short, exist_ok=True)
os.makedirs(output_dir_long, exist_ok=True)


def clean_text(text):
    """Clean and normalize extracted text."""
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def url_to_filename(url):
    """Convert a URL into a clean, safe file name."""
    # Remove https:// or http:// and convert forward slashes to #
    clean_url = url.replace('https://', '').replace('http://', '').replace('/', '#')
    return f"{clean_url}.txt"

def extract_all_paragraphs(driver):
    """Extract text from all <p> tags on the page."""
    try:
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        if not paragraphs:
            print("⚠️ No <p> tags found on the page.")
            return ""
            
        print(f"✅ Found {len(paragraphs)} <p> tags on the page. Extracting text...")
        
        all_paragraphs = []
        for p in paragraphs:
            if p.text.strip():
                all_paragraphs.append(p.text.strip())
                
        return "\n\n".join(all_paragraphs)
    except Exception as e:
        print(f"⚠️ Error extracting paragraphs: {str(e)}")
        return ""

def count_words(text):
    """Count the number of words in a text."""
    words = text.split()
    return len(words)

def get_chrome_version():
    """Get the installed Chrome version on Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version = winreg.QueryValueEx(key, "version")[0]
        return int(version.split('.')[0])  # Return major version number
    except WindowsError:
        return None

def handle_popups(driver):
    """Attempt to close common popup types"""
    try:
        # Common popup close button selectors
        popup_selectors = [
            "button[aria-label='Close']",
            "button[aria-label='close']",
            ".modal-close",
            ".popup-close",
            ".close-button",
            "button.close",
            "[data-dismiss='modal']",
            "//button[contains(@class, 'close')]",
            "//button[contains(text(), 'Close')]",
            "//button[contains(text(), '×')]",
            "//div[@role='dialog']//button",
            "//button[contains(@class, 'modal')]"
        ]
        
        for selector in popup_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed():
                        element.click()
                        print("✅ Closed a popup")
                        time.sleep(1)  # Wait for popup animation
            except:
                continue

        # If selectors didn't work, try sending escape key
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)  # Wait for potential animation
            print("✅ Sent escape key as fallback")
        except Exception as e:
            print(f"⚠️ Error sending escape key: {str(e)}")
                
    except Exception as e:
        print(f"⚠️ Error handling popups: {str(e)}")

def safe_click(driver, element, max_attempts=3):
    """Attempts to click an element using multiple methods."""
    for attempt in range(max_attempts):
        try:
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)  # Let scroll finish
            
            # Try different click methods
            try:
                element.click()  # Regular click
                return True
            except:
                try:
                    driver.execute_script("arguments[0].click();", element)  # JS click
                    return True
                except:
                    try:
                        ActionChains(driver).move_to_element(element).click().perform()  # Action click
                        return True
                    except:
                        if attempt == max_attempts - 1:
                            raise
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"⚠️ All click attempts failed: {str(e)}")
                return False
            time.sleep(1)
    return False

def scrape_url(url_data, driver):
    """Scrape content from a URL using Selenium with transcript button handling."""
    try:
        url = url_data["url"]
        source = url_data["source"]
        
        print(f"\n🔎 Visiting: {url} (Source: {source})")
        driver.get(url)
        
        # Increased delay after navigation for better page loading
        time.sleep(random.uniform(2, 3))
        
        # Try to close any popups
        handle_popups(driver)
        
        # Wait for page to load (wait for any paragraph to be present)
        wait = WebDriverWait(driver, 30)  # Increased from 20 to 30 seconds
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "p")))
            # Additional random delay after page load
            time.sleep(random.uniform(2, 3))
        except TimeoutException:
            print("⚠️ Timeout waiting for page to load. Will try to continue anyway.")
        
        # --- Try to find and click "Show full transcript" button ---
        transcript_text = ""
        try:
            # Use a more flexible wait for the transcript button
            transcript_button = None
            button_locators = [
                "//*[contains(text(), 'Show full transcript')]",
                "//*[contains(text(), 'Read full transcript')]",
                "//button[contains(., 'transcript')]",
                "//a[contains(., 'transcript')]"
            ]
            
            for locator in button_locators:
                try:
                    transcript_button = driver.find_element(By.XPATH, locator)
                    if transcript_button and transcript_button.is_displayed():
                        print(f"✅ Found transcript button using: {locator}")
                        break
                except NoSuchElementException:
                    continue
            
            if transcript_button and transcript_button.is_displayed():
                print("🖱️ Clicking transcript button...")
                if safe_click(driver, transcript_button):
                    print("✅ Successfully clicked transcript button")
                    # Increased delay for transcript content to load
                    time.sleep(random.uniform(2, 3))
                else:
                    print("⚠️ Failed to click transcript button")
                
                # Look for transcript container with multiple selectors
                transcript_selectors = [
                    "div[aria-label='Transcript']",
                    "div.transcript",
                    "div[class*='transcript']",
                    "div[aria-labelledby*='Transcript']",
                    "div[role='region'][aria-label*='transcript']",
                    ".transcript-container",
                    "#transcript-container"
                ]
                
                for selector in transcript_selectors:
                    try:
                        transcript_element = driver.find_element(By.CSS_SELECTOR, selector)
                        if transcript_element.is_displayed():
                            transcript_text = transcript_element.text
                            if transcript_text:
                                print(f"✅ Found transcript with selector: {selector}")
                                break
                    except NoSuchElementException:
                        continue
                
                if not transcript_text:
                    print("⚠️ Clicked button, but couldn't find transcript container.")
                    # As a fallback, try to find any newly appeared div after clicking
                    try:
                        # Wait for any new content to appear
                        time.sleep(1)
                        divs = driver.find_elements(By.TAG_NAME, "div")
                        for div in divs:
                            div_text = div.text
                            if div_text and len(div_text) > 500:  # Assuming transcript is reasonably long
                                transcript_text = div_text
                                print("✅ Found potential transcript content in a div element.")
                                break
                    except Exception as e:
                        print(f"⚠️ Error in fallback transcript search: {str(e)}")
            else:
                print("ℹ️ No transcript button found on this page.")
        except Exception as e:
            print(f"⚠️ Error handling transcript button: {str(e)}")

        # --- Extract all paragraph content regardless of transcript ---
        page_paragraphs_text = extract_all_paragraphs(driver)

        # Clean text outputs
        transcript_text = clean_text(transcript_text) if transcript_text else "No transcript found."
        page_paragraphs_text = clean_text(page_paragraphs_text) if page_paragraphs_text else "No paragraphs found."

        # Count words
        transcript_word_count = count_words(transcript_text)
        paragraphs_word_count = count_words(page_paragraphs_text)
        total_word_count = transcript_word_count + paragraphs_word_count

        # Determine which directory to use based on word count
        output_dir = output_dir_long if total_word_count >= WORD_COUNT_THRESHOLD else output_dir_short
        filename = url_to_filename(url)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Source: {source}\n")
            f.write(f"Total Word Count: {total_word_count}\n\n")
            f.write("=== TRANSCRIPT CONTENT ===\n")
            f.write(f"Word Count: {transcript_word_count}\n\n")
            f.write(transcript_text)
            f.write("\n\n=== PAGE PARAGRAPHS CONTENT ===\n")
            f.write(f"Word Count: {paragraphs_word_count}\n\n")
            f.write(page_paragraphs_text)

        print(f"✅ Successfully saved content to: {filepath} (Total words: {total_word_count})")
        print(f"📁 Saved to {'long' if total_word_count >= WORD_COUNT_THRESHOLD else 'short'} content folder")
        return True

    except Exception as e:
        print(f"❌ Error processing {url}: {str(e)}")
        return False

def main():
    """Main function to process all URLs."""
    print("\n" + "="*60)
    print("WEB SCRAPER WITH TRANSCRIPT BUTTON SUPPORT".center(60))
    print("="*60 + "\n")
    
    # Initialize undetected-chromedriver with improved options
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-notifications')
    
    try:
        print("🌐 Initializing undetected Chrome browser...")
        chrome_version = get_chrome_version()
        if chrome_version:
            driver = uc.Chrome(
                options=options,
                version_main=chrome_version
            )
        else:
            driver = uc.Chrome(options=options)  # Fallback to automatic detection
        
        driver.set_page_load_timeout(60)
        
        results = []
        total_urls = len(urls)
        print(f"📋 Found {total_urls} URLs to process")
        
        for i, url_data in enumerate(urls, 1):
            print(f"\n[{i}/{total_urls}] Processing: {url_data['url']}")
            success = scrape_url(url_data, driver)
            results.append((url_data['url'], success))
            
            if i < total_urls:
                # Increased delay between processing URLs
                delay = random.uniform(4, 9)
                print(f"⏳ Waiting {delay:.1f} seconds before next URL...")
                time.sleep(delay)
        
        # Print summary
        print("\n" + "="*60)
        print("SCRAPING SUMMARY".center(60))
        print("="*60)
        
        successful = sum(1 for _, success in results if success)
        print(f"✅ Successfully processed {successful} out of {total_urls} URLs")
        
        failed_urls = [url for url, success in results if not success]
        if failed_urls:
            print("\n❌ Failed URLs:")
            for url in failed_urls:
                print(f"- {url}")
        
        print("\n✅ Scraping completed!")
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
    finally:
        if 'driver' in locals():
            print("🧹 Cleaning up and closing browser...")
            driver.quit()

if __name__ == "__main__":
    main()