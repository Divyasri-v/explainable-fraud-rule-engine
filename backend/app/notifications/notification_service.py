"""High-risk alerting. DEMO_MODE=true logs + stores; otherwise AWS SNS/SES."""
import logging

from app.config import Settings, get_settings
from app.models import NotificationLog, Transaction
from app.utils import inr

log = logging.getLogger("fraud.notify")


class NotificationService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def _compose(self, txn: Transaction):
        subject = f"[{txn.risk_level}] Fraud alert: {txn.transaction_id} scored {txn.risk_score}/100"
        lines = [
            f"Transaction {txn.transaction_id} for customer {txn.customer_id} crossed the high-risk threshold.",
            f"Amount: {inr(float(txn.amount))} | Location: {txn.city or 'unknown'} | Merchant: {txn.merchant or 'n/a'}",
            f"Risk score: {txn.risk_score} ({txn.risk_level})",
            "Triggered rules:",
            *[f"  - {f.rule_name} (+{f.risk_points}): {f.reason}" for f in txn.flags],
            "(DEMO DATA - not a real transaction)" if self.settings.demo_mode else "",
        ]
        return subject[:100], "\n".join(l for l in lines if l)

    def send_high_risk_alert(self, db, txn: Transaction) -> NotificationLog:
        s = self.settings
        subject, message = self._compose(txn)
        channel, status, error = "DEMO", "SIMULATED", None
        try:
            if s.demo_mode:
                log.warning("DEMO NOTIFICATION (no AWS call made)\n%s\n%s", subject, message)
            elif s.notify_channel == "ses":
                channel = "SES"
                import boto3
                boto3.client("ses", region_name=s.aws_region).send_email(
                    Source=s.ses_sender_email,
                    Destination={"ToAddresses": [s.ses_recipient_email]},
                    Message={"Subject": {"Data": subject}, "Body": {"Text": {"Data": message}}})
                status = "SENT"
            else:
                channel = "SNS"
                import boto3
                boto3.client("sns", region_name=s.aws_region).publish(
                    TopicArn=s.sns_topic_arn, Subject=subject, Message=message)
                status = "SENT"
        except Exception as exc:  # never fail the transaction because an alert failed
            log.exception("Alert delivery failed")
            status, error = "FAILED", str(exc)[:500]

        record = NotificationLog(transaction_id=txn.id, channel=channel, status=status,
                                 subject=subject, message=message, error=error)
        db.add(record)
        db.commit()
        return record
