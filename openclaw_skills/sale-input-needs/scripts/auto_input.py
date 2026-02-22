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

    args = parser.parse_args()

    # Note: In a real agent scenario, authentication might be needed.
    # Here we assume the agent has session access or the API is local/internal.
    payload = {
        'cli_id': args.cli_id,
        'inquiry_mpn': args.mpn,
        'inquiry_brand': args.brand,
        'inquiry_qty': args.qty,
        'target_price_rmb': args.price,
        'remark': args.remark
    }

    try:
        # We use form submission as expected by the existing quote/add endpoint
        # Note: This requires the server to be running.
        response = requests.post(f"{args.base_url}/quote/add", data=payload, allow_redirects=False)
        
        if response.status_code in [200, 303]:
            print(f"Successfully sent request for MPN: {args.mpn}")
        else:
            print(f"Failed to input. Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
