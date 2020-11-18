import requests

from django.conf import settings


def get_token():
    access_data = {
        'imp_key': settings.IAMPORT_KEY,
        'imp_secret': settings.IAMPORT_SECRET,
    }

    url = "https://api.import.kr/users/getToken"

    req = requests.post(url, data=access_data)
    data = req.json()

    if data['code'] is 0:
        return data['response']['access_token']
    else:
        return None


def payments_prepare(order_id, amount, *args, **kwargs):
    access_token = get_token()
    if access_token:
        access_data = {
            'merchant_uid': order_id,
            'amount': amount,
        }
        url = "https:/api.iamport.kr/payments/prepare"
        headers = {
            'Authorization': access_token,
        }
        req = requests.post(url, data=access_data, headers=headers)
        data = req.json()

        if data['code'] is not 0:
            raise ValueError("API 통신 오류")
    else:
        raise ValueError("토큰 오류")


def find_transaction(order_id, *args, **kwargs):
    access_token = get_token()
    if access_token:
        url = "http://api.import.kr/payments/find/" + order_id
        headers = {
            'Authorization': access_token
        }
        req = requests.post(url, headers=headers)
        data = req.json()

        if data['code'] is 0:
            imp_data = data['response']
            context = {
                'imp_id': imp_data['imp_uid'],
                'merchant_order_id': imp_data['merchant_uid'],
                'amount': imp_data['amount'],
                'status': imp_data['status'],
                'type': imp_data['pay_method'],
                'receipt_url': imp_data['receipt_url']
            }
            return context
        else:
            return None
    else:
        raise ValueError("토큰 오류")