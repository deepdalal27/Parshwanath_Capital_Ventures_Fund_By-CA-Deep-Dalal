"""Post an image + caption to a LinkedIn Company Page (Posts API + Images API).

Needs an access token with the w_organization_social scope, issued to a page admin, from a
LinkedIn app that has the Community Management API product. See README.md.
"""
import re

import requests

API = "https://api.linkedin.com/rest"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# LinkedIn "little text" reserved characters must be backslash-escaped in commentary.
_RESERVED = re.compile(r"([\\|{}@\[\]()<>#*_~])")


def refresh_access_token(client_id, client_secret, refresh_token):
    r = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token", "refresh_token": refresh_token,
        "client_id": client_id, "client_secret": client_secret,
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def to_commentary(caption, hashtags):
    text = _RESERVED.sub(r"\\\1", caption.strip())
    tags = " ".join("{hashtag|\\#|%s}" % re.sub(r"\W", "", t) for t in hashtags if re.sub(r"\W", "", t))
    return f"{text}\n\n{tags}" if tags else text


class LinkedIn:
    def __init__(self, token, org_id, version):
        self.org = f"urn:li:organization:{org_id}"
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": version,
            "X-Restli-Protocol-Version": "2.0.0",
        })

    def _check(self, r, what):
        if r.status_code >= 300:
            raise RuntimeError(f"LinkedIn {what} failed: HTTP {r.status_code} {r.text[:500]}")
        return r

    def upload_image(self, png_path):
        r = self._check(self.s.post(f"{API}/images?action=initializeUpload", timeout=30,
                                    json={"initializeUploadRequest": {"owner": self.org}}), "image init")
        value = r.json()["value"]
        with open(png_path, "rb") as f:
            self._check(requests.put(value["uploadUrl"], data=f.read(), timeout=120,
                                     headers={"Authorization": self.s.headers["Authorization"]}),
                        "image upload")
        return value["image"]

    def post(self, commentary, image_urn, title, alt_text):
        body = {
            "author": self.org,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                             "thirdPartyDistributionChannels": []},
            "content": {"media": {"id": image_urn, "title": title[:200], "altText": alt_text[:4086]}},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        r = self._check(self.s.post(f"{API}/posts", json=body, timeout=30), "post")
        return r.headers.get("x-restli-id", "")
