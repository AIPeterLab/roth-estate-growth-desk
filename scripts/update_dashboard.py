#!/usr/bin/env python3
from __future__ import annotations
import json,time
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]; MODE="roth"; START=date(2023,5,18)
SYMBOLS=["QQQ","QLD","SPY","SSO","CHAT","QTUM","BTC-USD"]
HALVING=date(2024,4,20); BTC_BUY=HALVING-timedelta(days=500); BTC_SELL=HALVING+timedelta(days=540)

def fetch(symbol):
    end=int(time.time())+86400; start=int(datetime(2005,1,1,tzinfo=timezone.utc).timestamp())
    u=f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol,safe='')}?period1={start}&period2={end}&interval=1d&events=history&includeAdjustedClose=true"
    with urlopen(Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=40) as r:p=json.load(r)["chart"]["result"][0]
    a=p["indicators"]["adjclose"][0]["adjclose"]
    return {datetime.fromtimestamp(t,timezone.utc).date():float(v) for t,v in zip(p["timestamp"],a) if v is not None}

def sma(vals,n): return sum(vals[-n:])/n if len(vals)>=n else None
def ema(vals,n):
    if len(vals)<n:return None
    x=sum(vals[:n])/n; a=2/(n+1)
    for v in vals[n:]:x=v*a+x*(1-a)
    return x

def aligned(series):
    days=sorted(set.intersection(*(set(x) for x in series.values())))
    return days

def qld_states(q,qld):
    days=sorted(set(q)&set(qld)); sig=0; pos="Cash"; out={}
    qvals=[]
    for i,d in enumerate(days):
        qvals.append(q[d]); e=ema(qvals,200); prior=[qld[x] for x in days[max(0,i-20):i]]
        if len(prior)==20:
            if sig==0 and qld[d]>max(prior):sig=1
            elif sig==1 and qld[d]<min(prior):sig=0
        if sig==1:pos="QLD"
        elif pos=="QLD":pos="QQQ"
        if pos=="QQQ" and e and q[d]<e:pos="Cash"
        out[d]=(pos,sig,e,max(prior) if len(prior)==20 else None,min(prior) if len(prior)==20 else None)
    return out

def spy_states(spy):
    out={}; vals=[]; pos="Cash"
    for d in sorted(spy):
        vals.append(spy[d]); s=sma(vals,200)
        if s:
            if spy[d]>s*1.01:pos="SSO"
            elif spy[d]<s*.99:pos="Cash"
        out[d]=(pos,s)
    return out

def latest_on_or_before(mapping,d):
    k=max(x for x in mapping if x<=d); return mapping[k]

def simulate_roth(px,qs):
    days=[d for d in aligned({k:px[k] for k in ["QQQ","QLD","SPY","CHAT","QTUM","BTC-USD"]}) if d>=date(2023,5,18)]
    values={"QQQ / QLD":3000.0,"CHAT":2500.0,"QTUM":2500.0,"BTC / Cash":2000.0}; prev=days[0]
    b1=10000.0;b2=10000.0
    for d in days[1:]:
        oldpos=qs[prev][0]; values["QQQ / QLD"]*=px[oldpos][d]/px[oldpos][prev] if oldpos!="Cash" else 1
        values["CHAT"]*=px["CHAT"][d]/px["CHAT"][prev]; values["QTUM"]*=px["QTUM"][d]/px["QTUM"][prev]
        if BTC_BUY<=prev<=BTC_SELL:values["BTC / Cash"]*=px["BTC-USD"][d]/px["BTC-USD"][prev]
        b1*=.5*px["QQQ"][d]/px["QQQ"][prev]+.5*px["SPY"][d]/px["SPY"][prev]
        b2*=sum(.2*px[s][d]/px[s][prev] for s in ["QQQ","SPY","BTC-USD","CHAT","QTUM"])
        prev=d
    return values,b1,b2,days[-1]

def status_action(weight,target,lo,hi):return "Rebalance toward target" if weight<lo or weight>hi else "No action"
def write():
    px={s:fetch(s) for s in SYMBOLS}; qs=qld_states(px["QQQ"],px["QLD"]); ss=spy_states(px["SPY"])
    market=max(d for d in set(px["QQQ"])&set(px["SPY"])); qpos,qsig,qema,qhi,qlo=latest_on_or_before(qs,market); spos,ssma=latest_on_or_before(ss,market)
    btc_day=max(px["BTC-USD"]); bpos="BTC" if BTC_BUY<=btc_day<=BTC_SELL else "Cash"; cycle=(btc_day-HALVING).days
    if MODE=="roth":
        vals,b1,b2,market=simulate_roth(px,qs); total=sum(vals.values()); specs=[("QQQ / QLD",30,25,35,qpos,"Risk-on" if qpos=="QLD" else "Defensive"),("CHAT",25,20,30,"CHAT","Hold"),("QTUM",25,20,30,"QTUM","Hold"),("BTC / Cash",20,15,25,bpos,"Risk-on" if bpos=="BTC" else "Risk-off")]
        sleeves=[]
        for n,t,lo,hi,p,s in specs:
            w=vals[n]/total*100;sleeves.append({"name":n,"value":round(vals[n],2),"weight":w,"target":t,"drift":w-t,"position":p,"signal":s,"action":status_action(w,t,lo,hi),"note":"Annual thesis review" if n in ["CHAT","QTUM"] else "Strategy signal controls position"})
        active=total; benchmarks=[{"name":"Active Roth model","value":active,"return_pct":active/10000*100-100,"diff":0,"rule":"30/25/25/20 active rules"},{"name":"Benchmark 1","value":b1,"return_pct":b1/10000*100-100,"diff":b1-active,"rule":"QQQ 50% / SPY 50%"},{"name":"Benchmark 2","value":b2,"return_pct":b2/10000*100-100,"diff":b2-active,"rule":"QQQ/SPY/BTC/CHAT/QTUM 20% each"}]
        outside=[x for x in sleeves if x["action"]!="No action"]; action="Annual rebalance review" if outside else "No action"
        payload={"mark":"R","title":"Roth Estate-Growth Desk","subtitle":"Aggressive long-horizon portfolio · strategy rules before rebalancing","lead_label":"Normalized model value","total_value":active,"required_action":action,"next_review":"May 2027","explanation":"Daily model tracking from a normalized $10,000 start on CHAT's first trading date. Private brokerage balances are not published.","allocation_label":"Active 30/25/25/20 model","tracking_start":"2023-05-18","sleeves":sleeves,"benchmarks":benchmarks,"rules":[{"title":"Signals decide position","copy":"QLD/QQQ/Cash and BTC/Cash change only under their written models."},{"title":"Themes stay invested","copy":"CHAT and QTUM are buy-and-hold sleeves with annual thesis review."},{"title":"Bands decide size","copy":"Rebalance annually only when a sleeve is outside its stated band."},{"title":"Drawdown is not a sell rule","copy":"A valid strategy exit or thesis failure is required."}],"metrics":[{"label":"QQQ strategy","value":f"Hold {qpos}","note":f"Donchian signal {qsig}"},{"label":"BTC strategy","value":f"Hold {bpos}","note":f"Cycle day {cycle}"},{"label":"CHAT close","value":f"${px['CHAT'][market]:,.2f}","note":"Buy and hold"},{"label":"QTUM close","value":f"${px['QTUM'][market]:,.2f}","note":"Buy and hold"},{"label":"Benchmark 1","value":f"${b1:,.0f}","note":"50/50 QQQ/SPY"},{"label":"Benchmark 2","value":f"${b2:,.0f}","note":"Five-way equal weight"}]}
    else:
        base={"IRA_QQQ":4880.0,"IRA_SPY":4880.0,"IRA_BTC":2550.0,"IRA_CASH":2300.0}; total=sum(base.values()); growth=sum(base[k] for k in ["IRA_QQQ","IRA_SPY","IRA_BTC"]); specs=[("IRA_QQQ",40,35,45,qpos,"Risk-on" if qpos=="QLD" else "Defensive"),("IRA_SPY",40,35,45,spos,"Risk-on" if spos=="SSO" else "Risk-off"),("IRA_BTC",20,15,25,bpos,"Risk-on" if bpos=="BTC" else "Risk-off")]; sleeves=[]
        for n,t,lo,hi,p,s in specs:
            w=base[n]/growth*100;sleeves.append({"name":n,"value":base[n],"weight":w,"target":t,"drift":w-t,"position":p,"signal":s,"action":status_action(w,t,lo,hi),"note":"Growth sleeve weight"})
        sleeves.append({"name":"IRA_CASH","value":base["IRA_CASH"],"weight":base["IRA_CASH"]/total*100,"target":base["IRA_CASH"]/total*100,"drift":0,"position":"Cash","signal":"Reserve","action":"Confirm 3-year coverage","note":"Excluded from 40/40/20 target"}); outside=[x for x in sleeves[:3] if x["action"]!="No action"]
        payload={"mark":"IRA","title":"IRA Reserve & Growth Desk","subtitle":"3-year cash reserve plus 40/40/20 growth sleeve","lead_label":"Guide account value","total_value":total,"required_action":"Confirm reserve; "+("rebalance review" if outside else "no growth rebalance"),"next_review":"August 2027","explanation":"Account balances are the August 3 guide values. Daily refresh updates market signals; broker balances remain private and require a manual value update.","allocation_label":"Growth target 40/40/20","tracking_start":"2026-08-03","sleeves":sleeves,"benchmarks":[{"name":"Full IRA guide value","value":total,"return_pct":0,"diff":0,"rule":"Reserve plus growth sleeve"},{"name":"Growth sleeve","value":growth,"return_pct":0,"diff":growth-total,"rule":"QQQ/SPY/BTC only"},{"name":"Cash reserve","value":base["IRA_CASH"],"return_pct":0,"diff":base["IRA_CASH"]-total,"rule":"Withdrawals first for 3 years"}],"rules":[{"title":"Check reserve first","copy":"Confirm IRA_CASH covers the intended three-year withdrawal need."},{"title":"Apply strategy signals","copy":"QQQ, SPY, and BTC sleeve positions follow their source models."},{"title":"Calculate growth-only weights","copy":"Use IRA_QQQ, IRA_SPY, and IRA_BTC for the 40/40/20 test."},{"title":"Defensive signal wins","copy":"Never override an exit merely because a sleeve is below target."}],"metrics":[{"label":"Cash reserve","value":f"${base['IRA_CASH']:,.0f}","note":"3-year protection bucket"},{"label":"Growth sleeve","value":f"${growth:,.0f}","note":"84.3% of full IRA"},{"label":"QQQ strategy","value":f"Hold {qpos}","note":f"Donchian signal {qsig}"},{"label":"SPY strategy","value":f"Hold {spos}","note":f"SPY ${px['SPY'][market]:.2f} · SMA200 ${ssma:.2f}"},{"label":"BTC strategy","value":f"Hold {bpos}","note":f"Cycle day {cycle}"},{"label":"Annual band test","value":"In band" if not outside else "Review","note":"QQQ 35–45 · SPY 35–45 · BTC 15–25"}]}
    payload.update({"market_date":str(market),"generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"footer":"Daily market and strategy refresh at 6:25 PM New York time. Private broker balances are not fetched. This is an operating display, not tax, legal, or individualized financial advice."})
    (ROOT/"data").mkdir(exist_ok=True);(ROOT/"data"/"dashboard.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":write()
