import requests


def send(value1):
    event_name = 'stock'
    key = 'd52n-XLnjmsFF9fZ6AX6sB'
    url = f'https://maker.ifttt.com/trigger/{event_name}/with/key/{key}'
    ret = requests.post(url, json={'value1': value1}).text
