#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time

WORKER_URL = "https://withered-frost-8444.hallgrunt.workers.dev"
GROUP = "Croatia"
OUTPUT_FILE = "oha_channels.m3u"

def fetch_catalog_via_worker(cursor=None):
    params = {"action": "catalog", "group": GROUP}
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(WORKER_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def resolve_via_worker(channel_id):
    resp = requests.get(WORKER_URL, params={"action": "resolve", "ID": channel_id}, timeout=20, allow_redirects=False)
    if resp.status_code == 302:
        return resp.headers.get("Location")
    return None

def main():
    print(f"Dohvaćam kanale za grupu: {GROUP}")
    channels = []
    cursor = None
    page = 0

    while True:
        page += 1
        print(f"  Stranica {page}...", end=" ", flush=True)
        try:
            data = fetch_catalog_via_worker(cursor)
            items = data.get("items", [])
            if not items:
                print("nema više kanala.")
                break
            print(f"pronađeno {len(items)} kanala.")
            for item in items:
                channels.append({
                    "name": item.get("name", ""),
                    "logo": item.get("logo", ""),
                    "id": item.get("ids", {}).get("id", "")
                })
            cursor = data.get("nextCursor")
            if cursor is None:
                break
        except Exception as e:
            print(f"greška: {e}")
            break

    if not channels:
        print("❌ Nema kanala.")
        return

    print(f"Ukupno {len(channels)} kanala. Resolvam preko Workera...")
    resolved = []

    for idx, ch in enumerate(channels, 1):
        print(f"  {idx}/{len(channels)}: {ch['name']}...", end=" ", flush=True)
        if not ch["id"]:
            print("NEMA ID")
            continue
        stream = resolve_via_worker(ch["id"])
        if stream:
            print("OK")
            ch["stream_url"] = stream
            resolved.append(ch)
        else:
            print("NEMA")
        time.sleep(0.2)

    if not resolved:
        print("❌ Nema resolvanih kanala.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in resolved:
            f.write(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="oha",{ch["name"]}\n')
            f.write(f"{ch['stream_url']}\n")

    print(f"🎉 M3U datoteka spremljena: {OUTPUT_FILE} ({len(resolved)} kanala)")

if __name__ == "__main__":
    main()