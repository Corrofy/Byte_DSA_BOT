import httpx
from typing import Optional, Any
from bot.config import settings

RECENT_AC_SUBMISSIONS_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
    statusDisplay
    lang
  }
}
"""

USER_PUBLIC_PROFILE_QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      aboutMe
      realName
      userAvatar
    }
    submitStats {
      acSubmissionNum {
        difficulty
        count
        submissions
      }
    }
  }
}
"""

PROBLEMSET_QUERY = """
query problemsetQuestionList(
  $categorySlug: String
  $limit: Int
  $skip: Int
  $filters: QuestionListFilterInput
) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: $filters
  ) {
    total: totalNum
    questions: data {
      questionFrontendId
      title
      titleSlug
      difficulty
      isPaidOnly
      topicTags {
        name
        slug
      }
      acRate
    }
  }
}
"""


class LeetCodeService:
    def __init__(self):
        self.url = settings.LEETCODE_GRAPHQL_URL
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": settings.LEETCODE_USER_AGENT,
            "Referer": "https://leetcode.com",
        }

    async def _post(self, query: str, variables: dict[str, Any]) -> Optional[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(
                    self.url,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                )
                if res.status_code == 200:
                    return res.json()
                return None
            except Exception as e:
                print(f"[LeetCodeService] Request error: {e}")
                return None

    async def get_user_profile(self, username: str) -> Optional[dict[str, Any]]:
        data = await self._post(USER_PUBLIC_PROFILE_QUERY, {"username": username})
        if data and "data" in data and data["data"].get("matchedUser"):
            return data["data"]["matchedUser"]
        return None

    async def get_recent_accepted_submissions(self, username: str, limit: int = 20) -> list[dict[str, Any]]:
        data = await self._post(RECENT_AC_SUBMISSIONS_QUERY, {"username": username, "limit": limit})
        if data and "data" in data and data["data"].get("recentAcSubmissionList"):
            return data["data"]["recentAcSubmissionList"]
        return []

    async def verify_user_bio_code(self, username: str, code: str) -> bool:
        profile = await self.get_user_profile(username)
        if not profile or not profile.get("profile"):
            return False
        about_me = profile["profile"].get("aboutMe") or ""
        return code.strip() in about_me


leetcode_service = LeetCodeService()
