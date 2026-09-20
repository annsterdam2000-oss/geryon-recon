# agent/modules/ip.py
import dns.resolver
import dns.reversename
import requests


def module_ip(target: str) -> dict:
    target = target.strip()
    result = {"target": target}

    # --- 1. Гео/провайдер через ip-api.com ---
    try:
        r = requests.get(
            f"http://ip-api.com/json/{target}",
            params={
                "fields": "status,message,country,countryCode,region,regionName,"
                          "city,zip,lat,lon,timezone,isp,org,as,asname,"
                          "mobile,proxy,hosting,query"
            },
            timeout=10,
        )
        data = r.json()
        if data.get("status") == "success":
            result["geo"] = {
                "country": data.get("country"),
                "country_code": data.get("countryCode"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "zip": data.get("zip"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "timezone": data.get("timezone"),
            }
            result["network"] = {
                "isp": data.get("isp"),
                "org": data.get("org"),
                "as": data.get("as"),
                "asname": data.get("asname"),
                "mobile": data.get("mobile"),
                "proxy": data.get("proxy"),
                "hosting": data.get("hosting"),
            }
        else:
            result["geo_error"] = data.get("message", "unknown error")
    except Exception as e:
        result["geo_error"] = str(e)

    # --- 2. Reverse DNS (PTR) ---
    try:
        rev = dns.reversename.from_address(target)
        answers = dns.resolver.resolve(rev, "PTR", lifetime=5)
        result["ptr"] = [str(r).rstrip(".") for r in answers]
    except Exception:
        result["ptr"] = []

    # --- 3. Whois по IP через ipwhois ---
    try:
        from ipwhois import IPWhois
        obj = IPWhois(target)
        whois_data = obj.lookup_rdap(depth=1)

        net = whois_data.get("network", {}) or {}
        result["whois"] = {
            "netname": net.get("name"),
            "cidr": net.get("cidr"),
            "country": net.get("country"),
            "start_address": net.get("start_address"),
            "end_address": net.get("end_address"),
            "registered": net.get("events", [{}])[0].get("timestamp") if net.get("events") else None,
            "description": net.get("remarks"),
            "asn": whois_data.get("asn"),
            "asn_description": whois_data.get("asn_description"),
            "asn_country": whois_data.get("asn_country_code"),
        }
    except Exception as e:
        result["whois_error"] = str(e)

    return result