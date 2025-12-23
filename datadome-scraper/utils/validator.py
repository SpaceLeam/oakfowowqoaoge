"""
Response Validator
"""


class ResponseValidator:
    def is_valid(self, resp) -> bool:
        """Check if response is valid (not blocked)"""
        if resp is None:
            return False
        if resp.status_code == 403:
            return False
        if resp.status_code != 200:
            return False
        # Check for captcha/block page indicators
        if 'captcha' in resp.text.lower():
            return False
        if 'blocked' in resp.text.lower():
            return False
        return True

    def is_blocked(self, resp) -> bool:
        """Check if blocked by DataDome"""
        if resp is None:
            return True
        if resp.status_code == 403:
            return True
        if 'geo.captcha-delivery.com' in resp.text:
            return True
        return False
