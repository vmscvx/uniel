import os
import sys
import time
import base64
import brotli
import requests


def get_env(var):
    value = os.getenv(var)
    if value is None:
        print(
            f"Error: Environment variable {var} is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def download_data(url, username, password):
    resp = requests.get(url, auth=(username, password))
    resp.encoding = 'cp1251'
    return resp.text


def check_header(raw_lines, expected_b64):
    if not raw_lines:
        return False
    first_line = raw_lines[0]
    b64 = base64.b64encode(first_line.encode('utf-8')).decode('ascii')
    return b64 == expected_b64


def process_barcodes(lines):
    barcodes = []
    for line in lines[1:]:
        line = line.rstrip()
        if not line:
            continue
        line = line[:-1]
        pcs = line.rsplit(";", 1)
        if len(pcs) != 2:
            continue
        vendor_code, barcode = pcs
        barcode = barcode.strip()
        if len(barcode) == 13:
            barcodes.append((barcode, vendor_code.split(";")[0]))
        else:
            candidate = barcode.split(" ", 1)[0]
            if len(candidate) == 13:
                barcodes.append((candidate, vendor_code.split(";")[0]))
    barcodes.sort()
    prev_code = 2000000000000
    delta_lines = []
    for barcode, vendor_code in barcodes:
        delta = str(int(barcode) - prev_code)
        prev_code = int(barcode)
        delta_lines.append(f"{delta};{vendor_code}")
    result_lines = [str(int(time.time()))] + delta_lines
    return result_lines


def compress_and_save(lines, outname='data'):
    text = "\n".join(lines).encode("utf-8")
    compressed = brotli.compress(text, mode=brotli.MODE_TEXT, quality=11)
    with open(outname, "wb") as f:
        f.write(compressed)


def main():
    url = get_env("URL")
    user = get_env("USER")
    password = get_env("PASSWORD")
    header_b64 = get_env("HEADER")

    raw_text = download_data(url, user, password)
    raw_lines = raw_text.splitlines()

    if not check_header(raw_lines, header_b64):
        print("Header mismatch, aborting.", file=sys.stderr)
        sys.exit(2)

    processed_lines = process_barcodes(raw_lines)
    compress_and_save(processed_lines, "data")


if __name__ == "__main__":
    main()
