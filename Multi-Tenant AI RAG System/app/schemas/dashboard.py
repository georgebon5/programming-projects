"""
Admin dashboard schemas — tenant statistics.
"""

from datetime import datetime

from pydantic import BaseModel


class TenantStats(BaseModel):
    tenant_name: str
    total_users: int
    active_users: int
    total_documents: int
    processed_documents: int
    failed_documents: int
    total_chunks: int
    total_conversations: int
    total_messages: int
    storage_bytes: int


class RecentActivity(BaseModel):
    type: str  # "upload", "chat", "user_joined"
    description: str
    timestamp: datetime


class DashboardResponse(BaseModel):
    stats: TenantStats
    recent_activity: list[RecentActivity]
