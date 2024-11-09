import os
import json
import logging
from urllib.parse import urljoin
import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class APIRequestHandler:
    def __init__(self, base_url):
        load_dotenv()
        self.base_url = base_url
        self.http_proxy = os.environ.get("HTTP_PROXY")
        self.https_proxy = os.environ.get("HTTPS_PROXY")
        self.verify_ssl = os.environ.get("VERIFY_SSL", "False").lower() in ("true", "1")

        # Proxies
        self.proxies = (
            {"http": self.http_proxy, "https": self.https_proxy}
            if self.http_proxy or self.https_proxy
            else None
        )

        # Default headers
        self.headers = {
            "Content-Type": "application/json",
        }

    def add_header(self, key, value):
        """Add or update a header."""
        self.headers[key] = value

    def _merge_headers(self, additional_headers):
        """Merge additional headers with default headers, giving precedence to additional headers."""
        if additional_headers:
            merged_headers = self.headers.copy()
            merged_headers.update(
                additional_headers
            )  # Override with additional headers
            return merged_headers
        return self.headers

    def _make_request(
        self, session, method, url, payload=None, headers=None, stream=False
    ):
        """Internal method to make a request and handle exceptions."""
        try:
            response = session.request(
                method,
                url,
                json=payload,
                headers=headers,
                verify=self.verify_ssl,
                stream=stream,
                proxies=self.proxies,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Error: {e}")
            return None

    def make_request(
        self, endpoint, method="POST", payload=None, additional_headers=None
    ):
        """Make a synchronous request and return JSON response or None on error."""
        url = urljoin(self.base_url, endpoint)
        headers = self._merge_headers(additional_headers)
        with requests.Session() as session:
            response = self._make_request(
                session, method, url, payload=payload, headers=headers, stream=False
            )
            if response:
                try:
                    response.raise_for_status()
                    return response.json()
                except ValueError:
                    logger.error("Failed to parse JSON response")
                    return None
            return None

    def stream_request(self, endpoint, payload=None, additional_headers=None):
        """Make a request with streaming and yield each chunk."""
        url = urljoin(self.base_url, endpoint)
        headers = self._merge_headers(additional_headers)
        with requests.Session() as session:
            response = self._make_request(
                session, "POST", url, payload=payload, headers=headers, stream=True
            )
            if response and response.status_code == 200:
                buffer = ""
                for chunk in response.iter_lines(decode_unicode=True):
                    if chunk:
                        line = chunk.strip()
                        if line == "data: [DONE]":
                            yield "[DONE]"
                            break
                        if line.startswith("data: "):
                            try:
                                json_data = json.loads(line[6:])
                                yield json_data
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding JSON from stream: {e}")
            else:
                logger.error("Streaming request failed")


# Example usage
def main():
    handler = APIRequestHandler("https://api.example.com")
    payload = {"message": "Test request"}
    additional_headers = {"X-Custom-Header": "CustomValue"}

    # Synchronous request
    result = handler.make_request(
        "/endpoint", payload=payload, additional_headers=additional_headers
    )
    print("Synchronous response:", result)

    # Streaming request
    print("Streaming response:")
    for chunk in handler.stream_request(
        "/stream-endpoint", payload=payload, additional_headers=additional_headers
    ):
        print(chunk)


if __name__ == "__main__":
    main()
