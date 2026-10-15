import os
import time
from urllib.parse import parse_qs

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, jsonify
from alipay import AliPay

app = Flask(__name__)

# 内存订单表（仅演示用，生产请换数据库）
# 结构: { out_trade_no: {"status": "PENDING"/"PAID"/"CLOSED", "amount": "0.01"} }
ORDERS = {}


def get_alipay_client():
    from alipay import AliPay

    # ========== 沙箱测试临时硬编码密钥 ==========
    # PKCS#8 私钥（BEGIN PRIVATE KEY）
    app_private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA6gy+dqhNNejC8NEHVNraGLmJcPa07VAevUs2AsjPgEuqumXtYwZnucV5/n5wgE+4DaTb0o8vqVsaDJ/oSZVcIibBU5KAzLwnLXKQ2Pw/KSYPn7uhIZDm/G7ZTrZCl/X/SfNqt71wMTtLCELZOtbmi+V7UPObTw/bcCPbcrK07fVgFbimzz5dNyJtjbUKVGJ9ESzv1OP5BYwuBLXw/Zc4UaJYghKRk9lm6800YA1vp2XWonAYJvmGNJ+toTUDw39as+ILH5rF/PeuJfIfQXwh8dEdPe59D5UpVwmh1tPshyubXe0sAhGkIDjtEwzYYZDFGRAhPlI6FZvOYCGlhvWw0QIDAQABAoIBAEKYzblFunKUgKO1Vri2bUiLwqf6CxFbsuN5+yxfp2uCHFpdlmaO9ATQRB4+LBTWmjCHsGUBiTZPTeI5vgbyEP1Gucvl6/BVuXAdIUocvHwg8GErKnY6nP9HK15STjCfNrz8HmmZ5cqcbIU1QEqVy5QTADvQlWixwmbuTQsd/o2WsRCN4oALXkYJdinJaXlHpLY2knXkN8WJlKd3s4WOn7xnoftUgr0d2DsamCHrKGW3asJ6rDmW7zWzSDJpMvRobv5VsH2AJuf+WqKPdU3tqSWllCbfrP+dyUKFX7i4NS7iRjLsVV006dXdajrmHJjzBUIvwZLTyVBac33GzRRRW+ECgYEA/m+VOwoQvJWRM+/mQJfgRR/bg4Ss2C3aCwgdNDCd5Jfi7wWV2tfc8HuLpZUXxmUa11L49YRI0jqh+AC4kayov5PDY+uNSDNe77h9KPen0q4OepCHOnXFMA8ewjmxPi11S1sR9Opyakxjnj5jb/Uw6bFZjxubQFJyKkokfw2tEOMCgYEA630UHQ4FWFj6KMTNGI2ZMwetVi1rU6rCXEztlyssbrNi9lmVc2PKFv0DBf/1oR62ZhRqTbzlFAJNsLdrkaQ+yEezs1majgoZ3GWhcVPIWftnWNB+mXs+OaI2LpqAK4/5BA0lH3V9heW+rtALYL+gWTEr69ORW+NmNgn8j9yyKbsCgYAc04WDv9svkn519OsQTGSzUC2tk92FTISUlWHBpPRujqq+S9KzjZtRf53Nr7uW1aOZ26OrJUae0tfA4kwG7RndQp9zdZ93G6LY4/0CJDTWULQBPNilTex+SmhAtwqWsc3FMNcy+VDnLCppJkZby9qzz00HQqhvPCgFFItX/bOq4wKBgB4/aK/6txEMDMXj0XxP49e8KrWhC+IpUuHMN9BtCT4G6LU/+IRj0vd09Eh3AjP53+/ou2bU1o/lY9lJFhYVBMNxAlINNl78SSoYG86Utm1ob3PnA/vu6qU4gsEls0TlL1Un4xbRXpguVHnb2zpIIu6R9FRMTqWA5gYW7kwESxY1AoGBANXfnMuF6UUg8qsHCcqtUs2ZeQ0XKeswx/i+03YlUVR0kb8I+9685aydlesCkCIEiEAUSk6uW3yozqWU0MnA2ZHg0PgD1RkXsccnMTjsi+7dqou/l+D3lpTxWe891rQgJdgFC/oRrK6AjIMcdUBZKLGTMjrsLN4F7T+xXoVVTQ/c\n-----END RSA PRIVATE KEY-----"

    alipay_public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmhSSmKA6k9wRl0Z3h8sAqUikJO+h8kSQjKt5uQc0NKg3+8JBX0JA+vDvaS9LC7KU7hR6boVp50eFZ9Abhh2YOZhc1rpppWexNM4eZG8Zvjv/lPR8QaGaOIahEk4EA2GWmeduQ1HNlPqRU0amU3AqETy8TKrIR0fu3tPwKcF3k5cA+BHtKf/wNP9JYyHRBgNviBlQuecpOQ+883LozBeD6NBGNolKS/R1lSh/gYuzTmn5VouzgVH3xS4KfDXsAGfuPv6LeQ1X0ftWM2k4YbxwkGKSsN/EywzJG6xcCn1XpFaxbZ/RUMiaUUnJJADGSSSC7eQJdqac7jOYifuXGkFzaQIDAQAB\n-----END PUBLIC KEY-----"

    app_id = os.environ.get("ALIPAY_APP_ID", "")
    notify_url = os.environ.get("ALIPAY_NOTIFY_URL", "")
    return AliPay(
        appid=app_id,
        app_private_key_string=app_private_key,
        alipay_public_key_string=alipay_public_key,
        sign_type="RSA2",
        debug=False
    )


def mark_paid(out_trade_no):
    """幂等：只有从非 PAID 状态才更新为 PAID"""
    order = ORDERS.get(out_trade_no)
    if order and order["status"] != "PAID":
        order["status"] = "PAID"
        print(f"[ORDER] {out_trade_no} -> PAID")
        return True
    return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pay/create')
def create_payment():
    """发起支付，重定向到支付宝沙箱网关"""
    alipay = get_alipay_client()

    out_trade_no = "TEST" + str(int(time.time() * 1000))
    total_amount = "0.01"
    subject = "测试商品"

    # 先落到本地订单表
    ORDERS[out_trade_no] = {"status": "PENDING", "amount": total_amount}

    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=out_trade_no,
        total_amount=total_amount,
        subject=subject,
        return_url=os.environ.get('ALIPAY_RETURN_URL', '')
    )

    gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
    return redirect(gateway + "?" + order_string)


@app.route('/alipay/notify', methods=['POST'])
def alipay_notify():
    """异步通知：支付宝主动推送，必须返回纯文本 success"""
    alipay = get_alipay_client()

    raw_data = request.get_data(as_text=True)
    data = parse_qs(raw_data)
    params = {k: v[0] for k, v in data.items()}

    signature = params.pop('sign', None)
    params.pop('sign_type', None)

    if not signature or not alipay.verify(params, signature):
        return 'fail', 400

    trade_status = params.get('trade_status')
    out_trade_no = params.get('out_trade_no')

    if trade_status == 'TRADE_SUCCESS':
        mark_paid(out_trade_no)

    return 'success'


@app.route('/pay/result')
def pay_result():
    """同步跳转返回页，页面会带上订单号，前端自动查询真实状态"""
    out_trade_no = request.args.get('out_trade_no', '')
    return render_template('result.html', out_trade_no=out_trade_no)


@app.route('/pay/query/<out_trade_no>')
def query_payment(out_trade_no):
    """主动查询订单支付状态（回调兜底）"""
    # 先看本地表是否已经标记为 PAID（回调可能已经先到了）
    local = ORDERS.get(out_trade_no)
    if local and local["status"] == "PAID":
        return jsonify({"status": "paid", "source": "local"})

    alipay = get_alipay_client()

    try:
        result = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    trade_status = result.get('trade_status')

    if trade_status == 'TRADE_SUCCESS':
        mark_paid(out_trade_no)
        return jsonify({"status": "paid", "source": "alipay", "trade_status": trade_status})
    elif trade_status == 'WAIT_BUYER_PAY':
        return jsonify({"status": "pending", "source": "alipay", "trade_status": trade_status})
    elif trade_status == 'TRADE_CLOSED':
        if local:
            local["status"] = "CLOSED"
        return jsonify({"status": "closed", "source": "alipay", "trade_status": trade_status})
    else:
        # 订单可能还没同步到支付宝，或 code 非 10000
        code = result.get('code')
        if code == '40004':  # 交易不存在
            return jsonify({"status": "not_found", "source": "alipay", "code": code})
        return jsonify({"status": "unknown", "source": "alipay", "result": result})


@app.route('/health')
def health():
    return {"status": "healthy"}, 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
