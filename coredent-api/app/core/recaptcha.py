import logging

logger = logging.getLogger(__name__)


class CaptchaVerificationError(Exception):
    pass


async def verify_recaptcha_v3(token: str, action: str, min_score: float = 0.5) -> None:
    logger.warning("reCAPTCHA v3 verification is not configured; accepting all tokens")
