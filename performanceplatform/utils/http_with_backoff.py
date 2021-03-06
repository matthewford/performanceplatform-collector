from httplib2 import *
from httplib2 import DEFAULT_MAX_REDIRECTS
import logging
import time
from performanceplatform.collector.logging_setup import (
    extra_fields_from_exception)

_MAX_RETRIES = 5


class HttpWithBackoff(Http):

    def request(self,
                uri,
                method="GET",
                body=None,
                headers=None,
                redirections=DEFAULT_MAX_REDIRECTS,
                connection_type=None):

        delay = 10

        for n in range(_MAX_RETRIES):
            response = super(HttpWithBackoff, self).request(
                uri,
                method,
                body,
                headers,
                redirections,
                connection_type)
            response_headers = response[0]
            code = response_headers.status
            if code in [403, 502, 503]:
                retry_info = ('{} request for {} failed with code {} '
                              '(Attempt {} of {}).'.format(method, uri, code,
                                                           n + 1,
                                                           _MAX_RETRIES))
                if n + 1 < _MAX_RETRIES:
                    retry_info += ' Retrying in {} seconds...'.format(delay)
                logging.info(retry_info)
                time.sleep(delay)
                delay *= 2
            else:
                # bad status codes should be handled by the Google API
                # client in the normal way
                return response

        # we made _MAX_RETRIES requests but none worked
        logging.error(
            'Max retries exceeded for {}'.format(uri),
            # HttpLibException doesnt exist but this fits with the format
            # for logging other request failures
            extra={
                'exception_class': 'HttpLibException',
                'exception_message': '{}: {}'.format(response[0].status,
                                                     response[0].reason)
            }
        )
        return response
