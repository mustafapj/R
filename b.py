import requests

API_KEY = "sk-ef7adaec26e9475a847d295ce17ee6f2"

url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "hello"}],
    "max_tokens": 5
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    
    if response.status_code == 200:
        print("✅ المفتاح متصل")
    else:
        print("❌ المفتاح غير متصل")
        
except:
    print("❌ المفتاح غير متصل")