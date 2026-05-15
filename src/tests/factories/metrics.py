import factory
from faker import Faker

from apps.metrics.models import MetricRecord

fake = Faker()


class MetricRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MetricRecord

    event_type = factory.Faker("word")

    @factory.LazyAttribute
    def metadata(self):
        return {
            "post_slug": fake.slug(),
            "ip": fake.ipv4(),
            "user_agent": fake.user_agent(),
            "referer": fake.url(),
            "user_id": fake.uuid4(),
            "is_bot": fake.boolean(),
        }
