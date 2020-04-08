import logging


class FileFormatter(logging.Formatter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record):
        from ipware import get_client_ip

        try:
            request = record.request
        except AttributeError:
            record.client_ip = None
            record.is_routable = None
            record.request_size = None
            record.method = None
        else:
            client_ip, is_routable = get_client_ip(request)

            record.client_ip = client_ip
            record.is_routable = is_routable
            record.request_size = request.META['CONTENT_LENGTH']
            record.method = request.method

        record.status_msg, record.endpoint = getattr(record, 'args', [None]*2)

        return super().format(record)
