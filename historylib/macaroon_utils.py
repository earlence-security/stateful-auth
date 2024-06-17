import json
from pymacaroons import Macaroon, Verifier
from authlib.common.security import generate_token

default_caveat = 'amount < 100 && recipient = Leo && currency = USD'

def generate_macaroon(session, macaroon_model, caveat=default_caveat):

    identifier = generate_token(42)
    key = generate_token(42)

    session.add(macaroon_model(identifier=identifier, root_key=key))
    session.commit()

    m = Macaroon(
        location='statefulauth.com',
        identifier=identifier,
        key=key
    )

    # hardcode the caveat for now
    m.add_first_party_caveat(caveat)

    # Serialize for transport in OAuth token
    serialized = m.serialize()
    return serialized

# varify the macaroon to make sure caveat can be parsed and signature is valid
def verify_macaroon(session, macaroon_model, macaroon):
    v = Verifier()
    v.satisfy_exact(default_caveat)
    m = Macaroon.deserialize(macaroon)
    mac_db = session.query(macaroon_model).filter_by(identifier=m.identifier).first()
    verified = v.verify(
        m,
        mac_db.root_key
    )
    return verified

# stateless policies: When Token POST to "http://127.0.0.1:5000/api/send-money"
# 1. amount < 100.
# 2. amount < 100 && recipient = Leo.
# 3. amount < 100 && recipient = Leo && currency = USD.
def verify_policy(request, macaroon):
    # get the caveat
    m = Macaroon.deserialize(macaroon)
    caveats = m.first_party_caveats()
    for caveat in caveats:
        caveat_text = caveat.caveat_id
        if request.uri == "http://127.0.0.1:5000/api/send-money" and request.method == 'POST':
            body = request.data
            match caveat_text:
                case 'amount < 100':
                    if body['amount'] < 100:
                        return True
                case 'amount < 100 && recipient = Leo':
                    if body['amount'] < 100 and body['recipient'] == 'Leo':
                        return True
                case 'amount < 100 && recipient = Leo && currency = USD':
                    if body['amount'] < 100 and body['recipient'] == 'Leo' and body['currency'] == 'USD':
                        return True
    return False
