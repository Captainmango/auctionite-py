class CannotBidOnOwnListing(BaseException):
    """Cannot bid on own listing."""

    def __str__(self) -> str:
        return "Cannot bid on own listing."


class BidBehindCurrentLeader(BaseException):
    """Bid submitted is behind current leader"""

    def __str__(self) -> str:
        return "Bid submitted is behind current leader"


class BidBelowStartingPrice(BaseException):
    """Bid is below starting price"""

    def __str__(self) -> str:
        return "Bid is below starting price"


class AlreadyLeadingAuction(BaseException):
    """Already leading auction"""

    def __str__(self) -> str:
        return "Already leading auction"
