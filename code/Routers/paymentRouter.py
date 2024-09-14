import datetime
import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from dotenv import load_dotenv
from Core.Shared.Database import Database
from Middlewares.authProtectionMiddlewares import LoginProtected
from Models.Requests.SubscriptionRequestModels import SubscriptionRequest
from Core.Shared.Trails import TRIALS
from Models.Entities import TrialSubscription

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SK")

paymentRouter = APIRouter()

@paymentRouter.post("/create-payment-intent")
async def create_payment_intent(subscription: SubscriptionRequest, userID: str = Depends(LoginProtected)):
    if subscription.plan not in list(TRIALS.keys()):
        raise HTTPException(status_code=400, detail="Invalid subscription plan.")
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=TRIALS[subscription.plan]["price"],
            currency="usd",
            metadata={"uid": userID}
        )

        return {"success": True, "client_secret": intent['client_secret']}
    
    except stripe.error.StripeError as e:
        raise {"success": False, "message": "Stripe related error, try again later."}
    except Exception as e:
        raise {"success": False, "message": str(e)}

@paymentRouter.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            amount_paid = payment_intent['amount']
            uid = payment_intent['metadata']['uid']
            trial = payment_intent['plan']

            trial_subscription = TrialSubscription(
                amount=amount_paid, 
                uid=uid, 
                trial=trial,
                payment_intent= payment_intent
            )

            trialDict = await Database.createTrialSubscription(trial_subscription)
            await Database.updateUser(uid, {"trial": trialDict["trial"]})

        return { "success": True, "message": "Payment success!" }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
