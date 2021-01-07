import sys
import click
import pandas as pd

from datetime import datetime
from pynance.auth import signed_params
from pynance.utils import create_session, create_datetime, to_milliseconds

import configparser


@click.command()
@click.argument("symbol")
@click.option("--credentials-file", type=click.File('r'),
              default="scripts/credentials")
def main(symbol, credentials_file):

    config = configparser.ConfigParser()
    config.read_file(credentials_file)

    api_key = config["binance"]["api_key"]
    secret_key = config["binance"]["secret_key"]

    s = create_session(api_key)
    r = s.get("https://api.binance.com/api/v3/time")
    timestamp = r.json().get("serverTime")
    # click.echo(f" Local time: {datetime.now()}")
    # click.echo(f"Server time: {create_datetime(timestamp)}")

    click.echo(f"Difference: {to_milliseconds((datetime.now() - create_datetime(timestamp)).total_seconds())}")

    # r = s.get("https://api.binance.com/api/v3/avgPrice",
    #           params=dict(symbol=symbol))
    # click.echo(r.json())

    # r = s.get("https://api.binance.com/api/v3/ticker/price",
    #           params=dict(symbol=symbol))
    # click.echo(r.json())

    # r = s.get("https://api.binance.com/api/v3/ticker/bookTicker",
    #           params=dict(symbol=symbol))
    # click.echo(r.json())

    # r = s.get("https://api.binance.com/api/v3/time")
    # timestamp = r.json().get("serverTime")
    # click.echo(f" Local time: {datetime.now()}")
    # click.echo(f"Server time: {create_datetime(timestamp)}")

    # r = s.get("https://api.binance.com/api/v3/myTrades",
    #           params=signed_params(params=dict(symbol=symbol),
    #                                secret_key=secret_key))
    # frame = pd.DataFrame(r.json()).set_index("orderId")
    # print(frame.assign(time=pd.to_datetime(frame.time, unit="ms")))

    # r = s.get("https://api.binance.com/api/v3/aggTrades",
    #           params=dict(symbol=symbol))
    # frame = pd.DataFrame(r.json())
    # click.echo(pd.to_datetime(frame["T"], unit="ms"))

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
