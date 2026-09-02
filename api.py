import json,os,time,uuid
import redis
from flask import Flask,jsonify,request

app=Flask(__name__)
client=redis.Redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"),decode_responses=True)
WEBHOOK="day317:webhook:"
DELIVERY="day317:delivery:"
QUEUE="day317:deliveries"

@app.get("/")
def home():
    return jsonify(service="day317-webhook-delivery",message="Webhook delivery service is running")

@app.get("/health")
def health():
    try:
        client.ping()
        return jsonify(status="healthy",redis="connected")
    except redis.RedisError:
        return jsonify(status="unhealthy"),503

@app.post("/webhooks")
def register():
    data=request.get_json(silent=True) or {}
    url=str(data.get("url","")).strip()
    secret=str(data.get("secret","")).strip()
    if not url or not secret:
        return jsonify(error="url and secret are required"),400
    wid=str(uuid.uuid4())
    item={"id":wid,"url":url,"secret":secret,"created_at":time.time()}
    client.set(WEBHOOK+wid,json.dumps(item))
    return jsonify(id=wid,url=url),201

@app.get("/webhooks")
def list_webhooks():
    result=[]
    for key in client.scan_iter(match=WEBHOOK+"*"):
        raw=client.get(key)
        if raw:
            item=json.loads(raw);item.pop("secret",None);result.append(item)
    return jsonify(webhooks=result)

@app.post("/events")
def publish():
    data=request.get_json(silent=True) or {}
    event=data.get("event")
    if not event:
        return jsonify(error="event is required"),400
    ids=[]
    for key in client.scan_iter(match=WEBHOOK+"*"):
        raw=client.get(key)
        if not raw: continue
        webhook=json.loads(raw)
        did=str(uuid.uuid4())
        item={"id":did,"webhook_id":webhook["id"],"event":event,
              "data":data.get("data",{}),"status":"queued","attempts":0,
              "created_at":time.time()}
        client.set(DELIVERY+did,json.dumps(item))
        client.rpush(QUEUE,did)
        ids.append(did)
    return jsonify(event=event,deliveries=ids),202

@app.get("/deliveries/<delivery_id>")
def delivery(delivery_id):
    raw=client.get(DELIVERY+delivery_id)
    if not raw: return jsonify(error="delivery not found"),404
    return jsonify(json.loads(raw))

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
