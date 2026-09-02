
import os
from datetime import datetime
from decimal import Decimal
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]=os.getenv("DATABASE_URL","sqlite:///banking.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
app.config["SECRET_KEY"]=os.getenv("SECRET_KEY","change-this-in-production")
db=SQLAlchemy(app)
CORS(app,origins=os.getenv("FRONTEND_ORIGIN","http://localhost:5173"))

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    email=db.Column(db.String(160),unique=True,nullable=False)
    password_hash=db.Column(db.String(255),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)

class Account(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    account_number=db.Column(db.String(24),unique=True,nullable=False)
    account_type=db.Column(db.String(30),default="Savings")
    balance=db.Column(db.Numeric(12,2),default=0)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)

class Transaction(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    account_id=db.Column(db.Integer,db.ForeignKey("account.id"),nullable=False)
    type=db.Column(db.String(20),nullable=False)
    amount=db.Column(db.Numeric(12,2),nullable=False)
    description=db.Column(db.String(255),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)

def token_for(user):
    return jwt.encode({"user_id":user.id},app.config["SECRET_KEY"],algorithm="HS256")

def current_user():
    h=request.headers.get("Authorization","")
    if not h.startswith("Bearer "): return None
    try:
        d=jwt.decode(h[7:],app.config["SECRET_KEY"],algorithms=["HS256"])
        return db.session.get(User,d["user_id"])
    except Exception: return None

@app.get("/api/health")
def health(): return jsonify(status="ok",service="banking-api")

@app.post("/api/register")
def register():
    d=request.get_json() or {}
    name,email,password=d.get("name"),d.get("email","").lower().strip(),d.get("password")
    if not name or not email or not password or len(password)<8:
        return jsonify(error="Name, email and password (8+ chars) are required"),400
    if User.query.filter_by(email=email).first(): return jsonify(error="Email already registered"),409
    u=User(name=name.strip(),email=email,password_hash=generate_password_hash(password))
    db.session.add(u); db.session.flush()
    a=Account(account_number=f"10{u.id:08d}",balance=Decimal("1000.00"),user_id=u.id)
    db.session.add(a); db.session.flush()
    db.session.add(Transaction(account_id=a.id,type="CREDIT",amount=Decimal("1000.00"),description="Opening balance"))
    db.session.commit()
    return jsonify(token=token_for(u),user={"id":u.id,"name":u.name,"email":u.email}),201

@app.post("/api/login")
def login():
    d=request.get_json() or {}
    u=User.query.filter_by(email=d.get("email","").lower().strip()).first()
    if not u or not check_password_hash(u.password_hash,d.get("password","")):
        return jsonify(error="Invalid credentials"),401
    return jsonify(token=token_for(u),user={"id":u.id,"name":u.name,"email":u.email})

@app.get("/api/dashboard")
def dashboard():
    u=current_user()
    if not u:return jsonify(error="Unauthorized"),401
    accounts=Account.query.filter_by(user_id=u.id).all()
    return jsonify(user={"id":u.id,"name":u.name,"email":u.email},
      accounts=[{"id":a.id,"account_number":a.account_number,"account_type":a.account_type,"balance":float(a.balance or 0)} for a in accounts])

@app.get("/api/transactions/<int:account_id>")
def transactions(account_id):
    u=current_user(); a=db.session.get(Account,account_id)
    if not u or not a or a.user_id!=u.id:return jsonify(error="Unauthorized"),401
    rows=Transaction.query.filter_by(account_id=a.id).order_by(Transaction.created_at.desc()).all()
    return jsonify(transactions=[{"id":t.id,"type":t.type,"amount":float(t.amount),"description":t.description,"created_at":t.created_at.isoformat()} for t in rows])

@app.post("/api/transfer")
def transfer():
    u=current_user(); d=request.get_json() or {}; a=db.session.get(Account,d.get("account_id"))
    try: amount=Decimal(str(d.get("amount","0")))
    except: amount=Decimal("0")
    if not u or not a or a.user_id!=u.id:return jsonify(error="Unauthorized"),401
    if amount<=0 or amount>a.balance:return jsonify(error="Invalid amount or insufficient funds"),400
    a.balance=Decimal(a.balance)-amount
    db.session.add(Transaction(account_id=a.id,type="DEBIT",amount=amount,description=(d.get("description") or "Transfer").strip()))
    db.session.commit()
    return jsonify(message="Transfer completed",balance=float(a.balance))

with app.app_context(): db.create_all()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)),debug=True)
