import requests

def main():
    url = "http://127.0.0.1:8000/api/chat/stream"
    params = {"prompt": "Hello", "temperature": 0.7}
    print(f"Pinging {url}...")
    try:
        r = requests.get(url, params=params, stream=True)
        print(f"Status Code: {r.status_code}")
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                print(chunk.decode('utf-8'), end='', flush=True)
        print("\nRequest finished.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
