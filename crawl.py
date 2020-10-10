import json
from selenium import webdriver
from tld import get_tld
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import sys
import time



def run_onedomain(domain_url):
    #file = "fingerprinting_domains.json"
    binary_path = '/home/xlin/VisibleV8/visible_chromium/src/out/Builder/chrome'
    executable_path = '/home/xlin/Tools/chromedriver_75/chromedriver'
    timestr = str(time.strftime("%Y%m%d_%H%M%S"))
    #urls = []
    #with open(file, 'r') as f:
    #    s = f.read()
    #    data = json.loads(s)
    #    for line in data:
    #        url_ls = data[line]
    #        for each in url_ls:
    #            urls.append(each['top_url'])
    #print(len(urls))

    domain_dir = domain_url.replace('/', '_')
    domain_dir = domain_dir.replace(':', '_')
    if not os.path.isdir(domain_dir):
        os.mkdir(domain_dir)
    os.chdir(domain_dir)
    
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = 'normal'  # complete
    options = Options()
    options.headless = False
    options.binary_location = binary_path
    options.add_argument('--no-sandbox')
    
    #for each_url in urls:
    try:
        #fld = get_tld(each_url, as_object=True).fld
        fld = get_tld(domain_url, as_object=True).fld
        driver = webdriver.Chrome(desired_capabilities=caps, executable_path=executable_path, chrome_options=options)
        if 'http' not in domain_url:
            domain_url = 'http://'+domain_url
        driver.get(domain_url)
        time.sleep(10)
        print(fld)
    except Exception as e:
        print(str(e))
        #continue
        exit(1)
    for root, dirs, files in os.walk("."):
        i = 0
        for filename in files:
            if filename.startswith('vv8-') and filename.endswith('0.log'):
                os.rename(filename, fld + '_' + timestr + '_' +str(i) + '.log')
                i += 1
    try:
        driver.quit()
    except Exception as exc:
        print(str(exc))
        #continue
        exit(1)


if __name__ == '__main__':
    top_url = sys.argv[1]
    run_onedomain(top_url)
