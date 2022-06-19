import plaid 
import uuid
import json
import datetime 
from decouple import config 
from plaid.api import plaid_api 
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest


PLAID_CLIENT_ID = config('PLAID_CLIENT_ID')
PLAID_SECRET = config('PLAID_SECRET')
PLAID_ENV = config('PLAID_ENV')
PLAID_REDIRECT_URI = config('PLAID_REDIRECT_URI')
PLAID_WEBHOOK = config('PLAID_WEBHOOK')
PLAID_PRODUCTS = config('PLAID_PRODUCTS')
PLAID_COUNTRY_CODES = config('PLAID_COUNTRY_CODES')

host = plaid.Environment.Development if PLAID_ENV == 'development' else plaid.Environment.Production if PLAID_ENV == 'production' else plaid.Environment.Sandbox 

configuration = plaid.Configuration(
    host=host,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

def save(date, data):
    with open('data.json', 'wb') as f:
        f.write(json.dumps({'date': '%s' % (date), 'data': data}))

def create_link_token():
    try:
        request = LinkTokenCreateRequest(
            client_name='Plaid Bot',
            language='en',
            products=list(map(lambda k: Products(k))),
            country_codes=list(map(lambda k: CountryCode(k))),
            user=LinkTokenCreateRequestUser(
                client_user_id=uuid.uuid4().hex
            )
        )
        response = client.link_token_create(request)
        return response.link_token
    except plaid.ApiException as e:
        print(e)
        return json.loads(e.body)


def get_access_token(public_token):
    try:
        request = ItemPublicTokenExchangeRequest(
            public_token=public_token 
        )
        response = client.item_public_token_exchange(request)
        access_token = response.access_token 
        item_id = response.item_id 
        now = datetime.datetime.now()
        save(now, access_token)
        return response.to_dict()
    except plaid.ApiException as e:
        return json.loads(e.body)


def get_balance(access_token):
    try:
        request = AccountsBalanceGetRequest(
            access_token=access_token
        )
        response = client.accounts_balance_get(request)
        save(datetime.datetime.now(), response.to_dict())
        print(response.to_dict())
        return response.to_dict()
    except plaid.ApiException as e:
        error_response = json.loads(e.body)
        return error_response 


def get_accounts(access_token):
    try:
        request = AccountsGetRequest(
            access_token=access_token
        )
        response = client.accounts_get(request)
        print(response.to_dict())
        return response.to_dict()
    except plaid.ApiException as e:
        error_response = json.loads(e.body)
        return error_response 

def get_transactions(access_token):
    cursor = ''
    added = []
    modified = []
    removed = [] 
    has_more = True
    try:
        while has_more:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
            )
            response = client.transactions_sync(request).to_dict()
            added.extend(response['added'])
            modified.extend(response['modified'])
            removed.extend(response['removed'])
            has_more = response['has_more']
            cursor = response['next_cursor']
            print(response)

        latest_transactions = sorted(added, key=lambda t: t['date'])[-10:]
        save(datetime.datetime.now(), latest_transactions)
        return latest_transactions

    except plaid.ApiException as e:
        error_response = json.loads(e.body)
        return error_response


