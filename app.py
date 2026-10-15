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
    return AliPay(
        appid=os.environ.get('ALIPAY_APP_ID', ''),
        app_notify_url=os.environ.get('ALIPAY_NOTIFY_URL', ''),
        app_private_key_string=os.environ.get('ALIPAY_PRIVATE_KEY', ''),
        alipay_public_key_string=os.environ.get('ALIPAY_PUBLIC_KEY', ''),
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