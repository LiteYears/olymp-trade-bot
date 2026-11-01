import time
import json
import traceback
from datetime import datetime

from olymptradeapi.stable_api import Olymptrade

# ==========================================================
# CONFIG
# ==========================================================

EMAIL = "your_email"
PASSWORD = "your_password"
SSID = "your_session_cookie"

PAIR = "EURUSD"

REPORT_FILE = "olymtrade_stable_api_report.json"

# ==========================================================
# REPORT
# ==========================================================

report = {
    "timestamp": str(datetime.utcnow()),
    "tests": {}
}


def save_test(name, success, data=None, error=None):
    report["tests"][name] = {
        "success": success,
        "data": data,
        "error": error
    }


def run_test(name, func):
    try:
        result = func()

        save_test(
            name,
            True,
            result
        )

        print(f"[PASS] {name}")

        return result

    except Exception as e:

        save_test(
            name,
            False,
            error=str(e)
        )

        print(f"[FAIL] {name}: {e}")

        return None


# ==========================================================
# CONNECT
# ==========================================================

print("\n=== OLYMPTRADE STABLE_API TESTER ===\n")

account = Olymptrade(
    EMAIL,
    PASSWORD,
    set_ssid=SSID
)

try:

    connected, reason = account.connect()

    save_test(
        "connect",
        connected,
        {"reason": str(reason)}
    )

    print(
        f"Connected: {connected}"
    )

    if not connected:

        with open(
            REPORT_FILE,
            "w"
        ) as f:
            json.dump(
                report,
                f,
                indent=4
            )

        raise SystemExit()

except Exception as e:

    print(e)

    raise SystemExit()

# ==========================================================
# BALANCE
# ==========================================================

run_test(
    "balance",
    account.get_balance
)

# ==========================================================
# PAYMENT
# ==========================================================

run_test(
    "payment",
    account.get_payment
)

# ==========================================================
# ASSET DATA
# ==========================================================

run_test(
    "asset_data",
    account.get_asset_data
)

# ==========================================================
# PRACTICE ACCOUNT
# ==========================================================

def test_practice():

    account.change_balance(
        "PRACTICE"
    )

    return account.get_balance()

run_test(
    "practice_mode",
    test_practice
)

# ==========================================================
# REAL ACCOUNT
# ==========================================================

def test_real():

    account.change_balance(
        "REAL"
    )

    return account.get_balance()

run_test(
    "real_mode",
    test_real
)

# ==========================================================
# CANDLES
# ==========================================================

def test_candles():

    return account.get_candle(
        PAIR,
        60,
        int(time.time())
    )

run_test(
    "historical_candles",
    test_candles
)

# ==========================================================
# REALTIME STREAM
# ==========================================================

def realtime_test():

    stream_id = (
        account.start_candles_stream(
            PAIR,
            1
        )
    )

    candles = []

    start = time.time()

    while time.time() - start < 10:

        try:

            success, data = (
                account.get_realtime_candles(
                    PAIR,
                    1
                )
            )

            candles.append({
                "success": success,
                "data": data
            })

        except Exception:
            pass

        time.sleep(1)

    try:
        account.stop_candles_stream(
            stream_id
        )
    except:
        pass

    return {
        "stream_id": stream_id,
        "samples": len(candles)
    }

run_test(
    "realtime_stream",
    realtime_test
)

# ==========================================================
# METHOD DISCOVERY
# ==========================================================

def inspect_methods():

    methods = []

    for item in dir(account):

        if not item.startswith("_"):

            methods.append(item)

    return methods

run_test(
    "method_discovery",
    inspect_methods
)

# ==========================================================
# SAVE REPORT
# ==========================================================

with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report,
        f,
        indent=4,
        default=str
    )

print(
    f"\nReport saved to {REPORT_FILE}"
)
