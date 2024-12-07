import urllib.request

def fetchIncidents(url):
    # Initialize a dictionary to store HTTP headers.
    headers = {}
    # Set the User-Agent header to simulate a request from a web browser.
    headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    
    # Create a Request object with the specified URL and headers.
    request = urllib.request.Request(url, headers=headers)
    
    # Open the URL (like opening a web page in a browser), and read the data
    info = urllib.request.urlopen(request).read()
    
    # Return the data fetched from the URL.
    return info