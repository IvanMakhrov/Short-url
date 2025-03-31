from locust import HttpUser, task, between
import random
import string
from urllib.parse import quote

class ShortLinkUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"
    
    def on_start(self):
        self.short_codes = []
        self.original_urls = []
        
        for _ in range(3):
            self.create_short_link()
    
    @task(5)
    def create_short_link(self):
        url = f"https://example.com/{''.join(random.choices(string.ascii_lowercase, k=10))}"
        self.original_urls.append(url)
        
        payload = {"original_url": url}
        
        if random.random() < 0.3:
            payload["custom_alias"] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        with self.client.post(
            "/links/shorten",
            json=payload,
            name="/links/shorten",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    short_url = response.json()["short_code"]
                    if not short_url.startswith(("http://", "https://")):
                        response.failure(f"Invalid URL format in response: {short_url}")
                        return
                    
                    short_code = short_url.split("/")[-1]
                    if not short_code:
                        response.failure("Empty short code in response")
                        return
                    
                    self.short_codes.append(short_code)
                except (KeyError, AttributeError, ValueError) as e:
                    response.failure(f"Invalid response format: {str(e)}")
            elif response.status_code == 400:
                if "Custom alias already exists" in response.text:
                    response.success()
                else:
                    response.failure(f"Unexpected 400 error: {response.text}")
            else:
                response.failure(f"Status {response.status_code}: {response.text}")

    @task(3)
    def access_short_link(self):
        if not hasattr(self, 'short_codes') or not self.short_codes:
            return
        
        short_code = random.choice(self.short_codes)
        
        with self.client.get(
            f"/links/{short_code}",
            name="/links/[short_code]",
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()
            elif response.status_code != 302:
                response.failure(f"Unexpected status {response.status_code}: {response.text}")

    @task(3)
    def get_link_stats(self):
        if not self.short_codes:
            return
            
        short_code = random.choice(self.short_codes)
        with self.client.get(
            f"/links/{short_code}/stats",
            name="/links/[short_code]/stats",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}: {response.text}")
            elif not isinstance(response.json().get("click_count"), int):
                response.failure("Invalid stats format")

    @task(2)
    def search_link(self):
        if not self.original_urls:
            return
            
        url_to_search = random.choice(self.original_urls)
        encoded_url = quote(url_to_search, safe='')
        
        with self.client.get(
            f"/links/search/{encoded_url}",
            name="/links/search/[original_url]",
            catch_response=True
        ) as response:
            if response.status_code == 0:
                response.failure("Connection failed")
            elif response.status_code != 200:
                response.failure(f"Status {response.status_code}: {response.text}")
