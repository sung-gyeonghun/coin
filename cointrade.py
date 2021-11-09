import time
import pyupbit
import datetime
import schedule
import requests
from fbprophet import Prophet


#사용자의 Access key
access = "your-access"
#사용자의 Secret key
secret = "your-secret"

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
 
myToken = "xoxb-2688517439926-2695254372579-jz3WWkgATSjktnq0XL4hrxhp"
def dbgout(message):
    
    """실행된 후 slack으로 동시에 전송"""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
    post_message(myToken,"#coin", strbuf)




def get_start_time(tk):
    #시작 시간
    """시작 시간 조회"""
    X = pyupbit.get_ohlcv(tk, interval="day", count=1)
    start_time = X.index[0]
    return start_time

def get_balance(tk):
    #잔고 조회
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == tk:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_target_price(tk, k):
    #변동성 돌파 전략 이용. 변동성 K값 구하기.
    """변동성 돌파 전략으로 매수 목표가 조회"""
    X = pyupbit.get_ohlcv(tk, interval="day", count=2)
    target_price = X.iloc[0]['close'] + (X.iloc[0]['high'] - X.iloc[0]['low']) * k
    return target_price

def get_current_price(tk):
    #현재가격
    """현재가 조회"""
    return pyupbit.get_orderbook(tk=tk)["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(tk):
    #Prohbet으로 종가 예측
    """예측한 종가"""
    global predicted_close_price
    X = pyupbit.get_ohlcv(tk, interval="minute60")
    X = X.reset_index()
    X['ds'] = X['index']
    X['y'] = X['close']
    data = X[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue
predict_price("KRW-ETH")
schedule.every().hour.do(lambda: predict_price("KRW-ETH"))

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("자동매매가 시작되었습니다!")

#시작시 slack으로 알림
post_message(myToken,"#coin", "자동매매가 시작되었습니다!")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-ETH")
        end_time = start_time + datetime.timedelta(days=1)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-ETH", 0.5) #변동성 K값
            current_price = get_current_price("KRW-ETH")
            if target_price < current_price and current_price < predicted_close_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-ETH", krw*0.9995)
        else:
            eth = get_balance("ETH")
            if eth > 0.00008:
                upbit.sell_market_order("KRW-ETH", eth*0.9995)
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)