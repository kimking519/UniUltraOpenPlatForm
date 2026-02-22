from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response, Cookie, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Sills.base import init_db, get_db_connection
from Sills.db_daily import get_daily_list, add_daily, update_daily
from Sills.db_emp import get_emp_list, add_employee, batch_import_text, verify_login, change_password, update_employee, delete_employee
from Sills.db_vendor import add_vendor, batch_import_vendor_text, update_vendor, delete_vendor
from Sills.db_cli import get_cli_list, add_cli, batch_import_cli_text, update_cli, delete_cli
from Sills.db_quote import get_quote_list, add_quote, batch_import_quote_text, update_quote, delete_quote, batch_delete_quote
from Sills.db_offer import get_offer_list, add_offer, batch_import_offer_text, update_offer, delete_offer, batch_delete_offer, batch_convert_from_quote
from Sills.db_order import get_order_list, add_order, update_order_status, update_order, delete_order, batch_import_order, batch_delete_order, batch_convert_from_offer
from Sills.db_buy import get_buy_list, add_buy, update_buy_node, update_buy, delete_buy, batch_import_buy, batch_delete_buy, batch_convert_from_order

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
    if current_user['rule'] != '3':
        return {"success": False, "message": "仅管理员可删除"}
    success, msg = delete_cli(cli_id)
    return {"success": success, "message": msg}

# ---------------- Quote Module ----------------
@app.get("/quote", response_class=HTMLResponse)
async def quote_page(request: Request, current_user: dict = Depends(login_required), page: int = 1, page_size: int = 20, search: str = "", start_date: str = "", end_date: str = "", cli_id: str = ""):
    results, total = get_quote_list(page=page, page_size=page_size, search_kw=search, start_date=start_date, end_date=end_date, cli_id=cli_id)
    total_pages = (total + page_size - 1) // page_size
    cli_list, _ = get_cli_list(page=1, page_size=1000)
    return templates.TemplateResponse("quote.html", {
        "request": request,
        "active_page": "quote",
        "current_user": current_user,
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "search": search,
        "start_date": start_date,
        "end_date": end_date,
        "cli_id": cli_id,
        "cli_list": cli_list
    })

@app.post("/quote/add")
async def quote_add(request: Request, current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/quote", status_code=303)
    form = await request.form()
    data = dict(form)
    ok, msg = add_quote(data)
    import urllib.parse
    msg_param = urllib.parse.quote(msg)
    success = 1 if ok else 0
    return RedirectResponse(url=f"/quote?msg={msg_param}&success={success}", status_code=303)

@app.post("/quote/import")
async def quote_import_text(batch_text: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/quote", status_code=303)
    success_count, errors = batch_import_quote_text(batch_text)
    err_msg = ""
    if errors:
        import urllib.parse
        err_msg = "&msg=" + urllib.parse.quote(errors[0])
    return RedirectResponse(url=f"/quote?import_success={success_count}&errors={len(errors)}{err_msg}", status_code=303)

@app.post("/quote/import/csv")
async def quote_import_csv(csv_file: UploadFile = File(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/quote", status_code=303)
    content = await csv_file.read()
    try:
        text = content.decode('utf-8-sig').strip()
    except UnicodeDecodeError:
        text = content.decode('gbk', errors='replace').strip()
        
    # Pass full text to sill
    success_count, errors = batch_import_quote_text(text)
    err_msg = ""
    if errors:
        import urllib.parse
        err_msg = "&msg=" + urllib.parse.quote(errors[0])
    return RedirectResponse(url=f"/quote?import_success={success_count}&errors={len(errors)}{err_msg}", status_code=303)

@app.post("/api/quote/update")
async def quote_update_api(quote_id: str = Form(...), field: str = Form(...), value: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无修改权限"}
        
    allowed_fields = ['cli_id', 'inquiry_mpn', 'quoted_mpn', 'inquiry_brand', 'inquiry_qty', 'target_price_rmb', 'cost_price_rmb', 'remark']
    if field not in allowed_fields:
        return {"success": False, "message": "非法字段"}
        
    if field in ['inquiry_qty', 'target_price_rmb', 'cost_price_rmb']:
        try:
            val = float(value) if 'price' in field else int(value)
            success, msg = update_quote(quote_id, {field: val})
            return {"success": success, "message": msg}
        except:
            return {"success": False, "message": "必须是数字"}
            
    success, msg = update_quote(quote_id, {field: value})
    return {"success": success, "message": msg}

@app.post("/api/quote/delete")
async def quote_delete_api(quote_id: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] != '3':
        return {"success": False, "message": "仅管理员可删除"}
    success, msg = delete_quote(quote_id)
    return {"success": success, "message": msg}

@app.post("/api/quote/batch_delete")
async def quote_batch_delete_api(request: Request, current_user: dict = Depends(login_required)):
    if current_user['rule'] != '3':
        return {"success": False, "message": "仅管理员可删除"}
    data = await request.json()
    ids = data.get("ids", [])
    success, msg = batch_delete_quote(ids)
    return {"success": success, "message": msg}

@app.get("/api/quote/info")
async def get_quote_info_api(id: str, current_user: dict = Depends(login_required)):
    from Sills.base import get_db_connection
    with get_db_connection() as conn:
        row = conn.execute("SELECT q.*, c.cli_name FROM uni_quote q LEFT JOIN uni_cli c ON q.cli_id = c.cli_id WHERE q.quote_id = ?", (id,)).fetchone()
        if row:
            return {"success": True, "data": dict(row)}
        return {"success": False, "message": "未找到"}

@app.post("/api/quote/export_offer_csv")
async def quote_export_offer_csv(request: Request, current_user: dict = Depends(login_required)):
    data = await request.json()
    ids = data.get("ids", [])
    if not ids:
        return {"success": False, "message": "未选择任何记录进行导出"}
        
    from Sills.base import get_db_connection
    placeholders = ','.join(['?'] * len(ids))
    with get_db_connection() as conn:
        quotes = conn.execute(f"SELECT * FROM uni_quote WHERE quote_id IN ({placeholders})", ids).fetchall()
        
    import io, csv
    output = io.StringIO()
    # Excel will render utf-8-sig properly
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['需求编号','询价型号','报价型号','询价品牌','报价品牌','询价数量','实际数量','报价数量','成本价','报价','平台','供应商编号','货期','交期','报价语句','备注'])
    
    for q in quotes:
        q_dict = dict(q)
        writer.writerow([
            q_dict.get('quote_id', ''), q_dict.get('inquiry_mpn', ''), q_dict.get('quoted_mpn', ''),
            q_dict.get('inquiry_brand', ''), '', q_dict.get('inquiry_qty', 0), '', '',
            q_dict.get('cost_price_rmb', 0.0), '', '', '', '', '', '', q_dict.get('remark', '')
        ])
        
    return {"success": True, "csv_content": output.getvalue()}

# ---------------- Offer Module ----------------
@app.get("/offer", response_class=HTMLResponse)
async def offer_page(request: Request, current_user: dict = Depends(login_required), page: int = 1, page_size: int = 20, search: str = "", start_date: str = "", end_date: str = "", cli_id: str = ""):
    results, total = get_offer_list(page=page, page_size=page_size, search_kw=search, start_date=start_date, end_date=end_date, cli_id=cli_id)
    total_pages = (total + page_size - 1) // page_size
    from Sills.base import get_paginated_list
    vendor_data = get_paginated_list('uni_vendor', page=1, page_size=1000)
    vendor_list = vendor_data['items']
    cli_data = get_paginated_list('uni_cli', page=1, page_size=1000)
    cli_list = cli_data['items']
    return templates.TemplateResponse("offer.html", {
        "request": request,
        "active_page": "offer",
        "current_user": current_user,
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "search": search,
        "start_date": start_date,
        "end_date": end_date,
        "cli_id": cli_id,
        "vendor_list": vendor_list,
        "cli_list": cli_list
    })

@app.post("/offer/add")
async def offer_add(request: Request, current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/offer", status_code=303)
    form = await request.form()
    data = dict(form)
    ok, msg = add_offer(data, current_user['emp_id'])
    import urllib.parse
    msg_param = urllib.parse.quote(msg)
    success = 1 if ok else 0
    return RedirectResponse(url=f"/offer?msg={msg_param}&success={success}", status_code=303)

@app.post("/offer/import")
async def offer_import_text(batch_text: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/offer", status_code=303)
    success_count, errors = batch_import_offer_text(batch_text, current_user['emp_id'])
    err_msg = ""
    if errors:
        import urllib.parse
        err_msg = "&msg=" + urllib.parse.quote(errors[0])
    return RedirectResponse(url=f"/offer?import_success={success_count}&errors={len(errors)}{err_msg}", status_code=303)

@app.post("/offer/import/csv")
async def offer_import_csv(csv_file: UploadFile = File(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return RedirectResponse(url="/offer", status_code=303)
    content = await csv_file.read()
    try:
        text = content.decode('utf-8-sig').strip()
    except UnicodeDecodeError:
        text = content.decode('gbk', errors='replace').strip()
        
    # Pass full text to sill
    success_count, errors = batch_import_offer_text(text, current_user['emp_id'])
    err_msg = ""
    if errors:
        import urllib.parse
        err_msg = "&msg=" + urllib.parse.quote(errors[0])
    return RedirectResponse(url=f"/offer?import_success={success_count}&errors={len(errors)}{err_msg}", status_code=303)

@app.post("/api/offer/update")
async def offer_update_api(offer_id: str = Form(...), field: str = Form(...), value: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] not in ['3', '0']:
        return {"success": False, "message": "无修改权限"}
        
    allowed_fields = ['quote_id', 'inquiry_mpn', 'quoted_mpn', 'inquiry_brand', 'quoted_brand', 
                      'inquiry_qty', 'actual_qty', 'quoted_qty', 'cost_price_rmb', 'offer_price_rmb', 
                      'platform', 'vendor_id', 'date_code', 'delivery_date', 'offer_statement', 'remark']
    if field not in allowed_fields:
        return {"success": False, "message": "非法字段"}
        
    if field in ['inquiry_qty', 'actual_qty', 'quoted_qty', 'cost_price_rmb', 'offer_price_rmb']:
        try:
            val = float(value) if 'price' in field else int(value)
            success, msg = update_offer(offer_id, {field: val})
            return {"success": success, "message": msg}
        except:
            return {"success": False, "message": "必须是数字"}
            
    success, msg = update_offer(offer_id, {field: value})
    return {"success": success, "message": msg}

@app.post("/api/offer/delete")
async def offer_delete_api(offer_id: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] != '3':
        return {"success": False, "message": "仅管理员可删除"}
    success, msg = delete_offer(offer_id)
    return {"success": success, "message": msg}

@app.post("/api/offer/batch_delete")
async def offer_batch_delete_api(request: Request, current_user: dict = Depends(login_required)):
    if current_user['rule'] != '3':
        return {"success": False, "message": "仅管理员可删除"}
    data = await request.json()
    ids = data.get("ids", [])
    success, msg = batch_delete_offer(ids)
    return {"success": success, "message": msg}

@app.post("/api/offer/export_csv")
async def offer_export_csv(request: Request, current_user: dict = Depends(login_required)):
    data = await request.json()
    ids = data.get("ids", [])
    if not ids:
        return {"success": False, "message": "未选择任何记录进行导出"}
        
    from Sills.base import get_db_connection
    placeholders = ','.join(['?'] * len(ids))
    with get_db_connection() as conn:
        offers = conn.execute(f"SELECT * FROM uni_offer WHERE offer_id IN ({placeholders})", ids).fetchall()
        
    import io, csv
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['报价编号','日期','需求编号','询价型号','报价型号','询价品牌','报价品牌','询价数量','实际数量','报价数量','成本价','报价','平台','供应商编号','批号','交期','报价语句','备注'])
    
    for row in offers:
        r = dict(row)
        writer.writerow([
            r.get('offer_id'), r.get('offer_date'), r.get('quote_id'),
            r.get('inquiry_mpn'), r.get('quoted_mpn'), r.get('inquiry_brand'), r.get('quoted_brand'),
            r.get('inquiry_qty'), r.get('actual_qty'), r.get('quoted_qty'),
            r.get('cost_price_rmb'), r.get('offer_price_rmb'), r.get('platform'),
            r.get('vendor_id'), r.get('date_code'), r.get('delivery_date'),
            r.get('offer_statement'), r.get('remark')
        ])
        
    return {"success": True, "csv_content": output.getvalue()}

@app.get("/order", response_class=HTMLResponse)
async def order_page(request: Request, current_user: dict = Depends(login_required), page: int = 1, page_size: int = 20, search: str = "", cli_id: str = "", start_date: str = "", end_date: str = "", is_finished: str = ""):
    results, total = get_order_list(page=page, page_size=page_size, search_kw=search, cli_id=cli_id, start_date=start_date, end_date=end_date, is_finished=is_finished)
    total_pages = (total + page_size - 1) // page_size
    from Sills.db_cli import get_cli_list
    cli_list, _ = get_cli_list(page=1, page_size=1000)
    return templates.TemplateResponse("order.html", {
        "request": request, "active_page": "order", "current_user": current_user,
        "items": results, "total": total, "page": page, "page_size": page_size,
        "total_pages": total_pages, "search": search, "cli_id": cli_id, 
        "start_date": start_date, "end_date": end_date, "cli_list": cli_list,
        "is_finished": is_finished
    })

@app.post("/order/add")
async def order_add_route(
    cli_id: str = Form(...), offer_id: str = Form(None), 
    order_id: str = Form(None), order_date: str = Form(None),
    inquiry_mpn: str = Form(None), inquiry_brand: str = Form(None),
    is_finished: int = Form(0), is_paid: int = Form(0), 
    paid_amount: float = Form(0.0), remark: str = Form(""),
    current_user: dict = Depends(login_required)
):
    data = {
        "cli_id": cli_id, "offer_id": offer_id, "order_id": order_id, "order_date": order_date,
        "inquiry_mpn": inquiry_mpn, "inquiry_brand": inquiry_brand,
        "is_finished": is_finished, "is_paid": is_paid, 
        "paid_amount": paid_amount, "remark": remark
    }
    ok, msg = add_order(data)
    import urllib.parse
    return RedirectResponse(url=f"/order?msg={urllib.parse.quote(msg)}&success={1 if ok else 0}", status_code=303)

@app.post("/order/import")
async def order_import_text(batch_text: str = Form(None), csv_file: UploadFile = File(None), cli_id: str = Form(...), current_user: dict = Depends(login_required)):
    if batch_text:
        text = batch_text
    elif csv_file:
        content = await csv_file.read()
        try:
            text = content.decode('utf-8-sig').strip()
        except UnicodeDecodeError:
            text = content.decode('gbk', errors='replace').strip()
    else:
        return RedirectResponse(url="/order?msg=未提供导入内容&success=0", status_code=303)
        
    success_count, errors = batch_import_order(text, cli_id)
    import urllib.parse
    err_msg = ""
    if errors: err_msg = "&msg=" + urllib.parse.quote(errors[0])
    return RedirectResponse(url=f"/order?import_success={success_count}&errors={len(errors)}{err_msg}", status_code=303)

@app.post("/api/order/update_status")
async def api_order_update_status(order_id: str = Form(...), field: str = Form(...), value: int = Form(...), current_user: dict = Depends(login_required)):
    ok, msg = update_order_status(order_id, field, value)
    return {"success": ok, "message": msg}

@app.post("/api/order/update")
async def api_order_update(order_id: str = Form(...), field: str = Form(...), value: str = Form(...), current_user: dict = Depends(login_required)):
    if field in ['paid_amount']:
        try: value = float(value)
        except: return {"success": False, "message": "必须是数字"}
    ok, msg = update_order(order_id, {field: value})
    return {"success": ok, "message": msg}

@app.post("/api/order/delete")
async def api_order_delete(order_id: str = Form(...), current_user: dict = Depends(login_required)):
    if current_user['rule'] != '3': return {"success": False, "message": "无权限"}
    ok, msg = delete_order(order_id)
    return {"success": ok, "message": msg}

@app.post("/api/order/batch_delete")
async def api_order_batch_delete(request: Request, current_user: dict = Depends(login_required)):
    if current_user['rule'] != '3': return {"success": False, "message": "仅管理员可删除"}
    data = await request.json()
    ids = data.get("ids", [])
    ok, msg = batch_delete_order(ids)
    return {"success": ok, "message": msg}

@app.post("/api/order/export_csv")
async def order_export_csv(request: Request, current_user: dict = Depends(login_required)):
    data = await request.json()
    ids = data.get("ids", [])
    if not ids: return {"success": False, "message": "未选择记录"}
    placeholders = ','.join(['?'] * len(ids))
    with get_db_connection() as conn:
        orders = conn.execute(f"""
            SELECT ord.*, c.cli_name, 
                   COALESCE(ord.inquiry_mpn, o.inquiry_mpn) as final_mpn,
                   COALESCE(ord.inquiry_brand, o.inquiry_brand) as final_brand
            FROM uni_order ord 
            LEFT JOIN uni_cli c ON ord.cli_id = c.cli_id 
            LEFT JOIN uni_offer o ON ord.offer_id = o.offer_id
            WHERE ord.order_id IN ({placeholders})
        """, ids).fetchall()
    import io, csv
    output = io.StringIO(); output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['订单编号','日期','客户','报价编号','型号','品牌','完结状态','付款状态','已付金额','备注'])
    for r in orders:
        d = dict(r)
        writer.writerow([d['order_id'], d['order_date'], d['cli_name'], d['offer_id'] or '', d['final_mpn'] or '', d['final_brand'] or '', d['is_finished'], d['is_paid'], d['paid_amount'], d['remark']])
    return {"success": True, "csv_content": output.getvalue()}

@app.get("/buy", response_class=HTMLResponse)
async def buy_page(request: Request, current_user: dict = Depends(login_required), page: int = 1, page_size: int = 20, search: str = "", order_id: str = "", start_date: str = "", end_date: str = "", cli_id: str = "", is_shipped: str = ""):
    results, total = get_buy_list(page=page, page_size=page_size, search_kw=search, order_id=order_id, start_date=start_date, end_date=end_date, cli_id=cli_id, is_shipped=is_shipped)
    total_pages = (total + page_size - 1) // page_size
    with get_db_connection() as conn:
        vendors = conn.execute("SELECT vendor_id, vendor_name FROM uni_vendor").fetchall()
        orders = conn.execute("SELECT order_id FROM uni_order").fetchall()
        clis = conn.execute("SELECT cli_id, cli_name FROM uni_cli").fetchall()
    return templates.TemplateResponse("buy.html", {
        "request": request, "active_page": "buy", "current_user": current_user,
        "items": results, "total": total, "page": page, "page_size": page_size,
        "total_pages": total_pages, "search": search, "order_id": order_id,
        "start_date": start_date, "end_date": end_date, "cli_id": cli_id,
        "vendor_list": vendors, "order_list": orders, "cli_list": clis,
        "is_shipped": is_shipped
    })

@app.post("/buy/import")
async def buy_import_text(batch_text: str = Form(None), csv_file: UploadFile = File(None), current_user: dict = Depends(login_required)):
    if batch_text:
        text = batch_text
    elif csv_file:
        content = await csv_file.read()
        try:
            text = content.decode('utf-8-sig').strip()
        except UnicodeDecodeError:
            text = content.decode('gbk', errors='replace').strip()
    else:
        return RedirectResponse(url="/buy?import_success=0&errors=1&msg=未提供导入内容", status_code=303)
        
    success_count, errors = batch_import_buy(text)
    import urllib.parse
    err_msg = ""
    if errors: err_msg = "&msg=" + urllib.parse.quote(errors[0])
    return RedirectResponse(url=f"/buy?import_success={success_count}&errors={len(errors)}{err_msg}", status_code=303)

@app.post("/api/buy/batch_delete")
async def api_buy_batch_delete(request: Request, current_user: dict = Depends(login_required)):
    if current_user['rule'] != '3': return {"success": False, "message": "仅管理员可删除"}
    data = await request.json()
    ids = data.get("ids", [])
    ok, msg = batch_delete_buy(ids)
    return {"success": ok, "message": msg}

@app.post("/api/buy/export_csv")
async def buy_export_csv(request: Request, current_user: dict = Depends(login_required)):
    data = await request.json()
    ids = data.get("ids", [])
    if not ids: return {"success": False, "message": "未选择记录"}
    placeholders = ','.join(['?'] * len(ids))
    with get_db_connection() as conn:
        buys = conn.execute(f"""
            SELECT b.*, v.vendor_name, ord.order_id 
            FROM uni_buy b 
            LEFT JOIN uni_vendor v ON b.vendor_id = v.vendor_id 
            LEFT JOIN uni_order ord ON b.order_id = ord.order_id
            WHERE b.buy_id IN ({placeholders})
        """, ids).fetchall()
    import io, csv
    output = io.StringIO(); output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['采购编号','日期','销售订单','供应商','型号','品牌','单价','数量','总额','是否货源','是否下单','是否入库','是否发货','备注'])
    for r in buys:
        d = dict(r)
        writer.writerow([d['buy_id'], d['buy_date'], d['order_id'], d['vendor_name'], d['buy_mpn'], d['buy_brand'], d['buy_price_rmb'], d['buy_qty'], d['total_amount'], d['is_source_confirmed'], d['is_ordered'], d['is_instock'], d['is_shipped'], d['remark']])
    return {"success": True, "csv_content": output.getvalue()}
# --- New Workflow API endpoints ---

@app.post("/api/quote/batch_to_offer")
async def api_quote_batch_to_offer(data: dict, current_user: dict = Depends(login_required)):
    ids = data.get('ids', [])
    if not ids: return {"success": False, "message": "未选中记录"}
    try:
        ok, msg = batch_convert_from_quote(ids, current_user['emp_id'])
        return {"success": ok, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/offer/batch_to_order")
async def api_offer_batch_to_order(data: dict, current_user: dict = Depends(login_required)):
    ids = data.get('ids', [])
    cli_id = data.get('cli_id')
    if not ids: return {"success": False, "message": "未选中记录"}
    try:
        ok, msg = batch_convert_from_offer(ids, cli_id)
        return {"success": ok, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/order/batch_to_buy")
async def api_order_batch_to_buy(data: dict, current_user: dict = Depends(login_required)):
    ids = data.get('ids', [])
    if not ids: return {"success": False, "message": "未选中记录"}
    try:
        ok, msg = batch_convert_from_order(ids)
        return {"success": ok, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
