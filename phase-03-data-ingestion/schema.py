from typing import TypedDict, List

class FundSource(TypedDict):
    name: str
    url: str

class FundRecord(TypedDict):
    fund_name: str
    source_url: str
    document_type: str
    last_updated_date: str
    nav: str
    min_sip: str
    fund_size: str
    expense_ratio: str
    rating: str
    raw_text: str
