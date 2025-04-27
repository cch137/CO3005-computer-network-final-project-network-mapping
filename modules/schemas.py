from pydantic import BaseModel, HttpUrl, IPvAnyAddress
from typing import List, Optional


class PageSchema(BaseModel):
    url: HttpUrl
    domain: str
    title: str
    description: str
    markdown: str
    delay_time: str
    links: List[HttpUrl]


class NodeSchema(BaseModel):
    ip_addr: IPvAnyAddress
    name: Optional[str] = None
    domains: List[str]
    neighbours: List[str]
