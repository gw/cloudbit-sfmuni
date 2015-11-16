"""Module for interacting with the nextbus API."""

import logging

import requests
import xmltodict

from services.muni.stop_map import STOP_MAP

LOGGER = logging.getLogger()

NEXTBUS_URL = """ \
    http://webservices.nextbus.com/service/publicXMLFeed? \
        command={command} \
        &a=sf-muni \
        &r={route} \
        &s={stop_tag} \
"""


def get_next(route, stop_name, direction, num):
    """Get the next two predicted arrival times, in minutes.

    Uses the NextBus 'predictions' API command.

    Arguments:
        route (str) Name of Muni line. Must exist in STOP_MAP
        stop_name (str) Name of stop. Must exist in STOP_MAP
        direction (str) 'inbound' or 'outbound'
        num (int) Number of buses for which to return predictions

    """
    command = 'predictions'

    # Get stop tag
    try:
        stop_tag = STOP_MAP[route][stop_name][direction]
    except KeyError:
        LOGGER.warn('Invalid route, stop_name, or direction')
        raise

    # Insert URL params and send GET
    url = NEXTBUS_URL.format(command=command,
                             route=route,
                             stop_tag=stop_tag) \
                     .replace(' ', '')

    LOGGER.info('Hitting NextBus.')
    res = requests.get(url)

    # XML to dict
    parsed = xmltodict.parse(res.text)

    # 'direction' won't exist inside 'predictions' if no predictions
    try:
        predictions = parsed['body'] \
                            ['predictions'] \
                            ['direction'] \
                            ['prediction']
    except KeyError:
        LOGGER.info('No predictions.')
        LOGGER.debug('Parsed XML: %s', parsed)
        raise NoPredictionsError

    predictions_min = get_sorted_minutes(predictions)
    result = predictions_min[:num]

    LOGGER.info('Next {direction} {route} buses: {buses}'
                .format(direction=direction,
                        route=route,
                        buses=result))

    return result


def get_sorted_minutes(predictions):
    """Pull the earliest two predictions, in minutes, from parsed NextBus XML."""
    return sorted([int(p['@minutes']) for p in predictions])


# CUSTOM EXCEPTIONS
class NoPredictionsError(Exception):
    """Successful API call, but no predictions."""
    pass

