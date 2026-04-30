from random import randint

import factory
from faker import Faker

from apps.metrics.models import MetricEvent

fake = Faker()


class MetricEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MetricEvent

    event_type = factory.Faker("word")

    @factory.LazyAttribute
    def metadata(self):
        return {
            "post_id": randint(1, 10_000),
            "ip": fake.ipv4(),
            "user_agent": fake.user_agent(),
            "referer": fake.url(),
            "user_id": fake.uuid4(),
            "is_bot": fake.boolean(),
        }
