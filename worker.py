import hashlib,hmac,json,os,time
import redis,requests

client=redis.Redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"),decode_responses=True)
WEBHOOK="day317:webhook:"
DELIVERY="day317:delivery:"
QUEUE="day317:deliveries"
MAX_ATTEMPTS=5
BASE_DELAY=5

def sign(secret,payload):
    return hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()

def process(did):
    raw=client.get(DELIVERY+did)
    if not raw:return
    delivery=json.loads(raw)
    raw_webhook=client.get(WEBHOOK+delivery["webhook_id"])
    if not raw_webhook:
        delivery["status"]="failed";delivery["error"]="webhook not found"
        client.set(DELIVERY+did,json.dumps(delivery));return
    webhook=json.loads(raw_webhook)
    payload=json.dumps({"delivery_id":did,"event":delivery["event"],"data":delivery["data"]},separators=(",",":"))
    delivery["attempts"]+=1
    try:
        response=requests.post(webhook["url"],data=payload,headers={
            "Content-Type":"application/json",
            "X-Webhook-Signature":sign(webhook["secret"],payload),
            "X-Webhook-Delivery":did
        },timeout=5)
        delivery["last_status_code"]=response.status_code
        if 200<=response.status_code<300:
            delivery["status"]="delivered";delivery["delivered_at"]=time.time()
        else: raise RuntimeError(f"HTTP {response.status_code}")
    except (requests.RequestException,RuntimeError) as exc:
        delivery["error"]=str(exc)
        if delivery["attempts"]<MAX_ATTEMPTS:
            delay=BASE_DELAY*(2**(delivery["attempts"]-1))
            delivery["status"]="retrying";delivery["next_attempt_at"]=time.time()+delay
            client.set(DELIVERY+did,json.dumps(delivery))
            time.sleep(delay);client.rpush(QUEUE,did);return
        delivery["status"]="failed";delivery["failed_at"]=time.time()
    client.set(DELIVERY+did,json.dumps(delivery))

def run():
    print("Webhook worker started",flush=True)
    while True:
        try:
            item=client.blpop(QUEUE,timeout=5)
            if item: process(item[1])
        except redis.RedisError as exc:
            print(f"Redis error: {exc}",flush=True);time.sleep(3)

if __name__=="__main__":run()
