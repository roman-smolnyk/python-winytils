import asyncio
import sys
import logging

try:
    from winrt.windows.security.credentials.ui import (
        UserConsentVerificationResult, UserConsentVerifier,
        UserConsentVerifierAvailability)
except ImportError:
    pip = "pip install winrt.windows.security.credentials.ui"
    logging.getLogger("winytils").debug(pip)


async def windows_hello_prompt_async() -> int:
    """result 0 means success"""
    availability = await UserConsentVerifier.check_availability_async()
    
    if availability != UserConsentVerifierAvailability.AVAILABLE:
        logging.warning("Windows Hello not available on this system.")
        return UserConsentVerifierAvailability.DEVICE_NOT_PRESENT

    result = await UserConsentVerifier.request_verification_async("Please authenticate with Windows Hello")

    return result # result == UserConsentVerificationResult.VERIFIED


def windows_hello_prompt() -> int:
    return asyncio.run(windows_hello_prompt_async())

