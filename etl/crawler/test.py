from selenium import webdriver
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
driver = webdriver.Remote(      
   command_executor="http://127.0.0.1:4444/wd/hub",
   options=chrome_options
)
driver.get("http://www.baidu.com")
print(driver.title)
driver.close()