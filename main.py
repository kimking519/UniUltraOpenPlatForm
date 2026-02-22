from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Sills.base import init_db, get_db_connection
from Sills.db_daily import get_daily_list, add_daily, update_daily
from Sills.db_emp import get_emp_list, add_employee, batch_import_text, verify_login, change_password, update_employee, delete_employee
import uvicorn

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    init_db()

async def get_current_user(request: Request, emp_id: str = Cookie(None), rule: str = Cookie(None), account: str = Cookie(None)):
    if not emp_id or not rule:
        return None
    return {"emp_id": emp_id, "rule": rule, "account": account}

async def login_required(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return current_user

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
        
    with get_db_connection() as conn:
        cli_count = conn.execute("SELECT COUNT(*) FROM uni_cli").fetchone()[0]
        emp_count = conn.execute("SELECT COUNT(*) FROM uni_emp").fetchone()[0]
        order_sum = conn.execute("SELECT IFNULL(SUM(paid_amount), 0) FROM uni_order").fetchone()[0]
        
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "active_page": "dashboard",
        "current_user": current_user,
        "stats": {
            "cli_count": cli_count,
            "emp_count": emp_count,
            "order_sum": order_sum
        }
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = "", account: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "error": error, "account": account})

@app.post("/login")
async def login(response: Response, account: str = Form(...), password: str = Form(...)):
    if account == "Admin" and password == "uni519":
        # System init backdoor, just in case
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="emp_id", value="000")
        response.set_cookie(key="account", value="Admin")
        response.set_cookie(key="rule", value="3")
        return response

    ok, user, msg = verify_login(account, password)
    if not ok:
        # Redirect back to login with error message and retained account
        return RedirectResponse(url=f"/login?error={msg}&account={account}", status_code=303)
    
    # Check if first time login (password is default 12345)
    from Sills.db_emp import hash_password
    if user['password'] == hash_password('12345'):
        response = RedirectResponse(url="/change_password", status_code=303)
        response.set_cookie(key="emp_id", value=user['emp_id'])
        response.set_cookie(key="account", value=user['account'])
        response.set_cookie(key="rule", value=user['rule'])
        return response

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="emp_id", value=str(user['emp_id']))
    response.set_cookie(key="account", value=str(user['account']))
    response.set_cookie(key="rule", value=str(user['rule']))
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("emp_id")
    response.delete_cookie("rule")
    response.delete_cookie("account")
    return response

@app.get("/change_password", response_class=HTMLResponse)
async def change_pwd_page(request: Request, current_user: dict = Depends(get_current_user), error: str = ""):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("change_pwd.html", {"request": request, "current_user": current_user, "error": error})

@app.post("/change_password")
async def change_pwd_post(new_password: str = Form(...), confirm_password: str = Form(...), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    if new_password == '12345':
        return RedirectResponse(url="/change_password?error=新密码不能为12345", status_code=303)
    if new_password != confirm_password:
        return RedirectResponse(url="/change_password?error=两次输入的密码不一致", status_code=303)
        
    change_password(current_user['emp_id'], new_password)
    return RedirectResponse(url="/", status_code=303)

# Placeholder routes for modules 1-8
@app.get("/daily", response_class=HTMLResponse)
async def daily_page(request: Request, page: int = 1, current_user: dict = Depends(login_required)):
    items, total = get_daily_list(page=page)
    return templates.TemplateResponse("daily.html", {
        "request": request, 
        "active_page": "daily",
        "current_user": current_user,
        "items": items,
        "total": total,
        "page": page
    })

@app.post("/daily/add")
async def daily_add(currency_code: int = Form(...), exchange_rate: float = Form(...), current_user: dict = Depends(login_required)):
    from datetime import datetime
    record_date = datetime.now().strftime('%Y-%m-%d')
    success, msg = add_daily(record_date, currency_code, exchange_rate)
    return RedirectResponse(url="/daily", status_code=303)

@app.post("/api/daily/update")
async def daily_update_api(id: int = Form(...), exchange_rate: float = Form(...), current_user: dict = Depends(login_required)):
    success, msg = update_daily(id, exchange_rate)
    return {"success": success, "message": msg}

@app.get("/emp", response_class=HTMLResponse)
async def emp_page(request: Request, page: int = 1, search: str = "", current_user: dict = Depends(login_required)):
    items, total = get_emp_list(page=page, search=search)
    return templates.TemplateResponse("emp.html", {
        "request": request, 
        "active_page": "emp",
        "current_user": current_user,
        "items": items,
        "total": total,
        "page": page,
        "search": search
    })

@app.post("/emp/add")
async def emp_add(
    emp_name: str = Form(...), department: str = Form(""), position: str = Form(""),
    contact: str = Form(""), account: str = Form(...), hire_date: str = Form(...),
    rule: str = Form("1"), remark: str = Form(""),
    current_user: dict = Depends(login_required)
):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/emp", status_code=303)
        
    data = {
        "emp_name": emp_name, "department": department, "position": position,
        "contact": contact, "account": account, "password": "12345",
        "hire_date": hire_date,
        "rule": rule, "remark": remark
    }
    success, msg = add_employee(data)
    return RedirectResponse(url="/emp", status_code=303)

@app.post("/emp/import")
async def emp_import(import_text: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/emp", status_code=303)
    success_count, errors = batch_import_text(import_text)
    return RedirectResponse(url=f"/emp?import_success={success_count}&errors={len(errors)}", status_code=303)

@app.post("/api/emp/update")
async def emp_update_api(emp_id: str = Form(...), field: str = Form(...), value: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无权限"}
    # Only allow certain fields
    allowed_fields = ['account', 'department', 'position', 'rule', 'contact', 'hire_date', 'remark']
    if field not in allowed_fields:
        return {"success": False, "message": "非法字段"}
    
    success, msg = update_employee(emp_id, {field: value})
    return {"success": success, "message": msg}

@app.post("/api/emp/delete")
async def emp_delete_api(emp_id: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无权限"}
    success, msg = delete_employee(emp_id)
    return {"success": success, "message": msg}

@app.get("/emp", response_class=HTMLResponse)
async def emp_page(request: Request, page: int = 1, search: str = ""):
    items, total = get_emp_list(page=page, search=search)
    return templates.TemplateResponse("emp.html", {
        "request": request, 
        "active_page": "emp",
        "items": items,
        "total": total,
        "page": page,
        "search": search
    })

@app.post("/emp/add")
async def emp_add(
    emp_name: str = Form(...), department: str = Form(""), position: str = Form(""),
    contact: str = Form(""), account: str = Form(...), password: str = Form("123456"),
    rule: str = Form("员工"), remark: str = Form("")
):
    data = {
        "emp_name": emp_name, "department": department, "position": position,
        "contact": contact, "account": account, "password": password,
        "rule": rule, "remark": remark
    }
    success, msg = add_employee(data)
    return RedirectResponse(url="/emp", status_code=303)

@app.post("/emp/import")
async def emp_import(import_text: str = Form(...)):
    success_count, errors = batch_import_text(import_text)
    return RedirectResponse(url=f"/emp?import_success={success_count}&errors={len(errors)}", status_code=303)

@app.get("/cli", response_class=HTMLResponse)
async def cli_page(request: Request, current_user: dict = Depends(login_required)):
    return templates.TemplateResponse("cli.html", {"request": request, "active_page": "cli", "current_user": current_user})

@app.get("/quote", response_class=HTMLResponse)
async def quote_page(request: Request, current_user: dict = Depends(login_required)):
    return templates.TemplateResponse("quote.html", {"request": request, "active_page": "quote", "current_user": current_user})

@app.get("/vendor", response_class=HTMLResponse)
async def vendor_page(request: Request, current_user: dict = Depends(login_required)):
    return templates.TemplateResponse("vendor.html", {"request": request, "active_page": "vendor", "current_user": current_user})

@app.get("/offer", response_class=HTMLResponse)
async def offer_page(request: Request, current_user: dict = Depends(login_required)):
    return templates.TemplateResponse("offer.html", {"request": request, "active_page": "offer", "current_user": current_user})

@app.get("/order", response_class=HTMLResponse)
async def order_page(request: Request, current_user: dict = Depends(login_required)):
    return templates.TemplateResponse("order.html", {"request": request, "active_page": "order", "current_user": current_user})

@app.get("/buy", response_class=HTMLResponse)
async def buy_page(request: Request, current_user: dict = Depends(login_required)):
    return templates.TemplateResponse("buy.html", {"request": request, "active_page": "buy", "current_user": current_user})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
