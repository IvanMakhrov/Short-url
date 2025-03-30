from locust import HttpUser, task, between
import random
import string


class ShortLinkUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://0.0.0.0:8000"
    
    def on_start(self):
        """Initialize with some short codes"""
        self.short_codes = []
        self.original_urls = []
        
        for _ in range(3):
            self.create_short_link()
    
    @task(5)
    def create_short_link(self):
        """Test creating short links without authentication"""
        url = f"https://example.com/{''.join(random.choices(string.ascii_lowercase, k=10))}"
        self.original_urls.append(url)
        
        payload = {"original_url": url}
        
        if random.random() < 0.3:
            payload["custom_alias"] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        with self.client.post(
            "/links/shorten",
            json=payload,
            name="/links/shorten (unauthenticated)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                short_code = response.json()["short_code"].split("/")[-1]
                self.short_codes.append(short_code)
            elif response.status_code != 400:
                response.failure(f"Unexpected error: {response.text}")

    @task(10)
    def access_short_link(self):
        """Test accessing short links"""
        if not self.short_codes:
            return self.create_short_link()
            
        short_code = random.choice(self.short_codes)
        with self.client.get(
            f"/links/{short_code}", 
            name="/links/[short_code]",
            catch_response=True
        ) as response:
            if response.status_code >= 400:
                response.failure(f"Failed to access short link: {response.text}")

    @task(3)
    def get_link_stats(self):
        """Test getting link statistics"""
        if not self.short_codes:
            return
            
        short_code = random.choice(self.short_codes)
        with self.client.get(
            f"/links/{short_code}/stats",
            name="/links/[short_code]/stats",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get stats: {response.text}")
            elif not response.json().get("clicks"):
                response.failure("Invalid stats format")

    @task(2)
    def search_link(self):
        """Test searching links by original URL"""
        if not self.original_urls:
            return
            
        url_to_search = random.choice(self.original_urls)
        with self.client.get(
            f"/links/search/{url_to_search}",
            name="/links/search/[original_url]",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Search failed: {response.text}")

    @task(1)
    def test_nonexistent_short_link(self):
        """Test accessing a non-existent short link"""
        fake_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        with self.client.get(
            f"/links/{fake_code}",
            name="/links/[invalid_short_code]",
            catch_response=True
        ) as response:
            if response.status_code != 404:
                response.failure(f"Expected 404 for invalid short code, got {response.status_code}")
