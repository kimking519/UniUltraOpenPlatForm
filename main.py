from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response, Cookie, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Sills.base import init_db, get_db_connection
from Sills.db_daily import get_daily_list, add_daily, update_daily
from Sills.db_emp import get_emp_list, add_employee, batch_import_text, verify_login, change_password, update_employee, delete_employee
from Sills.db_vendor import add_vendor, batch_import_vendor_text, update_vendor, delete_vendor
from Sills.db_cli import add_cli, batch_import_cli_text, update_cli, delete_cli
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

@app.post("/emp/import/csv")
async def emp_import_csv(csv_file: UploadFile = File(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/emp", status_code=303)
    content = await csv_file.read()
    try:
        text = content.decode('utf-8-sig').strip()
    except UnicodeDecodeError:
        text = content.decode('gbk', errors='replace').strip()
        
    if '\n' in text:
        text = text.split('\n', 1)[1] # skip header
    success_count, errors = batch_import_text(text)
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

from Sills.base import get_paginated_list

@app.get("/vendor", response_class=HTMLResponse)
async def vendor_page(request: Request, page: int = 1, search: str = "", current_user: dict = Depends(login_required)):
    search_kwargs = {"vendor_name": search} if search else None
    result = get_paginated_list("uni_vendor", page=page, search_kwargs=search_kwargs)
    return templates.TemplateResponse("vendor.html", {
        "request": request, "active_page": "vendor", "current_user": current_user,
        "items": result["items"], "total_pages": result["total_pages"], 
        "page": page, "search": search, "active_page": "vendor"
    })

@app.post("/vendor/add")
async def vendor_add(
    vendor_name: str = Form(...), address: str = Form(""), qq: str = Form(""),
    wechat: str = Form(""), email: str = Form(""), remark: str = Form(""),
    current_user: dict = Depends(login_required)
):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/vendor", status_code=303)
    data = {
        "vendor_name": vendor_name, "address": address, "qq": qq,
        "wechat": wechat, "email": email, "remark": remark
    }
    add_vendor(data)
    return RedirectResponse(url="/vendor", status_code=303)

@app.post("/vendor/import")
async def vendor_import(import_text: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/vendor", status_code=303)
    success_count, errors = batch_import_vendor_text(import_text)
    return RedirectResponse(url=f"/vendor?import_success={success_count}&errors={len(errors)}", status_code=303)

@app.post("/vendor/import/csv")
async def vendor_import_csv(csv_file: UploadFile = File(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/vendor", status_code=303)
    content = await csv_file.read()
    try:
        text = content.decode('utf-8-sig').strip()
    except UnicodeDecodeError:
        text = content.decode('gbk', errors='replace').strip()
        
    if '\n' in text:
        text = text.split('\n', 1)[1] # skip header
    success_count, errors = batch_import_vendor_text(text)
    return RedirectResponse(url=f"/vendor?import_success={success_count}&errors={len(errors)}", status_code=303)

@app.post("/api/vendor/update")
async def vendor_update_api(vendor_id: str = Form(...), field: str = Form(...), value: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无权限"}
    allowed_fields = ['vendor_name', 'address', 'qq', 'wechat', 'email', 'remark']
    if field not in allowed_fields:
        return {"success": False, "message": "非法字段"}
    success, msg = update_vendor(vendor_id, {field: value})
    return {"success": success, "message": msg}

@app.post("/api/vendor/delete")
async def vendor_delete_api(vendor_id: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无权限"}
    success, msg = delete_vendor(vendor_id)
    return {"success": success, "message": msg}

@app.get("/cli", response_class=HTMLResponse)
async def cli_page(request: Request, page: int = 1, search: str = "", current_user: dict = Depends(login_required)):
    search_kwargs = {"cli_name": search} if search else None
    result = get_paginated_list("uni_cli", page=page, search_kwargs=search_kwargs)
    
    # Needs employees for dropdown
    employees, _ = get_emp_list(page=1, page_size=1000)
    
    return templates.TemplateResponse("cli.html", {
        "request": request, "active_page": "cli", "current_user": current_user,
        "items": result["items"], "total_pages": result["total_pages"], 
        "page": page, "search": search, "employees": employees
    })

@app.post("/cli/add")
async def cli_add(
    cli_name: str = Form(...), region: str = Form("韩国"), credit_level: str = Form("A"),
    margin_rate: float = Form(10.0), emp_id: str = Form(...), website: str = Form(""),
    payment_terms: str = Form(""), email: str = Form(""), phone: str = Form(""),
    remark: str = Form(""), current_user: dict = Depends(login_required)
):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/cli", status_code=303)
    data = {
        "cli_name": cli_name, "region": region, "credit_level": credit_level,
        "margin_rate": margin_rate, "emp_id": emp_id, "website": website,
        "payment_terms": payment_terms, "email": email, "phone": phone, "remark": remark
    }
    add_cli(data)
    return RedirectResponse(url="/cli", status_code=303)

@app.post("/cli/import")
async def cli_import(import_text: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/cli", status_code=303)
    success_count, errors = batch_import_cli_text(import_text)
    return RedirectResponse(url=f"/cli?import_success={success_count}&errors={len(errors)}", status_code=303)

@app.post("/cli/import/csv")
async def cli_import_csv(csv_file: UploadFile = File(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/cli", status_code=303)
    content = await csv_file.read()
    try:
        text = content.decode('utf-8-sig').strip()
    except UnicodeDecodeError:
        text = content.decode('gbk', errors='replace').strip()
        
    if '\n' in text:
        text = text.split('\n', 1)[1] # skip header
    success_count, errors = batch_import_cli_text(text)
    return RedirectResponse(url=f"/cli?import_success={success_count}&errors={len(errors)}", status_code=303)

@app.post("/api/cli/update")
async def cli_update_api(cli_id: str = Form(...), field: str = Form(...), value: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无权限"}
    allowed_fields = ['cli_name', 'region', 'credit_level', 'margin_rate', 'emp_id', 'website', 'payment_terms', 'email', 'phone', 'remark']
    if field not in allowed_fields:
        return {"success": False, "message": "非法字段"}
    
    if field == 'margin_rate':
        try: 
            val = float(value)
            success, msg = update_cli(cli_id, {field: val})
            return {"success": success, "message": msg}
        except: 
            return {"success": False, "message": "利润率必须是数字"}
        
    success, msg = update_cli(cli_id, {field: value})
    return {"success": success, "message": msg}

@app.post("/api/cli/delete")
async def cli_delete_api(cli_id: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无权限"}
    success, msg = delete_cli(cli_id)
    return {"success": success, "message": msg}

@app.get("/quote", response_class=HTMLResponse)
async def quote_page(request: Request, current_user: dict = Depends(login_required)):
    return templates.TemplateResponse("quote.html", {"request": request, "active_page": "quote", "current_user": current_user})

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
