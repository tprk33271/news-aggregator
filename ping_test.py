import urllib.request
import urllib.error
import time

def check_website(url):
    print(f"Checking {url}...")
    try:
        start_time = time.time()
        # Add a User-Agent header to avoid being blocked by basic bot protection
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req, timeout=10)
        end_time = time.time()
        
        status_code = response.getcode()
        response_time = (end_time - start_time) * 1000
        
        if status_code == 200:
            print(f"Success! Website is UP.")
            print(f"Status Code: {status_code}")
            print(f"Response Time: {response_time:.2f} ms")
        else:
            print(f"Warning: Website returned status code {status_code}")
            
    except urllib.error.HTTPError as e:
        print(f"Failed! Website returned HTTP Error: {e.code}")
    except urllib.error.URLError as e:
        print(f"Failed to reach the server.")
        print(f"Reason: {e.reason}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_website("https://www.b-quik.com")
