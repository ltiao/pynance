import sys
import click
import requests, requests_cache
import configparser

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from datetime import datetime
from mpl_toolkits.axes_grid1 import make_axes_locatable

from pynance.auth import signed_params
from pynance.utils import create_session, create_datetime, to_milliseconds
from utils import WIDTH, GOLDEN_RATIO, pt_to_in


def create_trades_frame(trades_list):

    trades = pd.DataFrame(trades_list)
    return trades.assign(time=pd.to_datetime(trades.time, unit="ms"),
                         price=pd.to_numeric(trades.price),
                         qty=pd.to_numeric(trades.qty),
                         quoteQty=pd.to_numeric(trades.quoteQty))


@click.command()
@click.argument("symbol")
@click.argument("output_dir", default="figures/",
                type=click.Path(file_okay=False, dir_okay=True))
@click.option("--credentials-file", type=click.File('r'),
              default="scripts/credentials")
@click.option('--transparent', is_flag=True)
@click.option('--context', default="paper")
@click.option('--style', default="ticks")
@click.option('--palette', default="muted")
@click.option('--width', '-w', type=float, default=pt_to_in(WIDTH))
@click.option('--height', '-h', type=float)
@click.option('--aspect', '-a', type=float, default=GOLDEN_RATIO)
@click.option('--dpi', type=float, default=300)
@click.option('--extension', '-e', multiple=True, default=["png"])
def main(symbol, credentials_file, output_dir, transparent, context, style,
         palette, width, height, aspect, dpi, extension):

    # preamble
    if height is None:
        height = width / aspect
    # height *= num_iterations
    # figsize = size(width, aspect)
    figsize = (width, height)

    suffix = f"{width*dpi:.0f}x{height*dpi:.0f}"

    rc = {
        "figure.figsize": figsize,
        "font.serif": ["Times New Roman"],
        "text.usetex": False,
    }
    sns.set(context=context, style=style, palette=palette, font="serif", rc=rc)

    output_path = Path(output_dir).joinpath(symbol)
    output_path.mkdir(parents=True, exist_ok=True)

    config = configparser.ConfigParser()
    config.read_file(credentials_file)

    api_key = config["binance"]["api_key"]
    secret_key = config["binance"]["secret_key"]

    # s = requests_cache.CachedSession(backend="sqlite")

    s = create_session(api_key)
    r = s.get("https://api.binance.com/api/v3/myTrades",
              params=signed_params(params=dict(symbol=symbol),
                                   secret_key=secret_key))

    frame = create_trades_frame(r.json()).set_index(["orderId", "id", "time"]) \
        .assign(commission=lambda x: pd.to_numeric(x.commission))

    r = s.get("https://api.binance.com/api/v3/avgPrice", params=dict(symbol=symbol))
    avg_price = r.json()
    print(f"Average price in the last {avg_price['mins']} minutes: "
          f"{avg_price['price']}")

    current_price = float(avg_price.get("price"))

    frame = frame.assign(cost=lambda x: x.qty * x.price,
                         value=lambda x: x.qty * current_price,
                         delta=lambda x: x.value - x.cost,
                         delta_rate=lambda x: x.delta / x.quoteQty,
                         delta_pct=lambda x: 100.0 * x.delta_rate,
                         relative_qty=lambda x: (-1)**(~x.isBuyer) * x.qty)

    print(frame)
    print(frame.relative_qty.cumsum())

    # # r = requests.get("https://api.binance.com/api/v3/trades",
    # #                  params=dict(symbol=symbol))
    # # frame = create_trades_frame(r.json())

    # fig, ax = plt.subplots()

    # sns.lineplot(x="time", y="relative_qty", data=frame.relative_qty.cumsum().reset_index(), ax=ax)

    # plt.tight_layout()
    # fig.autofmt_xdate()

    # for ext in extension:
    #     fig.savefig(output_path.joinpath(f"cumulative_{context}_{suffix}.{ext}"),
    #                 dpi=dpi, transparent=transparent)

    # plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
