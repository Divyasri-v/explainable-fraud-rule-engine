"""Central configuration. Everything comes from environment variables (.env)."""
import os
from functools import lru_cache
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    database_url: str
    demo_mode: bool
    notify_channel: str
    aws_region: str
    sns_topic_arn: str
    ses_sender_email: str
    ses_recipient_email: str
    medium_min: int
    high_min: int
    critical_min: int
    fraud_threshold: int
    alert_threshold: int
    disabled_rules: tuple
    cors_origins: tuple


@lru_cache
def get_settings() -> Settings:
    critical = env_int("RISK_CRITICAL_MIN", 80)
    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql+psycopg2://fraud_user:fraud_pass@localhost:5432/fraud_db"),
        demo_mode=env_bool("DEMO_MODE", True),
        notify_channel=os.getenv("NOTIFY_CHANNEL", "sns").lower(),
        aws_region=os.getenv("AWS_REGION", "ap-south-1"),
        sns_topic_arn=os.getenv("SNS_TOPIC_ARN", ""),
        ses_sender_email=os.getenv("SES_SENDER_EMAIL", ""),
        ses_recipient_email=os.getenv("SES_RECIPIENT_EMAIL", ""),
        medium_min=env_int("RISK_MEDIUM_MIN", 30),
        high_min=env_int("RISK_HIGH_MIN", 60),
        critical_min=critical,
        fraud_threshold=env_int("FRAUD_THRESHOLD", 30),
        alert_threshold=env_int("ALERT_THRESHOLD", critical),
        disabled_rules=tuple(x.strip() for x in os.getenv("DISABLED_RULES", "").split(",") if x.strip()),
        cors_origins=tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()),
    )
