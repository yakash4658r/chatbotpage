import json, requests, time, uuid, traceback
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from pymongo import MongoClient

# --- CONFIG ---
MONGO_URI = "mongodb+srv://criticmailservice_db_user:Critictechchatbotmongodb@chatbot.cs4z16o.mongodb.net/?appName=Chatbot"
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbzSY7ERRtnV79JnthuKp03LxqY0B46-ZXaSzOKyhTaA11wjuFqBByM8DZXx5qogWoXo/exec"
CF_APP_ID = "TEST10908756027378371954d27f636c65780901"
CF_SECRET_KEY = "cfsk_ma_test_449308e23dafb10504d6d10cd276d9ef_9c2d7ab0"
CASHFREE_URL = "https://sandbox.cashfree.com/pg/orders"

# MongoDB connection
mongo_orders = None
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client['Chatbot_DB']
    mongo_orders = db['orders']
    # Check if connection is alive
    client.server_info() 
except:
    mongo_orders = None

def home(request):
    return render(request, 'index.html')

@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = "ORD_" + str(uuid.uuid4())[:10].replace("-", "")
            clean_phone = str(data.get('phone')).strip()[-10:]

            # 1. Save to SQLite
            Order.objects.create(
                name=data.get('name'), email=data.get('email'),
                phone=clean_phone, plan=data.get('plan'),
                amount=float(data.get('amount')), orderId=order_id
            )

            # 2. Save to MongoDB (Corrected check)
            if mongo_orders is not None:
                try:
                    mongo_orders.insert_one({
                        "name": data.get('name'), "email": data.get('email'),
                        "phone": clean_phone, "plan": data.get('plan'),
                        "amount": float(data.get('amount')), "order_id": order_id,
                        "status": "PENDING", "created_at": time.ctime()
                    })
                except:
                    pass

            # 3. Call Cashfree
            payload = {
                "order_amount": float(data.get('amount')),
                "order_currency": "INR",
                "order_id": order_id,
                "customer_details": {
                    "customer_id": "CUST_" + str(uuid.uuid4())[:8],
                    "customer_name": data.get('name'),
                    "customer_email": data.get('email'),
                    "customer_phone": clean_phone
                },
                "order_meta": {
                    "return_url": f"http://127.0.0.1:8000/payment-status?order_id={order_id}"
                }
            }
            headers = {
                'x-client-id': CF_APP_ID.strip(),
                'x-client-secret': CF_SECRET_KEY.strip(),
                'x-api-version': '2023-08-01',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(CASHFREE_URL, json=payload, headers=headers, timeout=10)
            return JsonResponse(response.json())

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)

def payment_status(request):
    order_id = request.GET.get('order_id')
    headers = {
        'x-client-id': CF_APP_ID.strip(),
        'x-client-secret': CF_SECRET_KEY.strip(),
        'x-api-version': '2023-08-01'
    }
    
    try:
        response = requests.get(f"{CASHFREE_URL}/{order_id}", headers=headers).json()

        if response.get('order_status') == "PAID":
            order = Order.objects.get(orderId=order_id)
            order.paymentStatus = 'SUCCESS'
            order.save()

            # MongoDB Update (Corrected check)
            if mongo_orders is not None:
                try: mongo_orders.update_one({"order_id": order_id}, {"$set": {"status": "SUCCESS"}})
                except: pass

            # Send Google Sheet
            try: requests.post(GOOGLE_SHEET_URL, json={"name": order.name, "email": order.email, "phone": order.phone, "plan": order.plan, "amount": float(order.amount), "status": "PAID"}, timeout=5)
            except: pass

            # Send Email
            try: send_mail(f"New Sale! {order.name}", f"Plan: {order.plan}\nAmount: {order.amount}", settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER])
            except: pass

            return render(request, 'success.html', {'order': order})
        else:
            return HttpResponse("<h1>❌ Payment Pending/Failed</h1><a href='/'>Go Home</a>")
    except Exception as e:
        return HttpResponse(f"<h1>Error checking payment</h1><p>{str(e)}</p>")