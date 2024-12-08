import urllib.request

def fetchIncidents(url):
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    
    request = urllib.request.Request(url, headers=headers)
    
    info = urllib.request.urlopen(request).read()
    
    return info