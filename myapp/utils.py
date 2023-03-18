from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.conf import settings
from zoomus import ZoomClient


class EmailTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return (six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified))


class ConfirmationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, meeting, timestamp):
        return (six.text_type(meeting.pk)+six.text_type(timestamp)+six.text_type(meeting.is_confirmed))

generate_email_token = EmailTokenGenerator()
generate_confirmation_token = ConfirmationTokenGenerator()

def create_zoom_link(topic, start_time, duration, password, agenda):
    # Use the zoomus package to create a Zoom meeting
    client = ZoomClient('<API key>', '<API secret>')
    meeting = {
        'topic': topic,
        'start_time': start_time,
        'duration': duration,
        'password': password,
        'agenda': agenda,
        'settings': {
            'join_before_host': True,
            'mute_upon_entry': False,
            'approval_type': 2,
            'audio': 'voip',
            'auto_recording': 'cloud'
        }
    }
    response = client.meeting.create(meeting)

    # Extract the join URL from the response and return it
    join_url = response.get('join_url', None)
    return join_url