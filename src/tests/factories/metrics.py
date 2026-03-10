import factory
from faker import Faker

from apps.metrics.models import MetricEvent

fake = Faker()


def _make_metadata(obj):
    match obj.event_type:
        case MetricEvent.EventType.LOGIN:
            return {
                "ip": fake.ipv4(),
                "user_agent": fake.user_agent(),
                "user_id": obj.user.id,
            }
        case MetricEvent.EventType.LOGIN_FAILED:
            return {
                "ip": fake.ipv4(),
                "user_agent": fake.user_agent(),
                "username": fake.user_name(),
            }
        case MetricEvent.EventType.UPLOAD_CREATED:
            return {
                "purpose": fake.random_element(
                    elements=["avatar", "thumbnail", "attachment"]
                ),
                "size": fake.random_int(min=1, max=1024 * 1024),
            }
        case MetricEvent.EventType.POST_READ:
            return {
                "post_slug": fake.slug(),
            }


class MetricEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MetricEvent

    event_type = factory.Faker("random_element", elements=MetricEvent.EventType.values)
    user = factory.SubFactory("tests.factories.EditorFactory")
    metadata = factory.LazyAttribute(_make_metadata)
