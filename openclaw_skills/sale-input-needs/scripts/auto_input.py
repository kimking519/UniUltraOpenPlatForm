import sys
import requests
import argparse

def main():
    parser = argparse.ArgumentParser(description='Auto input sales needs to UniUltra Platform')
    parser.add_argument('--cli_id', required=True)
    parser.add_argument('--mpn', required=True)
    parser.add_argument('--brand', default='')
    parser.add_argument('--qty', type=int, default=0)
    parser.add_argument('--price', type=float, default=0.0)
    parser.add_argument('--remark', default='')
    parser.add_argument('--base_url', default='http://127.0.0.1:8000')
    parser.add_argument('--db_path', help='Path to uni_platform.db (e.g. /mnt/e/...)')

    args = parser.parse_args()

    if args.base_url and not args.db_path:
        # Use API mode
        payload = {
            'cli_id': args.cli_id,
            'inquiry_mpn': args.mpn,
            'inquiry_brand': args.brand,
            'inquiry_qty': args.qty,
            'target_price_rmb': args.price,
            'remark': args.remark
        }
        try:
            response = requests.post(f"{args.base_url}/quote/add", data=payload, allow_redirects=False)
            if response.status_code in [200, 303]:
                print(f"Successfully sent request for MPN: {args.mpn}")
            else:
                print(f"Failed to input via API. Status Code: {response.status_code}")
        except Exception as e:
            print(f"API Error: {e}")
            
    elif args.db_path:
        # Direct Database Mode (Good for WSL access to Win files)
        import sqlite3
        import uuid
        from datetime import datetime
        
        try:
            conn = sqlite3.connect(args.db_path)
            u_hex = uuid.uuid4().hex
            suffix = u_hex[:4]
            quote_id = "Q" + datetime.now().strftime("%Y%m%d%H%M%S") + suffix
            quote_date = datetime.now().strftime("%Y-%m-%d")
            
            sql = """
            INSERT INTO uni_quote (quote_id, quote_date, cli_id, inquiry_mpn, quoted_mpn, inquiry_brand, inquiry_qty, target_price_rmb, cost_price_rmb, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (quote_id, quote_date, args.cli_id, args.mpn, '', args.brand, args.qty, args.price, 0.0, args.remark)
            
            conn.execute(sql, params)
            conn.commit()
            conn.close()
            print(f"Successfully inserted into DB. New ID: {quote_id}")
        except Exception as e:
            print(f"Database Write Error: {e}")

if __name__ == "__main__":
    main()
